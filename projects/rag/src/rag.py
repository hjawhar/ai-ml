import os
from dotenv import load_dotenv
from src.agent.agent import Agent

load_dotenv()

def main():
    """Main ingestion pipeline"""
    print("=== RAG Pipeline ===\n")

    config = {
        "embedding_model": os.environ["embedding_model"],
        "llm_model": os.environ["llm_model"],
        "base_url": os.environ["base_url"],
        "api_key": os.environ["api_key"],
        "docs_path": os.environ["docs_path"],
        "persist_directory": os.environ["persist_directory"],
        "device": os.environ["device"],
        "clean_db": os.environ["clean_db"].lower() == "true",
    }

    print("Initializing agent...") 
    agent = Agent(config)
    print("Successfully initialized agent...")

    while True:
        question = input("Ask a question: ")
        if question.lower() == "quit":
            exit()
        else:
            agent.invoke_message(question) 

if __name__ == "__main__":
    main()