#!/usr/bin/env python3
"""
Enhanced RAG System Example with Gemini LLM

This script demonstrates how to use the RAG system with various document types
and provides an interactive interface for querying the knowledge base.
"""

import os
import sys
from pathlib import Path
from rag_gemini import RAGSystem
from document_processor import DocumentProcessor
from dotenv import load_dotenv

def create_sample_documents():
    """Create sample documents for demonstration."""
    
    # Create a sample directory structure
    sample_dir = Path("sample_documents")
    sample_dir.mkdir(exist_ok=True)
    
    # Sample text document
    with open(sample_dir / "ai_basics.txt", "w", encoding="utf-8") as f:
        f.write("""
Artificial Intelligence: A Comprehensive Overview

Artificial Intelligence (AI) represents one of the most transformative technologies of our time. 
It encompasses a broad range of techniques and approaches designed to enable machines to perform 
tasks that typically require human intelligence.

Key Areas of AI:

1. Machine Learning (ML)
Machine Learning is a subset of AI that focuses on the development of algorithms that can learn 
and improve from experience without being explicitly programmed. ML algorithms build mathematical 
models based on training data to make predictions or decisions.

Types of Machine Learning:
- Supervised Learning: Uses labeled data to train models
- Unsupervised Learning: Finds patterns in unlabeled data
- Reinforcement Learning: Learns through interaction with environment

2. Deep Learning
Deep Learning is a subset of machine learning that uses neural networks with multiple layers 
(hence "deep") to model and understand complex patterns in data. It has revolutionized fields 
like computer vision, natural language processing, and speech recognition.

3. Natural Language Processing (NLP)
NLP focuses on enabling computers to understand, interpret, and generate human language. 
Applications include machine translation, sentiment analysis, chatbots, and text summarization.

4. Computer Vision
Computer Vision enables machines to interpret and understand visual information from the world. 
Applications include image recognition, object detection, facial recognition, and autonomous vehicles.

Recent Developments:
- Large Language Models (LLMs) like GPT, BERT, and Gemini
- Transformer architecture revolutionizing NLP
- Generative AI for creating content
- AI Ethics and Responsible AI development
        """)
    
    # Sample JSON document
    with open(sample_dir / "ml_algorithms.json", "w", encoding="utf-8") as f:
        f.write("""
{
    "machine_learning_algorithms": [
        {
            "name": "Linear Regression",
            "type": "Supervised Learning",
            "description": "A statistical method used to model the relationship between a dependent variable and independent variables",
            "use_cases": ["Prediction", "Trend Analysis", "Risk Assessment"],
            "complexity": "Low"
        },
        {
            "name": "Random Forest",
            "type": "Supervised Learning", 
            "description": "An ensemble method that combines multiple decision trees to improve prediction accuracy",
            "use_cases": ["Classification", "Regression", "Feature Selection"],
            "complexity": "Medium"
        },
        {
            "name": "Neural Networks",
            "type": "Deep Learning",
            "description": "Networks of interconnected nodes that mimic the structure of biological neural networks",
            "use_cases": ["Image Recognition", "NLP", "Pattern Recognition"],
            "complexity": "High"
        },
        {
            "name": "K-Means Clustering",
            "type": "Unsupervised Learning",
            "description": "Algorithm that groups data points into k clusters based on similarity",
            "use_cases": ["Customer Segmentation", "Data Analysis", "Anomaly Detection"],
            "complexity": "Medium"
        }
    ],
    "evaluation_metrics": {
        "classification": ["Accuracy", "Precision", "Recall", "F1-Score"],
        "regression": ["MAE", "MSE", "RMSE", "R-squared"],
        "clustering": ["Silhouette Score", "Inertia", "Davies-Bouldin Index"]
    }
}
        """)
    
    print(f"Created sample documents in {sample_dir}")
    return sample_dir

def interactive_mode(rag_system):
    """Run the RAG system in interactive mode."""
    print("\n" + "="*60)
    print("🤖 RAG SYSTEM - INTERACTIVE MODE")
    print("="*60)
    print("Type your questions and get AI-powered answers!")
    print("Commands:")
    print("  - 'quit' or 'exit': Exit the program")
    print("  - 'stats': Show collection statistics")
    print("  - 'help': Show this help message")
    print("-" * 60)
    
    while True:
        try:
            query = input("\n💭 Your question: ").strip()
            
            if query.lower() in ['quit', 'exit']:
                print("👋 Goodbye!")
                break
            elif query.lower() == 'stats':
                stats = rag_system.get_collection_stats()
                print(f"📊 Collection Stats: {stats}")
                continue
            elif query.lower() == 'help':
                print("\n🔍 Ask questions about:")
                print("  - Artificial Intelligence and Machine Learning")
                print("  - Programming and Python")
                print("  - Any topic in the loaded documents")
                print("\n💡 Example questions:")
                print("  - What is machine learning?")
                print("  - Explain neural networks")
                print("  - What are the types of machine learning?")
                continue
            elif not query:
                continue
            
            print("\n🔍 Searching knowledge base...")
            result = rag_system.ask(query, n_results=3)
            
            print(f"\n🤖 **Answer:**")
            print(result['answer'])
            
            print(f"\n📚 **Sources used:** {result['n_sources']}")
            for i, source in enumerate(result['sources'][:3]):
                distance = source.get('distance', 0)
                source_name = source['metadata'].get('source', 'Unknown')
                print(f"  {i+1}. {source_name} (relevance: {1-distance:.2f})")
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main function demonstrating the RAG system."""
    print("🚀 RAG System with Gemini LLM - Enhanced Example")
    print("=" * 50)
    load_dotenv()
    
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY environment variable not found!")
        print("\n📋 Setup Instructions:")
        print("1. Get your Gemini API key from: https://makersuite.google.com/app/apikey")
        print("2. Create a .env file in this directory with:")
        print("   GEMINI_API_KEY=your_api_key_here")
        print("3. Or set it as an environment variable:")
        print("   export GEMINI_API_KEY=your_api_key_here")
        return
    
    try:
        # Initialize RAG system
        print("🔧 Initializing RAG system...")
        rag = RAGSystem()
        
        # Create sample documents
        sample_dir = create_sample_documents()
        
        # Process documents
        print("📄 Processing documents...")
        processor = DocumentProcessor()
        documents = processor.process_directory(str(sample_dir))
        
        if not documents:
            print("⚠️ No documents found. Creating sample documents...")
            # Add some hardcoded sample documents
            documents = [
                {
                    'content': """
                    Python is a high-level programming language known for its simplicity and readability.
                    It's widely used in data science, web development, automation, and artificial intelligence.
                    Python's extensive library ecosystem makes it perfect for rapid development and prototyping.
                    """,
                    'metadata': {'source': 'python_info', 'topic': 'programming'}
                }
            ]
        
        # Add documents to RAG system
        rag.add_documents(documents)
        
        # Show statistics
        stats = rag.get_collection_stats()
        print(f"✅ Knowledge base ready! {stats}")
        
        # Demo mode or interactive mode
        if len(sys.argv) > 1 and sys.argv[1] == "--demo":
            # Demo mode with predefined queries
            demo_queries = [
                "What is artificial intelligence?",
                "Explain different types of machine learning",
                "What are neural networks used for?",
                "Tell me about evaluation metrics for ML models"
            ]
            
            print("\n🎬 DEMO MODE - Running sample queries...")
            for query in demo_queries:
                print(f"\n❓ Query: {query}")
                print("-" * 40)
                result = rag.ask(query)
                print(f"🤖 Answer: {result['answer']}")
                print(f"📚 Sources: {result['n_sources']}")
        else:
            # Interactive mode
            interactive_mode(rag)
    
    except Exception as e:
        print(f"❌ Error initializing RAG system: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure all dependencies are installed: pip install -r requirements.txt")
        print("2. Check your internet connection (needed for embeddings)")
        print("3. Verify your Gemini API key is correct")

if __name__ == "__main__":
    main() 