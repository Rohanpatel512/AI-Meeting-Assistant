import re 
from sentence_transformers import SentenceTransformer, util 
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

FILLER_PATTERN = re.compile(r"\b(?:um+|ah+|err+|er+|em+)\b", re.IGNORECASE)
ARTIFACT_PATTERN = re.compile(
    r"\[(?:inaudible|unintelligible|background noise|music)\]",
    re.IGNORECASE
)
SIMILARITY_THRESHOLD = 0.65
GREY_AREA_THRESHOLD = 0.53
SLIDING_WINDOW = 15

tokenizer = AutoTokenizer.from_pretrained("cross-encoder/qnli-distilroberta-base")
cross_encoder = AutoModelForSequenceClassification.from_pretrained("cross-encoder/qnli-distilroberta-base")

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def preprocess_text(text: str) -> str:
    """
    Preprocesses the transcript text by removing filler words and artifact transcriptions.

    args:
        text (str): The text of the meeting transcript.
    """
    text = normalize_text(text)
    text = remove_similar_phrases(text)

    return text

def normalize_text(text: str) -> str:
    """
    Cleans the transcript text by removing filler words and artifact transcriptions
    and other unecessary elements.  

    args:
        text (str): The text of the meeting transcript.
    """

    pattern = r'\[.*?\]|\(.*?\)|\{.*?\}'

    # Remove bracketed text from transcript (e.g., (product manager))
    text = re.sub(pattern, '', text)

    # Remove filler words and artifact transcriptions
    text = FILLER_PATTERN.sub("", text)
    text = ARTIFACT_PATTERN.sub("", text)

    # Remove bracketed time stamps (e.g., [00:00:00])
    text = re.sub(r"\[?\d{1,2}:\d{2}(:\d{2})?(\.\d{3})?\]?(\s*-->\s*\[?\d{1,2}:\d{2}(:\d{2})?(\.\d{3})?\]?)?", "", text)

    # Removes horizontal spaces 
    text = re.sub(r"(?m)^[ \t]+", " ", text)

    # Remove lines containing only digits and the newline that follows them
    text = re.sub(r"(?m)^\s*\d+\s*\n", "", text)

    # Remove extra new-lines, but if there are multiple new-lines, keep one to separate the paragraphs 
    text = re.sub(r'\n+', '\n', text).strip()

    return text 

def isolate_speaker_lines(sentences: list) -> list:
    """
    Removes speaker identifiers from the transcript text, leaving only the spoken content.

    args:
        text (str): The text of the meeting transcript.
    
    returns:
        text (str): The text of the meeting transcript with filler phrases removed.
    """
    isolated_phrases = []
    for sentence in sentences:
        if ">" in sentence:
            speaker, content = sentence.split(">", 1)
            isolated_phrases.append(content.strip())
        else:
            isolated_phrases.append(sentence.strip())

    return isolated_phrases 

def token_dense_transcript(sentences: list) -> list:
    """
    Removes unecessary tokens from the transcript text to compress transcript to minimize token usage
    
    args:
        sentences (list): The list of sentences/phrases from the meeting transcript.
    
    returns:
        sentences (list): The list of sentences/phrases from the meeting transcript with unecessary tokens removed.    
    """
    i = 0
    prev_speaker = None
    for sentence in sentences:
        if ":" in sentence:
           speaker, content = sentence.split(":", 1)
           if speaker.strip() == prev_speaker:
               new_sentence = f" {content.strip()}"
           else:
               new_sentence = f"{speaker.strip()}> {content.strip()}"
           prev_speaker = speaker.strip()
           sentences[i] = new_sentence
        i += 1

    return sentences 


def remove_similar_phrases(text: str) -> str:
    """
    Removes similar phrases from the transcript text.
    
    args:
        text (str): The text of the meeting transcript.
        
    returns:
        text (str): The text of the meeting transcript with similar phrases removed.
    """

    duplicate_indices = set()

    # Split the text on newlines to get individual phrases 
    phrases = text.splitlines()

    sentences = [segment.strip() for segment in phrases]

    sentences = token_dense_transcript(sentences)

    isolated_phrases = isolate_speaker_lines(sentences)

    if len(isolated_phrases) == 0:
        return text

    for i in range(len(isolated_phrases)):
        if i in duplicate_indices:
            continue 

        phrase_embedding = model.encode(isolated_phrases[i], convert_to_tensor=True)

        for j in range(i + 1, min(i + SLIDING_WINDOW, len(isolated_phrases))):
            if j in duplicate_indices:
                continue 

            comparison_embedding = model.encode(isolated_phrases[j], convert_to_tensor=True)

            similarity_score = util.pytorch_cos_sim(phrase_embedding, comparison_embedding).item()

            if similarity_score > SIMILARITY_THRESHOLD:
                duplicate_indices.add(j)

            if similarity_score > GREY_AREA_THRESHOLD:
                pair = [isolated_phrases[i], isolated_phrases[j]]
                with torch.no_grad():
                    inputs = tokenizer(pair, padding=True, truncation=True, return_tensors="pt")
                    outputs = cross_encoder(**inputs)
                    logits = outputs.logits.squeeze(dim=1)

                if logits[0] > logits[1]:
                    duplicate_indices.add(j)

    filtered_sentences = [sentences[i] for i in range(len(sentences)) if i not in duplicate_indices]

    return " ".join(filtered_sentences)