import json

from typing_extensions import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from groq import Groq
from langgraph.graph import START, END, StateGraph
from langfuse.callback import CallbackHandler

from .configuration import Configuration, SearchAPI
from .utils import deduplicate_and_format_sources, tavily_search, format_sources, strip_thinking_tokens
from .state import SummaryState, SummaryStateInput, SummaryStateOutput
from .prompts import query_writer_instructions, summarizer_instructions, reflection_instructions, get_current_date
from dotenv import load_dotenv
load_dotenv()

client = Groq()

# Initialize Langfuse CallbackHandler for tracing
langfuse_handler = CallbackHandler()


# Nodes
def generate_query(state: SummaryState, config: RunnableConfig):
    """LangGraph node that generates a search query based on the research topic.
    
    Uses OpenAI's GPT models to create an optimized search query for web research based on
    the user's research topic.
    
    Args:
        state: Current graph state containing the research topic
        config: Configuration for the runnable, including OpenAI model settings
        
    Returns:
        Dictionary with state update, including search_query key containing the generated query
    """

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = query_writer_instructions.format(
        current_date=current_date,
        research_topic=state.research_topic
    )

    # Generate a query
    configurable = Configuration.from_runnable_config(config)

    result = client.chat.completions.create(
        model=configurable.groq_model,
        temperature=configurable.temperature,
        messages=[
            {
                "role": "system",
                "content": formatted_prompt
            },
            {
                "role": "user",
                "content": "Generate a query for web search:"
            }
        ],
        response_format={"type": "json_object"}
    )
    
    # Get the content
    content = result.choices[0].message.content

    # Parse the JSON response and get the query
    try:
        query = json.loads(content)
        search_query = query['query']
    except (json.JSONDecodeError, KeyError):
        # If parsing fails or the key is not found, use a fallback query
        if configurable.strip_thinking_tokens:
            content = strip_thinking_tokens(content)
        search_query = content
    return {"search_query": search_query}

def web_research(state: SummaryState, config: RunnableConfig):
    """LangGraph node that performs web research using the generated search query.
    
    Executes a web search using Tavily search API and formats the results for further processing.
    
    Args:
        state: Current graph state containing the search query and research loop count
        config: Configuration for the runnable, including search API settings
        
    Returns:
        Dictionary with state update, including sources_gathered, research_loop_count, and web_research_results
    """

    # Configure
    configurable = Configuration.from_runnable_config(config)

    # Search the web using Tavily
    search_results = tavily_search(
        state.search_query, 
        fetch_full_page=configurable.fetch_full_page, 
        max_results=3
    )
    search_str = deduplicate_and_format_sources(
        search_results, 
        max_tokens_per_source=1000, 
        fetch_full_page=configurable.fetch_full_page
    )

    return {
        "sources_gathered": [format_sources(search_results)], 
        "research_loop_count": state.research_loop_count + 1, 
        "web_research_results": [search_str]
    }

def summarize_sources(state: SummaryState, config: RunnableConfig):
    """LangGraph node that summarizes web research results.
    
    Uses OpenAI's GPT models to create or update a running summary based on the newest web research 
    results, integrating them with any existing summary.
    
    Args:
        state: Current graph state containing research topic, running summary,
              and web research results
        config: Configuration for the runnable, including OpenAI model settings
        
    Returns:
        Dictionary with state update, including running_summary key containing the updated summary
    """

    # Existing summary
    existing_summary = state.running_summary

    # Most recent web research
    most_recent_web_research = state.web_research_results[-1]

    # Build the human message
    if existing_summary:
        human_message_content = (
            f"<Existing Summary> \n {existing_summary} \n <Existing Summary>\n\n"
            f"<New Context> \n {most_recent_web_research} \n <New Context>"
            f"Update the Existing Summary with the New Context on this topic: \n <User Input> \n {state.research_topic} \n <User Input>\n\n"
        )
    else:
        human_message_content = (
            f"<Context> \n {most_recent_web_research} \n <Context>"
            f"Create a Summary using the Context on this topic: \n <User Input> \n {state.research_topic} \n <User Input>\n\n"
        )

    # Run the LLM
    configurable = Configuration.from_runnable_config(config)
    
    result = client.chat.completions.create(
        model=configurable.groq_model,
        temperature=configurable.temperature,
        messages=[
            {
                "role": "system",
                "content": summarizer_instructions
            },
            {
                "role": "user",
                "content": human_message_content
            }
        ]
    )

    # Strip thinking tokens if configured
    running_summary = result.choices[0].message.content
    if configurable.strip_thinking_tokens:
        running_summary = strip_thinking_tokens(running_summary)

    return {"running_summary": running_summary}

def reflect_on_summary(state: SummaryState, config: RunnableConfig):
    """LangGraph node that identifies knowledge gaps and generates follow-up queries.
    
    Analyzes the current summary to identify areas for further research and generates
    a new search query to address those gaps. Uses structured output to extract
    the follow-up query in JSON format.
    
    Args:
        state: Current graph state containing the running summary and research topic
        config: Configuration for the runnable, including OpenAI model settings
        
    Returns:
        Dictionary with state update, including search_query key containing the generated follow-up query
    """

    # Generate a query
    configurable = Configuration.from_runnable_config(config)
    
    # Use Groq with JSON mode
    result = client.chat.completions.create(
        model=configurable.groq_model,
        temperature=configurable.temperature,
        messages=[
            {
                "role": "system",
                "content": reflection_instructions.format(research_topic=state.research_topic)
            },
            {
                "role": "user",
                "content": f"Reflect on our existing knowledge: \n === \n {state.running_summary}, \n === \n And now identify a knowledge gap and generate a follow-up web search query:"
            }
        ],
        response_format={"type": "json_object"}
    )
    content = result.choices[0].message.content

    
    # Strip thinking tokens if configured
    try:
        # Try to parse as JSON first
        reflection_content = json.loads(content)
        # Get the follow-up query
        query = reflection_content.get('follow_up_query')
        # Check if query is None or empty
        if not query:
            # Use a fallback query
            return {"search_query": f"Tell me more about {state.research_topic}"}
        return {"search_query": query}
    except (json.JSONDecodeError, KeyError, AttributeError):
        # If parsing fails or the key is not found, use a fallback query
        return {"search_query": f"Tell me more about {state.research_topic}"}

def finalize_summary(state: SummaryState):
    """LangGraph node that finalizes the research summary.
    
    Prepares the final output by deduplicating and formatting sources, then
    combining them with the running summary to create a well-structured
    research report with proper citations.
    
    Args:
        state: Current graph state containing the running summary and sources gathered
        
    Returns:
        Dictionary with state update, including running_summary key containing the formatted final summary with sources
    """

    # Deduplicate sources before joining
    seen_sources = set()
    unique_sources = []
    
    for source in state.sources_gathered:
        # Split the source into lines and process each individually
        for line in source.split('\n'):
            # Only process non-empty lines
            if line.strip() and line not in seen_sources:
                seen_sources.add(line)
                unique_sources.append(line)
    
    # Join the deduplicated sources
    all_sources = "\n".join(unique_sources)
    state.running_summary = f"## Summary\n{state.running_summary}\n\n ### Sources:\n{all_sources}"
    return {"running_summary": state.running_summary}

def route_research(state: SummaryState, config: RunnableConfig) -> Literal["finalize_summary", "web_research"]:
    """LangGraph routing function that determines the next step in the research flow.
    
    Controls the research loop by deciding whether to continue gathering information
    or to finalize the summary based on the configured maximum number of research loops.
    
    Args:
        state: Current graph state containing the research loop count
        config: Configuration for the runnable, including max_web_research_loops setting
        
    Returns:
        String literal indicating the next node to visit ("web_research" or "finalize_summary")
    """

    configurable = Configuration.from_runnable_config(config)
    if state.research_loop_count <= configurable.max_web_research_loops:
        return "web_research"
    else:
        return "finalize_summary"

# Add nodes and edges
builder = StateGraph(SummaryState, input=SummaryStateInput, output=SummaryStateOutput, config_schema=Configuration)
builder.add_node("generate_query", generate_query)
builder.add_node("web_research", web_research)
builder.add_node("summarize_sources", summarize_sources)
builder.add_node("reflect_on_summary", reflect_on_summary)
builder.add_node("finalize_summary", finalize_summary)

# Add edges
builder.add_edge(START, "generate_query")
builder.add_edge("generate_query", "web_research")
builder.add_edge("web_research", "summarize_sources")
builder.add_edge("summarize_sources", "reflect_on_summary")
builder.add_conditional_edges("reflect_on_summary", route_research)
builder.add_edge("finalize_summary", END)

graph = builder.compile().with_config({"callbacks": [langfuse_handler]})