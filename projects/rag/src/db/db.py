import os
import shutil
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from src.loaders.loaders import Loader 

class Database:
    def __init__(self, embedding_model, docs, persist_directory="db/chroma_db", device = "cpu", clean_db = False):
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={"device": device}, 
            encode_kwargs={"normalize_embeddings": True},
        )
        self.loader = Loader(docs_path=docs)
        self.persist_directory = persist_directory
        self.docs = docs 
        self.clean_db = clean_db
 
    def create_vector_store(self, chunks):
        """Create and persist ChromaDB vector store"""
        print("Creating embeddings and storing in ChromaDB...")
       
        # Create ChromaDB vector store
        print("--- Creating vector store ---")
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embedding_model,
            persist_directory=self.persist_directory, 
            collection_metadata={"hnsw:space": "cosine"}
        )
        print("--- Finished creating vector store ---")
        
        print(f"Vector store created and saved to {self.persist_directory}")

        return vectorstore

    def create_or_use_existing_db(self):   
        print(f"{self.persist_directory}")
        # Check if vector store already exists
        if not self.clean_db and os.path.exists(self.persist_directory):
            print("✅ Vector store already exists. No need to re-process documents.")

            vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding_model, 
                collection_metadata={"hnsw:space": "cosine"}
            )
            print(f"Loaded existing vector store with {vectorstore._collection.count()} documents")

            self.vectorstore = vectorstore
        else: 
            if self.clean_db and os.path.exists(self.persist_directory):
                print("clean_db=True: removing existing vector store...")
                shutil.rmtree(self.persist_directory)
            print("Initializing vector store...\n")
            
            # Step 1: Load documents
            documents = self.loader.load_documents()  

            # Step 2: Split into chunks
            chunks = self.loader.split_documents(documents)
            
            # # Step 3: Create vector store
            vectorstore = self.create_vector_store(chunks)

            self.vectorstore = vectorstore

        return vectorstore



    def invoke_query(self, query):
        # Search for relevant documents
        # retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})

        # Similarity with score threshold
        # Only return documents above a certain similarity score
        retriever = self.vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": 3,
                "score_threshold": 0.3  # Only return chunks with cosine similarity ≥ 0.3
            }
        )

        # Maximum marginal relevance
        # Balance relevance and diversity - avoids redundant results
        # retriever = self.vectorstore.as_retriever(
        #     search_type="mmr",
        #     search_kwargs= {
        #         "k": 3,
        #         "fetch_k": 10,
        #         "lambda_mult": 0.5
        #     }
        # )

        relevant_docs = retriever.invoke(query)

        print(f"User Query: {query}")
        # Display results
        print("--- Context ---")
        for i, doc in enumerate(relevant_docs, 1):
            print(f"Document {i}:\n{doc.page_content}\n")

        return relevant_docs