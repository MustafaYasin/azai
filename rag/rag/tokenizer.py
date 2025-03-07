
from tiktoken import get_encoding
from transformers.tokenization_utils_base import PreTrainedTokenizerBase


class OpenAITokenizerWrapper(PreTrainedTokenizerBase):
    def __init__(
        self, model_name: str = "cl100k_base", max_length: int = 8191, **kwargs
    ):
        super().__init__(model_max_length=max_length, **kwargs)
        self.tokenizer = get_encoding(model_name)
        self._vocab_size = self.tokenizer.max_token_value

    def tokenize(self, text: str, **kwargs) -> list[str]:
        return [str(t) for t in self.tokenizer.encode(text)]

    def _tokenize(self, text: str) -> list[str]:
        return self.tokenize(text)

    def _convert_token_to_id(self, token: str) -> int:
        return int(token)

    def _convert_id_to_token(self, index: int) -> str:
        return str(index)

    def get_vocab(self) -> dict[str, int]:
        return dict(enumerate(range(self.vocab_size)))

    @property
    def vocab_size(self) -> int:
        return self._vocab_size

    def save_vocabulary(self, *args) -> tuple[str]:
        return ()

    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        return cls()
