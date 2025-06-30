import os
import json
from typing import List, Dict, Any
from pathlib import Path
import PyPDF2
import pandas as pd

class DocumentProcessor:
    """
    Utility class to process different types of documents for RAG system.
    """
    
    @staticmethod
    def process_text_file(file_path: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """Process a text file."""
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
            
            return {
                'content': content,
                'metadata': {
                    'source': os.path.basename(file_path),
                    'file_type': 'text',
                    'file_path': file_path,
                    'size': len(content)
                }
            }
        except Exception as e:
            print(f"Error processing text file {file_path}: {e}")
            return None
    
    @staticmethod
    def process_pdf_file(file_path: str) -> Dict[str, Any]:
        """Process a PDF file."""
        try:
            content = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
            
            return {
                'content': content,
                'metadata': {
                    'source': os.path.basename(file_path),
                    'file_type': 'pdf',
                    'file_path': file_path,
                    'num_pages': len(pdf_reader.pages),
                    'size': len(content)
                }
            }
        except Exception as e:
            print(f"Error processing PDF file {file_path}: {e}")
            return None
    
    @staticmethod
    def process_csv_file(file_path: str, text_columns: List[str] = None) -> Dict[str, Any]:
        """Process a CSV file by combining specified text columns."""
        try:
            df = pd.read_csv(file_path)
            
            if text_columns is None:
                # Auto-detect text columns (non-numeric columns)
                text_columns = df.select_dtypes(include=['object']).columns.tolist()
            
            # Combine text from specified columns
            content_parts = []
            for idx, row in df.iterrows():
                row_text = " | ".join([f"{col}: {str(row[col])}" for col in text_columns if pd.notna(row[col])])
                if row_text.strip():
                    content_parts.append(f"Row {idx + 1}: {row_text}")
            
            content = "\n".join(content_parts)
            
            return {
                'content': content,
                'metadata': {
                    'source': os.path.basename(file_path),
                    'file_type': 'csv',
                    'file_path': file_path,
                    'num_rows': len(df),
                    'columns': df.columns.tolist(),
                    'text_columns': text_columns,
                    'size': len(content)
                }
            }
        except Exception as e:
            print(f"Error processing CSV file {file_path}: {e}")
            return None
    
    @staticmethod
    def process_json_file(file_path: str, text_fields: List[str] = None) -> Dict[str, Any]:
        """Process a JSON file by extracting text from specified fields."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            def extract_text_from_json(obj, prefix=""):
                """Recursively extract text from JSON object."""
                text_parts = []
                
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_prefix = f"{prefix}.{key}" if prefix else key
                        if text_fields is None or current_prefix in text_fields or key in text_fields:
                            if isinstance(value, (str, int, float)):
                                text_parts.append(f"{key}: {value}")
                            elif isinstance(value, (dict, list)):
                                text_parts.extend(extract_text_from_json(value, current_prefix))
                        else:
                            text_parts.extend(extract_text_from_json(value, current_prefix))
                
                elif isinstance(obj, list):
                    for idx, item in enumerate(obj):
                        text_parts.extend(extract_text_from_json(item, f"{prefix}[{idx}]"))
                
                return text_parts
            
            text_parts = extract_text_from_json(data)
            content = "\n".join(text_parts)
            
            return {
                'content': content,
                'metadata': {
                    'source': os.path.basename(file_path),
                    'file_type': 'json',
                    'file_path': file_path,
                    'text_fields': text_fields,
                    'size': len(content)
                }
            }
        except Exception as e:
            print(f"Error processing JSON file {file_path}: {e}")
            return None
    
    @classmethod
    def process_directory(cls, directory_path: str, file_extensions: List[str] = None) -> List[Dict[str, Any]]:
        """
        Process all supported files in a directory.
        
        Args:
            directory_path: Path to the directory
            file_extensions: List of file extensions to process (e.g., ['.txt', '.pdf'])
                           If None, processes all supported extensions
        
        Returns:
            List of processed documents
        """
        if file_extensions is None:
            file_extensions = ['.txt', '.pdf', '.csv', '.json', '.md']
        
        documents = []
        directory = Path(directory_path)
        
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in file_extensions:
                print(f"Processing: {file_path}")
                
                if file_path.suffix.lower() in ['.txt', '.md']:
                    doc = cls.process_text_file(str(file_path))
                elif file_path.suffix.lower() == '.pdf':
                    doc = cls.process_pdf_file(str(file_path))
                elif file_path.suffix.lower() == '.csv':
                    doc = cls.process_csv_file(str(file_path))
                elif file_path.suffix.lower() == '.json':
                    doc = cls.process_json_file(str(file_path))
                else:
                    continue
                
                if doc:
                    documents.append(doc)
        
        return documents
    
    @classmethod
    def process_single_file(cls, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        Process a single file based on its extension.
        
        Args:
            file_path: Path to the file
            **kwargs: Additional arguments for specific processors
        
        Returns:
            Processed document or None if processing failed
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return None
        
        extension = file_path.suffix.lower()
        
        if extension in ['.txt', '.md']:
            return cls.process_text_file(str(file_path), **kwargs)
        elif extension == '.pdf':
            return cls.process_pdf_file(str(file_path))
        elif extension == '.csv':
            return cls.process_csv_file(str(file_path), **kwargs)
        elif extension == '.json':
            return cls.process_json_file(str(file_path), **kwargs)
        else:
            print(f"Unsupported file type: {extension}")
            return None


# Example usage
if __name__ == "__main__":
    processor = DocumentProcessor()
    
    # Example: Process a single text file
    # doc = processor.process_single_file("example.txt")
    # if doc:
    #     print(f"Processed document: {doc['metadata']['source']}")
    #     print(f"Content length: {len(doc['content'])} characters")
    
    # Example: Process all files in a directory
    # documents = processor.process_directory("./documents", ['.txt', '.pdf', '.md'])
    # print(f"Processed {len(documents)} documents")
    
    print("DocumentProcessor is ready to use!")
    print("Supported file types: .txt, .md, .pdf, .csv, .json") 