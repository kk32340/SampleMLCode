"""
Simple RAG (Retrieval Augmented Generation) Example using Gemini 1.5 Flash Latest
A minimal implementation for learning purposes.
"""

import os
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
from huggingface_hub import snapshot_download

# Load environment variables
load_dotenv()

class SimpleRAG:
    def __init__(self):
        """Initialize the Simple RAG system"""
        # Configure Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        # Initialize embedding model for document similarity
        print("Loading embedding model...")
        # Download model
        model_path = snapshot_download("sentence-transformers/all-MiniLM-L6-v2")
        model = SentenceTransformer(model_path)
        self.embedding_model = model  #SentenceTransformer('all-MiniLM-L6-v2')
        # Storage for documents and their embeddings
        self.documents = []
        self.embeddings = []

        
    def add_document(self, text, source=""):
        """Add a document to the knowledge base"""
        # Split document into chunks (simple approach)
        chunks = self.chunk_text(text, chunk_size=500, overlap=50)
        
        for i, chunk in enumerate(chunks):
            doc_info = {
                'content': chunk,
                'source': source,
                'chunk_id': i
            }
            
            # Generate embedding for the chunk
            embedding = self.embedding_model.encode([chunk])[0]
            
            self.documents.append(doc_info)
            self.embeddings.append(embedding)
        
        print(f"Added {len(chunks)} chunks from {source}")
    
    def chunk_text(self, text, chunk_size=500, overlap=50):
        """Simple text chunking by character count"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > start + chunk_size // 2:
                    chunk = text[start:start + break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
            
            if start >= len(text):
                break
                
        return [chunk for chunk in chunks if len(chunk.strip()) > 20]
    
    def retrieve_relevant_docs(self, query, n_results=3):
        """Retrieve most relevant documents for a query"""
        if not self.documents:
            return []
        
        # Generate embedding for query
        query_embedding = self.embedding_model.encode([query])[0]
        
        # Calculate similarities
        similarities = cosine_similarity(
            [query_embedding], 
            self.embeddings
        )[0]
        
        # Get top results
        top_indices = np.argsort(similarities)[::-1][:n_results]
        
        results = []
        for idx in top_indices:
            results.append({
                'content': self.documents[idx]['content'],
                'source': self.documents[idx]['source'],
                'similarity': similarities[idx]
            })
        
        return results
    
    def generate_answer(self, query, context_docs):
        """Generate answer using Gemini with retrieved context"""
        if not context_docs:
            context = "No relevant information found."
        else:
            context = "\n\n".join([
                f"Source: {doc['source']}\nContent: {doc['content']}"
                for doc in context_docs
            ])
        
        prompt = f"""
Based on the following context information, please answer the question.
If the context doesn't contain relevant information, say so.

Context:
{context}

Question: {query}

Answer:
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating response: {e}"
    
    def ask(self, query, n_results=3):
        """Main method to ask a question and get an answer"""
        print(f"\n🔍 Query: {query}")
        
        # Retrieve relevant documents
        relevant_docs = self.retrieve_relevant_docs(query, n_results)
        
        # Generate answer
        answer = self.generate_answer(query, relevant_docs)
        
        print(f"🤖 Answer: {answer}")
        
        if relevant_docs:
            print(f"\n📚 Sources used:")
            for i, doc in enumerate(relevant_docs, 1):
                print(f"  {i}. {doc['source']} (similarity: {doc['similarity']:.3f})")
        
        return {
            'answer': answer,
            'sources': relevant_docs,
            'n_sources': len(relevant_docs)
        }

def main():
    """Example usage of Simple RAG"""
    print("🚀 Simple RAG with Gemini 1.5 Flash Latest")
    print("=" * 50)
    
    # Initialize RAG system
    try:
        rag = SimpleRAG()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\n📋 Setup Instructions:")
        print("1. Get your Gemini API key from: https://makersuite.google.com/app/apikey")
        print("2. Create a .env file with: GEMINI_API_KEY=your_api_key_here")
        return
    
    # Load sample documents
    print("\n📄 Loading sample documents...")
    
    # Load from existing sample files
    try:
        with open('sample_documents/ai_basics.txt', 'r', encoding='utf-8') as f:
            ai_content = f.read()
            rag.add_document(ai_content, "AI Basics")
    except FileNotFoundError:
        print("Sample document not found, using hardcoded content...")
        ai_content = """
        Artificial Intelligence (AI) is the simulation of human intelligence in machines.
        Machine Learning is a subset of AI that enables computers to learn from data.
        Deep Learning uses neural networks with multiple layers.
        Natural Language Processing (NLP) helps computers understand human language.
        """
        rag.add_document(ai_content, "AI Basics")
    
    # Add more sample content
    python_content = """
    Python is a high-level programming language known for its simplicity.
    It's widely used in data science, web development, and AI.
    Popular Python libraries include NumPy, Pandas, and TensorFlow.
    Python supports object-oriented and functional programming paradigms.
    """
    rag.add_document(python_content, "Python Basics")
    
    # Example queries
    queries = [
        "What is artificial intelligence?",
        "Tell me about machine learning",
        "What is Python used for?",
        "Explain deep learning"
    ]
    
    print("\n" + "="*50)
    print("EXAMPLE QUERIES")
    print("="*50)
    
    for query in queries:
        rag.ask(query)
        print("-" * 50)
    
    # Interactive mode
    print("\n💬 Interactive mode (type 'quit' to exit):")
    while True:
        try:
            user_query = input("\nYour question: ").strip()
            
            if user_query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if user_query:
                rag.ask(user_query)
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()