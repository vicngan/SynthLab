import os
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
from dotenv import load_dotenv
load_dotenv()

try: 
    from PyPDF2 import PdfReader
    from sentence_transformers import SentenceTransformer
    import faiss
    LITERATURE_AVAILABLE = True
except ImportError:
    LITERATURE_AVAILABLE = False

class LiteratureSearch:
    """
    A class to perform literature search on synthetic data using semantic similarity.
    Upload a PDF of research papers and find relevant sections based on input queries.
    """

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):

        """
        Initializes the LiteratureSearch with a PDF file and a sentence transformer model.
        
        Args:
            pdf_path (str): Path to the PDF file containing research papers.
            model_name (str): Name of the pre-trained sentence transformer model to use.
        """

        if not LITERATURE_AVAILABLE:
            raise ImportError("Required libraries for LiteratureSearch are not installed.")
        
        print(f"Loading PDF and initializing model : {model_name}...")
    
        self.model = SentenceTransformer(model_name)
        self.embeddings = None
        self.documents = [] #list of document texts
        self.text_chunks = []
        self.index = None
        print("Initialization complete. Model loaded and PDF processed!")

    def extract_text_from_pdf(self, pdf_path: str) -> List[str]:
        """
        Extracts text from each page of the PDF.
        
        Args:
            pdf_path (str): Path to the PDF file.

        Returns:
            List[str]: List of text strings, one per page.
        """

        reader = PdfReader(pdf_path)
        filename = Path(pdf_path).name

        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and len(text.strip()) > 50: #ignore very short pages
                pages.append({
                    'filename': filename,
                    'page_number': i + 1,
                    'text': text.strip()        
                })

        print(f"Extracted text from {len(pages)} pages in {filename}.")
        return pages
    
    def add_pdf(self, pdf_path: str) -> int:
        """
        Adds another PDF file to the existing literature search index.
        
        Args:
            pdf_path (str): Path to the PDF file.

        Returns:
            int: Number of new pages added.
        """

        new_pages = self.extract_text_from_pdf(pdf_path)
        self.documents.extend(new_pages)
        self._process_text_chunks(new_pages)
        self._rebuild_index()
        print(f"Added {len(new_pages)} pages from {Path(pdf_path).name} to the index.") 

        return len(new_pages)
    
    def add_pdf_bytes(self, pdf_bytes: bytes, filename: str = "uploaded.pdf") -> int:
        """
        Adds a PDF file from bytes to the existing literature search index.
        
        Args:
            pdf_bytes (bytes): PDF file content in bytes.
            filename (str): Name to assign to the uploaded PDF.
        Returns:
            int: Number of new pages added.
        """

        import io
        reader= PdfReader(io.BytesIO(pdf_bytes))

        new_pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and len(text.strip()) > 50: #ignore very short pages
                new_pages.append({
                    'filename': filename,
                    'page_number': i + 1,
                    'text': text.strip()        
                })
        
        self.documents.extend(new_pages)
        self._rebuild_index()
        print(f"Added {len(new_pages)} pages from {filename} to the index.")
        return len(new_pages)
    
    def _rebuild_index(self):
        """
        Rebuilds the FAISS index with current text chunks.
        """

        if not self.documents:
            return
        
        text = [doc['text'] for doc in self.documents]
        self.embeddings = self.model.encode(text, show_progress_bar=True)

        #build FAISS index
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(self.embeddings.astype('float32'))
        print(f"FAISS index rebuilt with {self.index.ntotal} documents.")

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Searches for the most relevant document sections based on the input query.
        
        Args:
            query (str): The search query.
            top_k (int): Number of top results to return.
        Returns:
            List[Dict]: List of top_k relevant document sections with metadata.
        """

        if not self.documents or self.index is None:
            print("No documents in the index. Please add PDFs first.")
            return []
        
        #encode the query
        query_embedding = self.model.encode([query])

        #search in the index
        distances, indices = self.index.search(query_embedding.astype('float32'), top_k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc['score'] = float(1/(1 + distances[0][i]))  #convert distance to similarity score
                doc['text_snippet'] = doc['text'][:500] + ("..." if len(doc['text']) > 500 else "")
                results.append(doc)
            
        return results
    
    def get_stats(self) -> Dict:
        """
        Returns statistics about the loaded documents.
        
        Returns:
            Dict: Statistics including number of documents and pages.
        """
        if not self.documents:
            return {
                'num_documents': 0,
                'num_pages': 0,
                'files': []
            }
        
        files = list(set([doc['filename'] for doc in self.documents]))
        return {
            'num_documents': len(files),
            'num_pages': len(self.documents),
            'files': files
        }
    
    def save_index_to_s3(self, s3_handler, s3_prefix: str) -> None:
        """
        Save FAISS index and document metadata to an S3 bucket.

        Args:
            s3_handler: An instance of the S3Handler class.
            s3_prefix: The key prefix (folder) in S3 to save to.
        """
        import pickle
        import io

        # Save FAISS index
        if self.index is not None:
            # Serialize index to bytes
            index_bytes = faiss.serialize_index(self.index)
            s3_handler.write_file_content(f"{s3_prefix}/index.faiss", index_bytes, 'application/octet-stream')

        # Save document metadata and embeddings
        data = {
            'documents': self.documents,
            'embeddings': self.embeddings
        }
        # Pickle data to an in-memory byte stream
        with io.BytesIO() as bio:
            pickle.dump(data, bio)
            bio.seek(0)
            s3_handler.write_file_content(f"{s3_prefix}/documents.pkl", bio.read(), 'application/octet-stream')

        print(f"Index saved to S3 at prefix {s3_prefix}")

    def load_index_from_s3(self, s3_handler, s3_prefix: str) -> None:
        """
        Load FAISS index and document metadata from an S3 bucket.

        Args:
            s3_handler: An instance of the S3Handler class.
            s3_prefix: The key prefix (folder) in S3 to load from.
        """
        import pickle

        # Load FAISS index
        index_key = f"{s3_prefix}/index.faiss"
        index_obj = s3_handler.s3_client.get_object(Bucket=s3_handler.bucket_name, Key=index_key)
        index_bytes = index_obj['Body'].read()
        self.index = faiss.deserialize_index(index_bytes)

        # Load document metadata and embeddings
        docs_key = f"{s3_prefix}/documents.pkl"
        docs_obj = s3_handler.s3_client.get_object(Bucket=s3_handler.bucket_name, Key=docs_key)
        data = pickle.loads(docs_obj['Body'].read())
        self.documents = data.get('documents', [])
        self.embeddings = data.get('embeddings')

        print(f"Index loaded from S3 prefix {s3_prefix}: {len(self.documents)} documents")