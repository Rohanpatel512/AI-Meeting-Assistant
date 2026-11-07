import re 
from sentence_transformers import SentenceTransformer, util 
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from io import StringIO
import webvtt

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


SIMILARITY_THRESHOLD = 0.65
GREY_AREA_THRESHOLD = 0.53
SLIDING_WINDOW = 15

tokenizer = AutoTokenizer.from_pretrained("cross-encoder/qnli-distilroberta-base")
cross_encoder = AutoModelForSequenceClassification.from_pretrained("cross-encoder/qnli-distilroberta-base")

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def preprocess_transcript(transcript: str) -> str:
    """
    Master orchestrator function that completely preprocesses the transcript and makes it 
    ready for LLM.

    args:
        transcript (str): The transcript to be preprocessed.
    
    returns:
        transcript_preprocessed (str): The preprocessed transcript.
    """

    speakers = identify_speakers(transcript)
    segments = remove_cue_identifiers(transcript)

    # Clean up each segment 
    segments = clean_segments(segments)

    # Remove similar phrases 
    segments = remove_similar_phrases(segments)

    if len(speakers) > 0:
        combined_speaker_dialects = combine_speaker_dialogues(speakers, segments)
        transcript_preprocessed = create_final_transcript(combined_speaker_dialects, speakers, None)
    else:
        transcript_preprocessed = " ".join(segments)

    return transcript_preprocessed

def clean_segments(segments: list) -> list:
    """
    Clean up the phrases such as removing artificats, extra whitespaces, etc.

    args:
        segments (list) - List of speaker dialogues
    
    returns:
        segments (list) - List of speaker dialogues cleaned up.
    """

    pattern = r'\[(?:' + '|'.join(map(re.escape, ARTIFACTS)) + r')\]'

    for i in range(0, len(segments)):
        # Remove unecessary artifacts
        segments[i] = re.sub(pattern, '', segments[i])

        # Remove extra whitespace
        segments[i] = re.sub(r'\s+', ' ', segments[i])

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
    If two or more dialects come from the same speaker, it is combined into a 
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
    

def remove_cue_identifiers(transcript: str) -> str:
    """
    Removes cue identifiers from the transcript.

    args:
        transcript (str): The transcript to be cleaned.
    
    parameters:
        transcript_cleaned (str): The transcript with cue identifiers removed.
    """

    vtt = webvtt.WebVTT.from_buffer(StringIO(transcript))
    segments = []

    for caption in vtt:
        if caption.text.strip():
            segments.append(caption.text.strip())
    
    return segments

def remove_similar_phrases(segments: list) -> list:
    """
    Removes similar phrases from the transcript text.
    
    args:
        segments (str): List of phrases.
        
    returns:
        filtered_segments (str): List of meeting transcript phrases with similar dialects removed.
    """

    duplicate_indices = set()

    if len(segments) == 0:
        return []

    for i in range(len(segments)):
        if i in duplicate_indices:
            continue 

        phrase_embedding = model.encode(segments[i], convert_to_tensor=True)

        for j in range(i + 1, min(i + SLIDING_WINDOW, len(segments))):
            if j in duplicate_indices:
                continue 

            comparison_embedding = model.encode(segments[j], convert_to_tensor=True)

            similarity_score = util.pytorch_cos_sim(phrase_embedding, comparison_embedding).item()

            if similarity_score > SIMILARITY_THRESHOLD:
                duplicate_indices.add(j)

            if similarity_score > GREY_AREA_THRESHOLD:
                pair = [segments[i], segments[j]]
                with torch.no_grad():
                    inputs = tokenizer(pair, padding=True, truncation=True, return_tensors="pt")
                    outputs = cross_encoder(**inputs)
                    logits = outputs.logits.squeeze(dim=1)

                if logits[0] > logits[1]:
                    duplicate_indices.add(j)

    filtered_segments = [segments[i] for i in range(len(segments)) if i not in duplicate_indices]

    return filtered_segments



if __name__ == "__main__":
    text = """WEBVTT

00:00:01.120 --> 00:00:04.550
Good morning, everyone. Let's get the weekly sync started.

00:00:04.550 --> 00:00:09.180
I know a few people are still <i>jumping on</i>, but we have a tight schedule.

00:00:09.430 --> 00:00:13.800
Hey Sarah, sorry to interrupt, but is the quarterly report slide deck updated yet?

00:00:14.200 --> 00:00:18.050
Yes, David, it is. I pinned the link in the main Slack channel.

00:00:18.410 --> 00:00:23.900
>Awesome, thanks. [coughing] Just wanted to make sure before the client call.

001
00:00:24.150 --> 00:00:26.500
>No problem. Elena, do you want to give the engineering update?

00:00:26.900 --> 00:00:31.330
Sure. So, the database migration went live at 2:00 AM on Sunday.

00:00:31.330 --> 00:00:35.400
We experienced about ten minutes of <b>unplanned downtime</b>,
but everything is stable now.

00:00:36.000 --> 00:00:39.120
Wow, only ten minutes? That is a massive win.

00:00:39.120 --> 00:00:41.850
Yeah, we were expecting a lot worse. [laughter]

00:00:42.200 --> 00:00:47.500
Great job, Elena. Next up, let's talk about the Q4 hiring budget.

00:00:48.000 --> 00:00:52.300
We have approval for two new senior backend roles and one frontend role.

00:00:52.600 --> 00:00:54.990
I'll drop the job descriptions in the email thread later today.
"""
    #preprocess_transcript(text)
    print(preprocess_transcript(text))
