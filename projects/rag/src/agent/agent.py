from langchain.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from src.db.db import Database

class Agent:

    def __init__(self, config):
        # Create a ChatOpenAI model 
        self.model = ChatOpenAI(
            model=config['llm_model'],
            base_url=config['base_url'],
            api_key=config['api_key'],
            temperature=0,
        )
        self.chat_history = []
 
        print("Initializing database...")
        db = Database(embedding_model=config['embedding_model'], docs=config['docs_path'], persist_directory=config['persist_directory'], device=config['device'], clean_db=config['clean_db'])
        self.db = db.create_or_use_existing_db()
        print("Sucessfully initialized database...")

    def invoke_message(self, query):
        # Step 1: Make the question clear using conversation history
        if self.chat_history:
            # Ask AI to make the question standalone
            messages = [
                SystemMessage(content="Given the chat history, rewrite the new question to be standalone and searchable. Just return the rewritten question."),
            ] + self.chat_history + [
                HumanMessage(content=f"New question: {query}")
            ]
            
            result = self.model.invoke(messages)
            search_question = result.content.strip()
            print(f"Searching for: {search_question}")
        else:
            search_question = query

        # Step 2: Find relevant documents
        retriever = self.db.as_retriever(search_kwargs={"k": 5})
        docs = retriever.invoke(search_question)
        
        print(f"Found {len(docs)} relevant documents:")
        for i, doc in enumerate(docs, 1):
            # Show first 2 lines of each document
            lines = doc.page_content.split('\n')[:2]
            preview = '\n'.join(lines)
            print(f"  Doc {i}: {preview}...")

        # Step 3: Create final prompt (context first, question last: small models attend to the end)
        context = "\n\n".join(f"[{i}] {doc.page_content}" for i, doc in enumerate(docs, 1))
        combined_input = (
            f"Documents:\n{context}\n\n"
            f"Question: {query}\n\n"
            "Answer using only the documents above. "
            "If they do not contain the answer, say you don't have enough information."
        )
        
        # Step 4: Get the answer
        messages = [
            SystemMessage(content="You are a helpful assistant that answers questions based on provided documents and conversation history."),
        ] + self.chat_history + [
            HumanMessage(content=combined_input)
        ]
        
        result = self.model.invoke(messages)
        answer = result.content
        
        # Step 5: Remember this conversation
        self.chat_history.append(HumanMessage(content=query))
        self.chat_history.append(AIMessage(content=answer))    
        print(f"Answer: {answer}")
        return answer