import re

import tiktoken
from langchain_core.messages import BaseMessage

from app.core.settings import settings


class TokenCounter:

    def __init__(self, model_name: str | None = None):
        model_name = model_name or settings.openai_chat_model

        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            self.encoding = tiktoken.get_encoding("o200k_base")

    def count(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def split_text(
            self,
            text: str,
            max_tokens: int,
    ) -> list[str]:
        if max_tokens <= 0:
            raise ValueError("max_tokens must be greater than zero.")

        text = text.strip()

        if not text:
            return []

        sentences = re.split(r"(?<=[.!?])\s+", text)

        segments = []
        current_sentences = []

        for sentence in sentences:
            if not sentence:
                continue

            candidate = " ".join(
                current_sentences + [sentence]
            )

            if self.count(candidate) <= max_tokens:
                current_sentences.append(sentence)
                continue

            if current_sentences:
                segments.append(" ".join(current_sentences))
                current_sentences = []

            if self.count(sentence) <= max_tokens:
                current_sentences.append(sentence)
                continue

            # A single sentence is too large.
            # Split it directly at token boundaries.
            tokens = self.encoding.encode(sentence)

            for start in range(0, len(tokens), max_tokens):
                token_segment = tokens[start:start + max_tokens]
                segments.append(
                    self.encoding.decode(token_segment)
                )

        if current_sentences:
            segments.append(" ".join(current_sentences))

        return segments

    def count_messages(
            self,
            messages: list[BaseMessage],
    ) -> int:
        """
        Estimate the token count of rendered chat messages.

        Includes message content and a small allowance for
        message structure and role metadata.
        """
        total_tokens = 0

        for message in messages:
            total_tokens += 4  # Message structure overhead

            content = message.content

            if isinstance(content, str):
                total_tokens += self.count(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        text = block.get("text")
                        if isinstance(text, str):
                            total_tokens += self.count(text)
                    elif isinstance(block, str):
                        total_tokens += self.count(block)

            total_tokens += self.count(message.type)

        return total_tokens + 2  # Conversation-level overhead
