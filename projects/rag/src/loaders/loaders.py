
import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter

class Loader:
    def __init__(self, docs_path="docs", chunk_size=1000, chunk_overlap=200):
        self.docs_path = docs_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap


    def load_documents(self):
        """Load all text files from the docs directory"""
        print(f"Loading documents from {self.docs_path}...")
        
        # Check if docs directory exists
        if not os.path.exists(self.docs_path):
            raise FileNotFoundError(f"The directory {self.docs_path} does not exist. Please create it and add your company files.")
        
        # Load all .txt files from the docs directory
        loader = DirectoryLoader(
            path=self.docs_path,
            glob="*.txt",
            loader_cls=TextLoader
        )
        
        documents = loader.load()
        
        if len(documents) == 0:
            raise FileNotFoundError(f"No .txt files found in {self.docs_path}. Please add your company documents.")
        
    
        for i, doc in enumerate(documents[:2]):  # Show first 2 documents
            print(f"\nDocument {i+1}:")
            print(f"  Source: {doc.metadata['source']}")
            print(f"  Content length: {len(doc.page_content)} characters")
            print(f"  Content preview: {doc.page_content[:100]}...")
            print(f"  metadata: {doc.metadata}")

        return documents

    def split_documents(self, documents):
        """Split documents into smaller chunks with overlap"""
        print("Splitting documents into chunks...")

        recursive_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ". ", " ", ""],  # Multiple separators
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        # text_splitter = CharacterTextSplitter(
        #     chunk_size=self.chunk_size, 
        #     chunk_overlap=self.chunk_overlap
        # )
        
        chunks = recursive_splitter.split_documents(documents)
        
        if chunks:
            for i, chunk in enumerate(chunks[:5]):
                print(f"\n--- Chunk {i+1} ---")
                print(f"Source: {chunk.metadata['source']}")
                print(f"Length: {len(chunk.page_content)} characters")
                print(f"Content:")
                print(chunk.page_content)
                print("-" * 50)
            
            if len(chunks) > 5:
                print(f"\n... and {len(chunks) - 5} more chunks")
        
        return chunks