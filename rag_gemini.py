import os
import json
import numpy as np
from typing import List, Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import pandas as pd
from pathlib import Path

# Load environment variables
load_dotenv()

class RAGSystem:
    """
    Retrieval-Augmented Generation system using Gemini LLM and ChromaDB for vector storage.
    """
    
    def __init__(self, gemini_api_key: str = None):
        """
        Initialize the RAG system.
        
        Args:
            gemini_api_key: Google Gemini API key. If None, will try to get from environment.
        """
        # Initialize Gemini
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable or pass it directly.")
        
        genai.configure(api_key=self.gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        # Initialize embedding model
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))
        self.collection_name = "rag_documents"
        
        # Create or get collection
        try:
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "RAG document collection"}
            )
        except Exception:
            # Collection already exists
            self.collection = self.chroma_client.get_collection(name=self.collection_name)
        
        print("RAG System initialized successfully!")
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Input text to chunk
            chunk_size: Size of each chunk
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]
            
            # Try to break at sentence boundaries
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > start + chunk_size // 2:
                    chunk = text[start:break_point + 1]
                    end = break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
            
            if start >= len(text):
                break
        
        return chunks
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Add documents to the RAG system.
        
        Args:
            documents: List of documents with 'content' and optional 'metadata'
        """
        print(f"Adding {len(documents)} documents to the knowledge base...")
        
        all_chunks = []
        all_embeddings = []
        all_metadata = []
        all_ids = []
        
        for doc_idx, doc in enumerate(documents):
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            
            # Chunk the document
            chunks = self.chunk_text(content)
            
            for chunk_idx, chunk in enumerate(chunks):
                chunk_id = f"doc_{doc_idx}_chunk_{chunk_idx}"
                chunk_metadata = {
                    **metadata,
                    'doc_id': doc_idx,
                    'chunk_id': chunk_idx,
                    'chunk_size': len(chunk)
                }
                
                all_chunks.append(chunk)
                all_metadata.append(chunk_metadata)
                all_ids.append(chunk_id)
        
        # Generate embeddings
        print("Generating embeddings...")
        embeddings = self.embedding_model.encode(all_chunks)
        
        # Add to ChromaDB
        self.collection.add(
            documents=all_chunks,
            embeddings=embeddings.tolist(),
            metadatas=all_metadata,
            ids=all_ids
        )
        
        print(f"Successfully added {len(all_chunks)} chunks to the knowledge base!")
    
    def retrieve_documents(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of relevant documents with metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results
        )
        
        retrieved_docs = []
        for i in range(len(results['documents'][0])):
            retrieved_docs.append({
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return retrieved_docs
    
    def generate_response(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """
        Generate response using Gemini LLM with retrieved context.
        
        Args:
            query: User query
            context_docs: Retrieved documents for context
            
        Returns:
            Generated response
        """
        # Prepare context
        context = "\n\n".join([doc['content'] for doc in context_docs])
        
        # Create prompt
        prompt = f"""You are a helpful AI assistant. Use the following context to answer the user's question. 
If the context doesn't contain enough information to answer the question, say so clearly.

Context:
{context}

Question: {query}

Answer:"""
        
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def ask(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Complete RAG pipeline: retrieve and generate.
        
        Args:
            query: User query
            n_results: Number of documents to retrieve
            
        Returns:
            Dictionary containing answer, sources, and metadata
        """
        print(f"Processing query: {query}")
        
        # Retrieve relevant documents
        retrieved_docs = self.retrieve_documents(query, n_results)
        
        # Generate response
        answer = self.generate_response(query, retrieved_docs)
        
        return {
            'answer': answer,
            'sources': retrieved_docs,
            'query': query,
            'n_sources': len(retrieved_docs)
        }
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the document collection."""
        count = self.collection.count()
        return {
            'total_chunks': count,
            'collection_name': self.collection_name
        }


def main():
    """
    Example usage of the RAG system.
    """
    # Initialize RAG system
    # Make sure to set your GEMINI_API_KEY environment variable
    try:
        rag = RAGSystem()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set your GEMINI_API_KEY environment variable or create a .env file with:")
        print("GEMINI_API_KEY=your_api_key_here")
        return
    
    # Sample documents
    sample_documents = [
        {
            'content': """
            Artificial Intelligence (AI) is a broad field of computer science concerned with building smart machines 
            capable of performing tasks that typically require human intelligence. AI systems can learn from data, 
            recognize patterns, make decisions, and solve problems. Machine Learning is a subset of AI that focuses 
            on the development of algorithms that can learn and improve from experience without being explicitly programmed.
            
            Deep Learning is a subset of Machine Learning that uses neural networks with multiple layers to model 
            and understand complex patterns in data. It has been particularly successful in areas like image recognition, 
            natural language processing, and speech recognition.
            """,
            'metadata': {'source': 'AI_overview', 'topic': 'artificial_intelligence'}
        },
        {
            'content': """
            Python is a high-level, interpreted programming language known for its simplicity and readability. 
            It was created by Guido van Rossum and first released in 1991. Python supports multiple programming 
            paradigms, including procedural, object-oriented, and functional programming.
            
            Python is widely used in various domains including web development, data science, artificial intelligence, 
            automation, and scientific computing. Its extensive standard library and rich ecosystem of third-party 
            packages make it a popular choice for both beginners and experienced developers.
            """,
            'metadata': {'source': 'Python_overview', 'topic': 'programming'}
        },
        {
            'content': """
            Natural Language Processing (NLP) is a subfield of artificial intelligence that focuses on the interaction 
            between computers and humans through natural language. The goal of NLP is to enable computers to understand, 
            interpret, and generate human language in a valuable way.
            
            Common NLP tasks include text classification, sentiment analysis, named entity recognition, machine translation, 
            text summarization, and question answering. Modern NLP relies heavily on machine learning techniques, 
            particularly deep learning models like transformers.
            """,
            'metadata': {'source': 'NLP_overview', 'topic': 'natural_language_processing'}
        }
    ]
    
    # Add documents to the RAG system
    rag.add_documents(sample_documents)
    
    # Get collection statistics
    stats = rag.get_collection_stats()
    print(f"\nCollection Statistics: {stats}")
    
    # Example queries
    queries = [
        "What is artificial intelligence?",
        "Tell me about Python programming language",
        "What are common NLP tasks?",
        "How does machine learning relate to AI?"
    ]
    
    print("\n" + "="*50)
    print("RAG SYSTEM DEMO")
    print("="*50)
    
    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        
        result = rag.ask(query)
        print(f"Answer: {result['answer']}")
        print(f"\nSources used: {result['n_sources']}")
        
        # Show source snippets
        for i, source in enumerate(result['sources'][:2]):  # Show top 2 sources
            print(f"Source {i+1} (distance: {source['distance']:.3f}): {source['content'][:100]}...")
        
        print("\n" + "-"*50)


if __name__ == "__main__":
    main() 