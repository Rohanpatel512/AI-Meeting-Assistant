import tiktoken 

def evaluate_token_usage(raw_text: str, preprocessed_text: str, model_name: str = "openai/gpt-oss-20b"):
    """
    Evaluates the token usage of the preprocessed text using the specified model's tokenizer.

    Args:
        raw_text (str): The original text before preprocessing.
        preprocessed_text (str): The text after preprocessing.
        model_name (str): The name of the model to use for tokenization. Default is "openai/gpt-oss-20b".

    Returns:
        None 
    """
    # Get the tokenizer for the specified model
    encoding = tiktoken.encoding_for_model(model_name)

    # Calculate token counts
    raw_tokens = len(encoding.encode(raw_text))
    clean_tokens = len(encoding.encode(preprocessed_text))

    # Calculate metrics
    tokens_saved = raw_tokens - clean_tokens
    reduction_percentage = (tokens_saved / raw_tokens) * 100
    
    print("TOKEN METRICS REPORT:")
    print(f"  • Raw Transcript:       {raw_tokens:,} tokens")
    print(f"  • Preprocessed Payload: {clean_tokens:,} tokens")
    print(f"  • Absolute Tokens Cut:  {tokens_saved:,} tokens")
    print(f"  • Total Cost Reduction: {reduction_percentage:.2f}%")
    
    return reduction_percentage  


  