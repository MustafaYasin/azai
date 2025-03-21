_tokenizer = None


def _get_tokenizer():  # noqa: ANN202
    global _tokenizer  # noqa: PLW0603
    if _tokenizer:
        return _tokenizer
    import tiktoken

    _tokenizer = tiktoken.get_encoding("cl100k_base")
    return _tokenizer


def count_tokens(text: str) -> int:
    if not isinstance(text, str):
        return 0
    return len(_get_tokenizer().encode(text))
