import tiktoken 
from sentence_transformers import SentenceTransformer, util 
import numpy as np 
import torch.nn.functional as F

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def get_token_count(preprocessed_text: str, model_name: str = "openai/gpt-oss-120b"):
    """
    Returns exact number of tokens in a string.
    Explicitly uses the tiktoken tokenizer matching OpenAIs gpt-oss architecuture.

    args:
        preprocessed_text (str) - Transcript which as been preprocessed for chunking.
        model_name (str) - Primary model used for summarization of transcript.
    
    returns:   
        token_count (int) - Total number of tokens in the preprocessed text 

    """
    try:
        # Get the tokenizer for the specified model
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        encoding = tiktoken.get_encoding("o200k_harmony")

    return len(encoding.encode(preprocessed_text))



def token_aware_chunking(preprocessed_text: str, dialects_segment: list) -> list:
    """
    Chunks according to if transcript has or doesn't have speaker tags.

    args:
        preprocessed_text (list) - List of dialects processed for chunking
        has_speakers (boolean) - True if preprocessed text has speaker names, False otherwise.
    
    returns:
        chunks (list) - A list of chunked transcript text.
    """

    chunks = _chunk_text(dialects_segment)

    return chunks

def get_segment_distances(embeddings: list):
    """
    Gets the distance gap between each line of text to help compute similarity threshold

    args:
        embeddings (list) - A list of vector embeddings for each line of text.
    
    returns:
        distances (list) - Line distance between each vector embedding.
    """

    distances = []

    for i in range(1, len(embeddings)):
        distance = util.cos_sim(embeddings[i], embeddings[i - 1]).item()

        distances.append(1 - distance)

    return distances


def _chunk_text(dialects_segment: list, window_size: int = 1):
    """
    Chunks transcript that contain speaker tags.

    args:
        dialects_segment (list) - Preprocessed transcript that contains speaker tags in the form of a list.
    
    return
        chunks (list) - A list of chunked transcript text.
    
    """

    chunks = []
    current_chunk = [dialects_segment[0]]
    clean_texts = [segment.split('[SEP]', 1)[-1].strip() if '[SEP]' in segment else segment.strip() for segment in dialects_segment]

    # Create sliding windows
    window_texts = [
        " ".join(clean_texts[max(0, i - window_size) : min(len(clean_texts), i + window_size + 1)])
        for i in range(0, len(clean_texts))
    ]

    # Encode all windows 
    embeddings = model.encode(window_texts, batch_size=32, convert_to_tensor=True, normalize_embeddings=True)

    # Compute distances between each window texts 
    distances = get_segment_distances(embeddings)

    percent = 75 if len(dialects_segment) < 40 else 90
    similarity_threshold = np.percentile(distances, percent)

    current_word_count = len(clean_texts[0].split())
    max_words = 1000
    min_words = 400

    for i, distance in enumerate(distances):
        next_segment = dialects_segment[i + 1]
        next_words = len(clean_texts[i + 1].split())

        is_topic_shift = distance > similarity_threshold and current_word_count >= min_words
        exceeds_max_size = (current_word_count + next_words) > max_words

        if is_topic_shift or exceeds_max_size:
            chunks.append(current_chunk)
            current_chunk = [next_segment]
            current_word_count = next_words 
        else:
            current_chunk.append(next_segment)
            current_word_count += next_words

    if current_chunk:
        chunks.append(current_chunk) 

    return chunks
    