import re 
from sentence_transformers import SentenceTransformer, util 
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from io import StringIO
from app.services.chunker import token_aware_chunking
#from chunker import token_aware_chunking
import webvtt
from wtpsplit import SaT

ARTIFACTS = [
    "laughing",
    "laughter",
    "coughing",
    "cough",
    "sneezing",
    "sneeze",
    "sighing",
    "sigh",
    "clearing throat",
    "background noise",
    "background music",
    "music",
    "applause",
    "breathing",
    "static",
    "audio interference",
    "door slams",
    "door closing"
]

FILLERS = [
    r"um+",
    r"uh+",
    r"er+",
    r"ah+",
    r"like",
    r"you know",
    r"i mean",
    r"basically",
    r"actually",
    r"literally",
]


SIMILARITY_THRESHOLD = 0.65
GREY_AREA_THRESHOLD = 0.53
SLIDING_WINDOW = 15

tokenizer = AutoTokenizer.from_pretrained("cross-encoder/qnli-distilroberta-base")
cross_encoder = AutoModelForSequenceClassification.from_pretrained("cross-encoder/qnli-distilroberta-base")

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

sat = SaT("sat-3l-sm")

def preprocess_transcript(transcript: str) -> list:
    """
    Master orchestrator function that completely preprocesses the transcript and makes it 
    ready for LLM.

    args:
        transcript (str): The transcript to be preprocessed.
    
    returns:
        transcript_preprocessed (str): The preprocessed transcript.
    """

    speakers = identify_speakers(transcript)
    segments = extract_caption_segments(transcript)

    # Clean up each segment 
    segments = clean_segments(segments)

    # Remove similar phrases 
    if len(speakers) > 0:
        segments, speakers = remove_similar_phrases(segments, speakers)
    else:
        segments = remove_similar_phrases(segments, None)

    pattern = r"\b(?:" + "|".join(FILLERS) + r")\b,?\s*"
    
    if len(speakers) > 0:
        combined_speaker_dialects = combine_speaker_dialogues(speakers, segments)
        preprocessed_text = create_final_transcript(combined_speaker_dialects, speakers)
        chunks = token_aware_chunking(preprocessed_text, combined_speaker_dialects)
        return chunks
    else:
        segments = reassemble_fragmented_phrases(segments)
        for i in range(0, len(segments)):
            segments[i] = re.sub(pattern, "", segments[i], flags=re.IGNORECASE)
        chunks = token_aware_chunking(None, segments)
        return chunks


def reassemble_fragmented_phrases(segments: list, threshold: float = 0.25) -> list: 
    """
    Repairs mid-phrase line breaks or false speech-to-text sentence
    breaks.

    args:
        segments (list) - List of phrases spoken during meeting.
    
    returns:
        None
    """

    new_segments = []
    prev_segment = segments[0]

    for i in range(1, len(segments)):
        combined = f"{prev_segment} {segments[i]}"

        sentences = [s.strip() for s in sat.split(combined, threshold=threshold) if s.strip()]

        # If sentence is fragmented
        if len(sentences) == 1:
            prev_segment = sentences[0] 
        else:
            new_segments.extend(sentences[:-1])
            prev_segment = sentences[-1]

    if prev_segment:
        new_segments.append(prev_segment)

    return new_segments

    
def clean_segments(segments: list) -> list:
    """
    Clean up the phrases such as removing artificats, extra whitespaces, etc.

    args:
        segments (list) - List of speaker dialogues
    
    returns:
        segments (list) - List of speaker dialogues cleaned up.
    """

    pattern = r'\[(?:' + '|'.join(map(re.escape, ARTIFACTS)) + r')\]'

    filler_pattern = r"\b(?:" + "|".join(FILLERS) + r")\b,?\s*"

    for i in range(0, len(segments)):
        # Remove unecessary artifacts
        segments[i] = re.sub(pattern, '', segments[i])

        # Remove extra whitespace
        segments[i] = re.sub(r'\s+', ' ', segments[i])

        segments[i] = re.sub(r'</?v[^>]*>', '', segments[i]) 

    return segments



def create_final_transcript(combined_speaker_dialects: list, speakers: list) -> str:
    """
    Combines the list into a single preprocessed string (transcript) that will
    be passed through LLM for summarization

    args:
        combined_speaker_dialects (list): A list of phrases with their respective speaker labels. 
        speakers (list): A list of speakers.
    
    returns:
        transcript_preprocessed (str): Final preprocessed transcript that will be passed through LLM.
    """

    transcript_preprocessed = " ".join(combined_speaker_dialects)

    if speakers is not None:
        if speakers != []:
            transcript_preprocessed = re.sub(r"\[SEP\]", ">", transcript_preprocessed)
            transcript_preprocessed = re.sub(r'\s+', ' ', transcript_preprocessed)


    return transcript_preprocessed



def identify_speakers(transcript: str) -> list:
    """
    Identifies speaker for each line in the transcript and adds it to a list.

    args:
        transcript (str): The transcript to to be preprocessed.
    
    returns:
        speakers (list): The list of speakers in order.
    """

    return re.findall(r'<v\s+([^>]+)>', transcript, flags=re.IGNORECASE)



def combine_speaker_dialogues(speakers: list, segments: list) -> list:
    """
    If two or more consecutive dialects come from the same speaker, it is combined into a 
    single dialect.

    args:
        speakers (list): List of speaker dialogues 
        segments (list): The list of speakers who spoke each phrase
    
    returns:
        combined_speaker_dialogues (list): A list of phrases with their respective speaker labels.
    """

    if len(speakers) != len(segments):
        return []

    prev_speaker = None
    phrase = ""
    combined_speaker_dialogues = []

    for speaker, segment in zip(speakers, segments):

        if prev_speaker is not None and speaker != prev_speaker: 
            combined_speaker_dialogues.append(f"{prev_speaker}[SEP] {phrase}")
            phrase = ""

        phrase += segment + " "
        prev_speaker = speaker 

    if phrase:
        combined_speaker_dialogues.append(f"{prev_speaker}[SEP] {phrase}")

    return combined_speaker_dialogues



def strip_vtt_cue_identifiers(transcript: str) -> str:
    """
    Removes standalone cue identifiers that some platforms insert into VTT exports.
    These are usually single-line numeric markers such as "1" or "001" and are not
    spoken transcript content.
    """

    if not transcript or not isinstance(transcript, str):
        return transcript

    lines = transcript.splitlines()
    cleaned_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped.upper() == 'WEBVTT':
            cleaned_lines.append(line)
            continue

        if not stripped:
            cleaned_lines.append(line)
            continue

        next_line = ""
        for next_candidate in lines[i + 1:]:
            if next_candidate.strip():
                next_line = next_candidate.strip()
                break

        is_cue_identifier = bool(re.fullmatch(r'(?:\d+|[A-Za-z0-9_-]+)', stripped)) and (
            next_line.startswith('<v ') or
            next_line.startswith('<c.') or
            re.match(r'^\d{2,}:\d{2}:\d{2}\.\d{3}\s*-->', next_line)
        )

        if is_cue_identifier:
            continue

        if re.fullmatch(r'\d+', stripped):
            continue

        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


    

def extract_caption_segments(transcript: str) -> str:
    """
    Extracts dialogue segments from a WebVTT transcript.

    args:
        transcript (str): The transcript to be cleaned.
    
    parameters:
        segment (list): A list of extracted caption segments.
    """

    transcript = strip_vtt_cue_identifiers(transcript)
    
    vtt = webvtt.WebVTT.from_buffer(StringIO(transcript))
 
    segments = []

    for caption in vtt:
        if caption.text.strip():
            segments.append(caption.text.strip())
    
    return segments
    



def remove_similar_phrases(segments: list, speakers: list) -> list:
    """
    Removes similar phrases from the transcript text.
    
    args:
        segments (str): List of phrases.
        speakers (str): List of corresponding speakers that spoke the phrase (This is optional.)
        
    returns:
        filtered_segments (str): List of meeting transcript phrases with similar dialects removed.
    """

    duplicate_indices = set()

    if len(segments) == 0:
        return []

    embeddings = model.encode(segments, convert_to_tensor=True, batch_size=64, show_progress_bar=False)

    agreement_safelist = r'\b(yeah|yes|ok|okay|no|sure|agree|makes\ssense|sounds\sgood|cool|right)\b'

    for i in range(0, len(segments)):
        if i in duplicate_indices:
            continue 

        # Do not deduplicate short agreement phrases
        if len(segments[i].split()) <= 3 and re.search(agreement_safelist, segments[i], re.I):
            continue

        
        end_window = min(i + SLIDING_WINDOW, len(segments))

        if i + 1 >= end_window:
            continue 

        similarity_matrix = util.pytorch_cos_sim(embeddings[i], embeddings[i + 1:end_window])
        similarity_scores = similarity_matrix[0] if similarity_matrix.ndim > 1 else similarity_matrix

        cross_encoder_pairs = []
        cross_encoder_indices = []

        for offset_idx, similarity_score in enumerate(similarity_scores):
            j = i + 1 + offset_idx 
            if j in duplicate_indices:
                continue 

            similarity_value = float(similarity_score)

            if similarity_value > SIMILARITY_THRESHOLD: 
                duplicate_indices.add(j) 
                continue 
                
            if similarity_value > GREY_AREA_THRESHOLD: 
                cross_encoder_pairs.append([segments[i], segments[j]])
                cross_encoder_indices.append(j)

        if cross_encoder_pairs:
            with torch.no_grad():
                inputs = tokenizer(cross_encoder_pairs, padding=True, truncation=True, return_tensors="pt")
                outputs = cross_encoder(**inputs)
                logits = outputs.logits

            for index, j in enumerate(cross_encoder_indices):
                if logits[index].argmax().item() == 1:
                    duplicate_indices.add(j)

    filtered_segments = [segments[i] for i in range(len(segments)) if i not in duplicate_indices]

    if len(speakers) > 0:
        filtered_speakers = [speakers[i] for i in range(len(speakers)) if i not in duplicate_indices]

    return filtered_segments, filtered_speakers