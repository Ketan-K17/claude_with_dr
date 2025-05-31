#!/usr/bin/env python3
"""
Example usage of the Groq Deep Researcher

This script demonstrates how to use the refactored research assistant
that now uses Groq's models instead of local LLMs.
"""

import os
from dotenv import load_dotenv
from src.claude_deep_researcher.graph import graph
from src.claude_deep_researcher.state import SummaryStateInput

def main():
    """Main function to demonstrate the research assistant."""
    
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Check if required API keys are set
    if not os.getenv("GROQ_API_KEY"):
        print("❌ Error: GROQ_API_KEY environment variable is not set")
        print("Please set your Groq API key:")
        print("export GROQ_API_KEY='your-api-key-here'")
        return
    
    if not os.getenv("TAVILY_API_KEY"):
        print("❌ Error: TAVILY_API_KEY environment variable is not set")
        print("Please set your Tavily API key:")
        print("export TAVILY_API_KEY='your-api-key-here'")
        return
    
    # Example research topics
    research_topics = [
        "Latest developments in artificial intelligence and machine learning in 2024",
        "Impact of renewable energy adoption on global climate change",
        "Current state of quantum computing technology and its applications",
        "Emerging trends in cybersecurity and data privacy"
    ]
    
    # Let user choose a topic or enter their own
    print("🔬 Groq Deep Researcher")
    print("=" * 50)
    print("\nChoose a research topic:")
    for i, topic in enumerate(research_topics, 1):
        print(f"{i}. {topic}")
    print(f"{len(research_topics) + 1}. Enter your own topic")
    
    try:
        choice = input(f"\nEnter your choice (1-{len(research_topics) + 1}): ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(research_topics):
            research_topic = research_topics[int(choice) - 1]
        elif choice == str(len(research_topics) + 1):
            research_topic = input("Enter your research topic: ").strip()
            if not research_topic:
                print("❌ Error: No topic entered")
                return
        else:
            print("❌ Error: Invalid choice")
            return
            
    except KeyboardInterrupt:
        print("\n👋 Research cancelled")
        return
    
    # Configuration for the research
    config = {
        "configurable": {
            "groq_model": "llama-3.3-70b-versatile",  # Use GPT-4 for best results
            "temperature": 0.1,       # Low temperature for focused research
            "max_web_research_loops": 3,  # 3 research iterations
            "fetch_full_page": True,  # Get full page content
            "strip_thinking_tokens": True  # Clean up output
        }
    }
    
    # Create input state
    input_state = SummaryStateInput(research_topic=research_topic)
    
    print(f"\n🚀 Starting research on: {research_topic}")
    print("⏳ This may take a few minutes...")
    print("-" * 50)
    
    try:
        # Run the research
        result = graph.invoke(input_state, config=config)
        
        # Display results
        print("\n📊 Research Complete!")
        print("=" * 50)
        print(result["running_summary"])
        
    except Exception as e:
        print(f"\n❌ Error during research: {str(e)}")
        print("Please check your API keys and network connection.")
        return

if __name__ == "__main__":
    main() 