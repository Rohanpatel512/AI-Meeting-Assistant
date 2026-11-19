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


            



if __name__ == "__main__":
    text = """WEBVTT
1
00:00:02.120 --> 00:00:08.450
<v Maya Lin>Good morning everyone. Thanks for hopping on right at 10. We have a packed agenda today across the checkout latency postmortem, Q4 mobile release milestones, and cloud infrastructure budgets.</v>

2
00:00:08.900 --> 00:00:13.210
<v Carlos Rivera>Morning Maya. Just a heads up, I have a hard stop at 10:45 for a vendor call, so can we tackle the checkout incident first?</v>

3
00:00:13.500 --> 00:00:17.880
<v Maya Lin>Absolutely, let's jump straight into that. Carlos, walk us through what happened during Tuesday's traffic spike.</v>

4
00:00:18.300 --> 00:00:29.640
<v Carlos Rivera>Sure. So on Tuesday around 2:15 PM Eastern, checkout API p99 latency jumped from 240 milliseconds to over 4.2 seconds for about eighteen minutes. Roughly four percent of payment intents timed out.</v>

5
00:00:30.100 --> 00:00:35.420
<v Priya Patel>Was that tied to the new fraud-scoring webhook we enabled on Monday afternoon?</v>

6
00:00:35.890 --> 00:00:48.110
<v Carlos Rivera>Spot on. The third-party fraud service throttled our burst requests, and because our HTTP client didn't have a circuit breaker configured, worker threads piled up waiting on the 5-second socket timeout.</v>

7
00:00:48.600 --> 00:00:54.950
<v Jordan Vance>Oof, yeah, cascading thread starvation. Did rolling back the feature flag recover everything immediately?</v>

8
00:00:55.320 --> 00:01:05.780
<v Carlos Rivera>Yes, within ninety seconds of toggling the flag off, latency dropped back to baseline. No duplicate charges occurred because our idempotency keys held up.</v>

9
00:01:06.150 --> 00:01:15.400
<v Maya Lin>That's a huge relief. What are our concrete follow-ups so this doesn't happen again before Black Friday?</v>

10
00:01:15.880 --> 00:01:28.500
<v Carlos Rivera>Two things. First, we decided to wrap all external webhook calls in an exponential-backoff circuit breaker with a strict 800-millisecond timeout. Second, we'll fail open on non-critical fraud checks during peak traffic.</v>

11
00:01:29.050 --> 00:01:36.220
<v Priya Patel>I can implement the circuit breaker middleware in the checkout service. I'll have the pull request ready for review by this Friday, November 20th.</v>

12
00:01:36.700 --> 00:01:44.180
<v Carlos Rivera>Thanks Priya. And I'll run a k6 load test against staging at 3x peak volume on Monday morning to verify the fail-open behavior before we re-enable the flag.</v>

13
00:01:44.650 --> 00:01:51.900
<v Maya Lin>Great. Let's lock those two action items in. Priya has the circuit breaker PR due Friday, and Carlos owns the staging load test on Monday.</v>

14
00:01:52.400 --> 00:02:02.150
<v Maya Lin>Okay, shifting gears to item two on the agenda: the v3.4 mobile app release timeline. Jordan, where are we standing with iOS and Android QA?</v>

15
00:02:02.600 --> 00:02:14.880
<v Jordan Vance>Android is completely green and passed regression testing yesterday. On iOS, we hit a snag with Apple Pay biometric prompts crashing on iOS 18.2 beta devices.</v>

16
00:02:15.300 --> 00:02:21.750
<v Priya Patel>Wait, is that blocking the App Store submission scheduled for next Wednesday?</v>

17
00:02:22.100 --> 00:02:34.450
<v Jordan Vance>It would if we ship Apple Pay Express in v3.4. Our mobile lead suggested decoupling Apple Pay Express into a v3.4.1 hotfix next week so the core release ships on schedule.</v>

18
00:02:34.900 --> 00:02:42.300
<v Maya Lin>Does marketing have any campaign assets tied specifically to Apple Pay Express for next Wednesday's launch?</v>

19
00:02:42.750 --> 00:02:51.100
<v Jordan Vance>I checked with Hannah in product marketing this morning—their launch emails only highlight the new saved-cart sync and dark mode UI. Apple Pay isn't featured until December.</v>

20
00:02:51.550 --> 00:03:01.800
<v Maya Lin>Perfect. Let's make that official: we are decoupling Apple Pay Express from v3.4 and moving it to v3.4.1 so iOS and Android launch together next Wednesday, November 25th.</v>

21
00:03:02.250 --> 00:03:09.900
<v Jordan Vance>Sounds good. I'll update the release branch feature flags today and notify the App Store release coordinator by end of day.</v>

22
00:03:10.400 --> 00:03:20.650
<v Maya Lin>Awesome. Last major topic before Carlos has to drop: Q4 cloud and AI inference infrastructure spend. Priya, you shared the updated AWS and Groq usage projections?</v>

23
00:03:21.100 --> 00:03:35.800
<v Priya Patel>Yes. Our staging Kubernetes cluster has been running oversized GPU nodes 24/7, which added about $3,400 in unnecessary spend over the last thirty days. Also, our unchunked transcript summarization jobs were burning huge token volumes.</v>

24
00:03:36.250 --> 00:03:43.400
<v Carlos Rivera>How much did the new semantic chunking rollout save on the summarization pipeline?</v>

25
00:03:43.850 --> 00:03:54.900
<v Priya Patel>By stripping VTT metadata bloat and filtering out conversational filler before LLM extraction, we cut input token consumption by roughly sixty-five percent across long calls.</v>

26
00:03:55.350 --> 00:04:06.200
<v Maya Lin>That's a massive win. What about the staging GPU nodes? Can we put those on an automated night and weekend shutdown schedule?</v>

27
00:04:06.650 --> 00:04:17.500
<v Carlos Rivera>Definitely. Nobody runs staging benchmarks between 8 PM and 7 AM Eastern or over the weekend. Scaling those node groups to zero off-hours will save around $2,200 a month.</v>

28
00:04:17.950 --> 00:04:26.800
<v Maya Lin>Let's approve that right now. We will implement automated off-hours scaling to zero for all staging GPU node groups starting this week.</v>

29
00:04:27.250 --> 00:04:35.900
<v Carlos Rivera>I'll configure the Terraform scheduled autoscaling policies tomorrow morning and post confirmation in the #infra-ops channel by Thursday afternoon.</v>

30
00:04:36.350 --> 00:04:43.100
<v Jordan Vance>Quick question—if someone needs to run an urgent late-night load test on staging, is there an easy manual override?</v>

31
00:04:43.550 --> 00:04:51.200
<v Carlos Rivera>Yeah, you just trigger the GitHub Actions scale-up workflow and the nodes spin up in about three minutes.</v>

32
00:04:51.650 --> 00:04:56.400
<v Jordan Vance>Clean. Works for me.</v>

33
00:04:56.850 --> 00:05:06.100
<v Maya Lin>One final administrative note before we wrap: we are moving our weekly sprint planning sync from Wednesday mornings to Thursdays at 10:30 AM starting in December to avoid overlapping with the platform architecture review.</v>

34
00:05:06.550 --> 00:05:13.800
<v Maya Lin>I'll send out the updated recurring calendar invites later this afternoon. Any last blockers or questions before we give everyone ten minutes back?</v>

35
00:05:14.200 --> 00:05:18.450
<v Priya Patel>Nothing from my side. Thanks everyone!</v>

36
00:05:18.800 --> 00:05:23.100
<v Carlos Rivera>All good here. Have a great rest of your Wednesday.</v>
"""



    preprocess_transcript(text)
    #print(preprocess_transcript(text))

