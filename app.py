#!/usr/bin/env python3
"""
Groq Deep Researcher App

This module provides a simple interface to run the research workflow
and get the summary results. Can be used programmatically or as a standalone script.
"""

import os
from dotenv import load_dotenv
from src.openai_deep_researcher.graph import graph
from src.openai_deep_researcher.state import SummaryStateInput


def run_research(research_topic: str) -> str:
    """
    Run the research workflow for a given topic and return the summary.
    
    Args:
        research_topic (str): The topic to research
        
    Returns:
        str: The research summary from the running_summary field
        
    Raises:
        ValueError: If API keys are not set
        Exception: If research fails
    """
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Check if required API keys are set
    if not os.getenv("GROQ_API_KEY"):
        raise ValueError("GROQ_API_KEY environment variable is not set. Please set your Groq API key.")
    
    if not os.getenv("TAVILY_API_KEY"):
        raise ValueError("TAVILY_API_KEY environment variable is not set. Please set your Tavily API key.")
    
    # Configuration for the research
    config = {
        "configurable": {
            "groq_model": "llama-3.3-70b-versatile",  # Use Llama model for research
            "temperature": 0.1,       # Low temperature for focused research
            "max_web_research_loops": 3,  # 3 research iterations
            "fetch_full_page": True,  # Get full page content
            "strip_thinking_tokens": True  # Clean up output
        }
    }
    
    # Create input state
    input_state = SummaryStateInput(research_topic=research_topic)
    
    try:
        # Run the research
        result = graph.invoke(input_state, config=config)
        
        # Return the summary
        return result["running_summary"]
        
    except Exception as e:
        raise Exception(f"Research failed: {str(e)}")


def main():
    """Main function for standalone script usage."""
    
    print("🔬 Groq Deep Researcher")
    print("=" * 50)
    
    try:
        # Get research topic from user
        research_topic = input("Enter your research topic: ").strip()
        
        if not research_topic:
            print("❌ Error: No topic entered")
            return
        
        print(f"\n🚀 Starting research on: {research_topic}")
        print("⏳ This may take a few minutes...")
        print("-" * 50)
        
        # Run the research
        summary = run_research(research_topic)
        
        # Display results
        print("\n📊 Research Complete!")
        print("=" * 50)
        print(summary)
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {str(e)}")
        print("Please check your environment variables.")
    except Exception as e:
        print(f"\n❌ Error during research: {str(e)}")
        print("Please check your API keys and network connection.")
    except KeyboardInterrupt:
        print("\n👋 Research cancelled")


if __name__ == "__main__":
    main() 