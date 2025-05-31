import os
from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Optional, Literal

from langchain_core.runnables import RunnableConfig

class SearchAPI(Enum):
    TAVILY = "tavily"

class Configuration(BaseModel):
    """The configurable fields for the research assistant."""

    max_web_research_loops: int = Field(
        default=3,
        title="Research Depth",
        description="Number of research iterations to perform"
    )
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        title="Groq Model Name",
        description="Name of the Groq model to use (e.g., llama-3.3-70b-versatile)"
    )
    groq_api_key: Optional[str] = Field(
        default=None,
        title="Groq API Key",
        description="Groq API key for accessing the models"
    )
    search_api: Literal["tavily"] = Field(
        default="tavily",
        title="Search API",
        description="Web search API to use (Tavily only)"
    )
    fetch_full_page: bool = Field(
        default=True,
        title="Fetch Full Page",
        description="Include the full page content in the search results"
    )
    temperature: float = Field(
        default=0.0,
        title="Temperature",
        description="Temperature for OpenAI model sampling (0.0 to 1.0)"
    )
    strip_thinking_tokens: bool = Field(
        default=True,
        title="Strip Thinking Tokens",
        description="Whether to strip <think> tokens from model responses"
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        
        # Get raw values from environment or config
        raw_values: dict[str, Any] = {
            name: os.environ.get(name.upper(), configurable.get(name))
            for name in cls.model_fields.keys()
        }
        
        # Special handling for OpenAI API key - check standard environment variable
        if raw_values.get("openai_api_key") is None:
            raw_values["openai_api_key"] = os.environ.get("OPENAI_API_KEY")
        
        # Filter out None values
        values = {k: v for k, v in raw_values.items() if v is not None}
        
        return cls(**values)