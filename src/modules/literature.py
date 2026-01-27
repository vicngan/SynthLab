import os
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
import pickle
import anthropic
from datetime import datetime
import json
try: 
    from PyPDF2 import PdfReader
    LITERATURE_AVAILABLE = True
except ImportError:
    LITERATURE_AVAILABLE = False

class LiteratureSearch:
    """
    A class to perform literature search on synthetic data using semantic similarity.
    Upload a PDF of research papers and find relevant sections based on input queries.
    """

    def __init__(self):
        """
        Initializes the LiteratureSearch with the Anthropic Claude API.
        
        Args:
            None
        """
        if not LITERATURE_AVAILABLE:
            raise ImportError("PyPDF2 is not installed. Please run: pip install PyPDF2")
        
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set.")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model_name = "claude-3-haiku-20240307" # Fast and capable
        self.documents = [] # List of dicts: {'filename': str, 'page_number': int, 'text': str}
        self.search_history = []
        print("LiteratureSearch initialized with Anthropic Claude API.")

    def __getstate__(self):
        """
        Prepare the object's state for pickling. Excludes the non-serializable client.
        """
        state = self.__dict__.copy()
        # The 'client' attribute contains thread locks and is not serializable.
        # It will be re-initialized upon loading.
        del state['client']
        return state

    def __setstate__(self, state):
        """
        Restore the object's state after unpickling.
        """
        self.__dict__.update(state)
        # The client is not part of the pickled state and must be re-initialized.
        # We set it to None here; `load_session` is responsible for creating a new client.
        self.client = None

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
        print(f"Added {len(new_pages)} pages from {filename} to the context.")
        return len(new_pages)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Searches for the most relevant document sections based on the input query.
        
        Args:
            query (str): The search query.
            top_k (int): Number of top results to return (used in prompt).
        Returns:
            Dict: A dictionary containing a summary and a list of source results.
        """
        if not self.documents:
            return {"summary": "No documents have been uploaded. Please upload PDFs first.", "results": []}

        # Add to search history before performing the search
        self.search_history.append({
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "top_k": top_k
        })

        # Construct the context for Claude
        context_str = "<documents>\n"
        for i, doc in enumerate(self.documents):
            context_str += f"<document index=\"{i}\">\n"
            context_str += f"  <source>{doc['filename']}, page {doc['page_number']}</source>\n"
            context_str += f"  <content>\n{doc['text']}\n</content>\n"
            context_str += "</document>\n"
        context_str += "</documents>"

        # Construct the prompt
        prompt = f"""
You are a research assistant. Based *only* on the information in the provided documents, answer the following question: "{query}"

1.  First, provide a concise, synthesized summary that directly answers the question.
2.  After the summary, identify the {top_k} most relevant source documents you used. For each source, return its index, filename, and page number.
3.  For each cited source, also provide a "score" from 0.0 to 1.0 indicating its relevance to the query, and include the full text of that source page.

Respond in the following JSON format. Do not include any text outside of the JSON block.

{{
  "summary": "Your synthesized answer here.",
  "results": [
    {{
      "index": <document_index_int>,
      "filename": "source_filename.pdf",
      "page_number": <page_number_int>,
      "score": <relevance_score_float>,
      "text": "The full text content of the cited document page..."
    }}
  ]
}}
"""
        try:
            message = self.client.messages.create(model=self.model_name, max_tokens=4096, temperature=0.1, system=context_str, messages=[{"role": "user", "content": prompt}]).content[0].text
            json_start = message.find('{')
            json_end = message.rfind('}') + 1
            if json_start == -1 or json_end == 0: raise ValueError("Claude did not return a valid JSON object.")
            json_str = message[json_start:json_end]
            response_data = json.loads(json_str)
            for result in response_data.get("results", []):
                doc_index = result.get("index")
                if doc_index is not None and 0 <= doc_index < len(self.documents): result["text"] = self.documents[doc_index]["text"]
            return response_data
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return {"summary": f"An error occurred while contacting the AI model: {e}", "results": []}
    
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
    
    def save_session(self, path: Path):
        """
        Saves the current literature session (the object itself) to a file.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)
        print(f"Literature session saved to {path}")

    @staticmethod
    def load_session(path: Path) -> 'LiteratureSearch':
        """
        Loads a literature session from a file.
        """
        if not path.exists():
            raise FileNotFoundError(f"Session file not found: {path}")
        with open(path, "rb") as f:
            session = pickle.load(f)
        print(f"Literature session loaded from {path}")
        # Re-initialize the non-serializable client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key: raise ValueError("ANTHROPIC_API_KEY not set.")
        session.client = anthropic.Anthropic(api_key=api_key)
        return session