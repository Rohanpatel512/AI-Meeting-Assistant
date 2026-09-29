import re 

FILLER_PATTERN = re.compile(r"\b(?:um+|ah+|err+|er+|em+)\b", re.IGNORECASE)
ARTIFACT_PATTERN = re.compile(
    r"\[(?:inaudible|unintelligible|background noise|music)\]",
    re.IGNORECASE
)

def preprocess_text(text):

    # Remove filler words (e.g., "um", "ah", etc)
    text = FILLER_PATTERN.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Remove artifact transcription (e.g, [inaudible])
    text = ARTIFACT_PATTERN.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text