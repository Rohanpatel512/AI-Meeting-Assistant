import tiktoken 

def evaluate_token_usage(raw_text: str, chunked_data: list, prompt: str, model_name: str = "openai/gpt-oss-120b"):
    """
    Evaluates the token usage of the preprocessed text using the specified model's tokenizer.

    Args:
        raw_text (str): The original text before preprocessing.
        chunked_data (list): Preprocessed transcript that has been chunked.
        prompt (str): Prompt passed on as instructions to the LLM model.
        model_name (str): The name of the model to use for tokenization. Default is "openai/gpt-oss-20b".

    Returns:
        reduction_percentage (float) - Percentage of input tokens reduced  
    """

    try:
        # Get the tokenizer for the specified model
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        encoding = tiktoken.get_encoding("o200k_harmony")

    # Calculate token counts
    prompt_tokens = len(encoding.encode(prompt))
    raw_tokens = prompt_tokens + len(encoding.encode(raw_text))

    chunk_text_tokens = sum(
        len(encoding.encode("\n".join(line.replace("[SEP]", ":") for line in chunk)))
        for chunk in chunked_data
    )
    actual_sent_tokens = chunk_text_tokens + (len(chunked_data) * prompt_tokens)

    # 4. Calculate true net savings
    tokens_saved = raw_tokens - actual_sent_tokens
    reduction_percentage = (tokens_saved / raw_tokens) * 100 if raw_tokens > 0 else 0.0

    print("TOKEN METRICS REPORT:")
    print(f"  • Raw Single-Shot Baseline: {raw_tokens:,} tokens")
    print(f"  • Chunks Sent / Total:      {len(chunked_data)}")
    print(f"  • Actual Chunked Payload:   {actual_sent_tokens:,} tokens")
    print(f"  • Net Tokens Saved:         {tokens_saved:,} tokens")
    print(f"  • Net Input Cost Reduction: {reduction_percentage:.2f}%")

    return reduction_percentage 