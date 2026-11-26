"""Language selection controls new replies and summaries, not source quotes."""

from conversation import ConversationProvider, PROMPT, SCHEMA, ITEMS
from localization import ITEMS_EN


class BilingualConversationProvider(ConversationProvider):
    def __init__(self, key=None, base_url=None, language="zh"):
        super().__init__(key=key, base_url=base_url)
        if language not in ("en", "zh"):
            raise ValueError("Unsupported language")
        self.language = language

    def respond(self, messages, candidates):
        language = (
            "English"
            if self.language == "en"
            else "Traditional Chinese (match Cantonese phrasing when appropriate)"
        )
        instruction = (
            PROMPT
            + f"\nUI language is {language}. Write every new reply and evidence summary in {language}, even when earlier conversation uses another language. Keep quote fields EXACTLY in their original language."
        )
        items = ITEMS_EN if self.language == "en" else ITEMS
        return self.client.structured(
            instruction,
            {
                "messages": list(messages),
                "provisional_evidence": list(candidates.values()),
                "domains": {str(i): name for i, name in enumerate(items, 1)},
            },
            SCHEMA,
            "phq8_conversation",
            max_output_tokens=3200,
        )
