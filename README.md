# OpenAI Deep Researcher

A powerful AI-powered research assistant that uses OpenAI's GPT models to conduct comprehensive web research on any topic. The system performs iterative searches, synthesizes information, and provides detailed summaries with source citations.

## Features

- **Intelligent Query Generation**: Uses GPT models to create optimized search queries
- **Iterative Research**: Performs multiple research loops to gather comprehensive information
- **Source Synthesis**: Combines information from multiple sources into coherent summaries
- **Reflection & Gap Analysis**: Identifies knowledge gaps and generates follow-up queries
- **Citation Management**: Automatically deduplicates and formats source citations

## Setup

### Prerequisites

- Python 3.8+
- OpenAI API key
- Tavily API key (for web search)

### Installation

1. Clone the repository and navigate to the project directory

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export OPENAI_API_KEY="your-openai-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
```

## Configuration

The system can be configured through environment variables or runtime configuration:

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: OpenAI model to use (default: "gpt-4")
- `TEMPERATURE`: Temperature for model sampling (default: 0.0)
- `MAX_WEB_RESEARCH_LOOPS`: Number of research iterations (default: 3)
- `FETCH_FULL_PAGE`: Include full page content in search results (default: true)
- `STRIP_THINKING_TOKENS`: Remove thinking tokens from responses (default: true)

### Available Models

The system supports any OpenAI chat model:
- `gpt-4` (recommended for best results)
- `gpt-4-turbo`
- `gpt-3.5-turbo` (faster, more cost-effective)
- `gpt-4o` or other latest models

## Usage

### Basic Usage

```python
from openai_deep_researcher.graph import graph
from openai_deep_researcher.state import SummaryStateInput

# Configure the research
config = {
    "configurable": {
        "openai_model": "gpt-4",
        "max_web_research_loops": 3,
        "fetch_full_page": True
    }
}

# Define research topic
input_state = SummaryStateInput(
    research_topic="Latest developments in renewable energy technology"
)

# Run the research
result = graph.invoke(input_state, config=config)

# Get the final summary
print(result["running_summary"])
```

### Advanced Configuration

```python
from openai_deep_researcher.configuration import Configuration

# Create custom configuration
config = Configuration(
    openai_model="gpt-4-turbo",
    temperature=0.1,
    max_web_research_loops=5,
    fetch_full_page=True,
    strip_thinking_tokens=True
)

# Use with graph
result = graph.invoke(
    input_state, 
    config={"configurable": config.model_dump()}
)
```

## Architecture

The research assistant uses a LangGraph-based workflow with the following nodes:

1. **Generate Query**: Creates optimized search queries using GPT
2. **Web Research**: Performs web search using Tavily API
3. **Summarize Sources**: Synthesizes information from search results
4. **Reflect on Summary**: Identifies gaps and generates follow-up queries
5. **Finalize Summary**: Formats the final research report with citations

The system iteratively loops through research and reflection until the configured number of loops is reached, then finalizes the comprehensive summary.

## Cost Considerations

- **GPT-4**: Higher cost but better quality research and synthesis
- **GPT-3.5-turbo**: Lower cost alternative, suitable for simpler research tasks
- **Token usage**: Depends on research depth and source content length
- **Tavily API**: Separate cost for web search queries

## Migration from Ollama/LMStudio

This codebase has been refactored from a local LLM implementation to use OpenAI's API directly. Key changes:

- Removed dependencies on Ollama and LMStudio
- Simplified configuration to focus on OpenAI models
- Improved JSON mode handling using OpenAI's structured outputs
- Better error handling and fallback mechanisms

## Contributing

When contributing to this project, please ensure:

- All LLM calls use the OpenAI API through the configured model
- Error handling includes appropriate fallbacks
- Configuration changes are documented
- Tests cover new functionality

## License

MIT License 