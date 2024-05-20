from pydantic import BaseModel


class OpenAIApiConfig(BaseModel):
    """OpenAI API settings."""

    type: str
    base: str
    version: str
    chat_version: str
    key: str
