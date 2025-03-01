def truncate(text: str, max_length: int = 1500) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
