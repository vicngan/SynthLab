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
    
    def summarize_results(self, query: str, results: List[Dict], max_tokens: int = 500) -> str:
        """
        Use Claude to summarize search results and answer the query.
        
        Args:
            query: User's question
            results: Search results from self.search()
            max_tokens: Max length of summary
            
        Returns:
            AI-generated summary
        """

        import os

        try:
            import anthropic
        except ImportError:
            return "Install anthropic: pip install anthropic"
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return "ANTHROPIC_API_KEY not set. Add it to your .env file."
        
        #combine top results into context
        context = "\n\n --- \n\n".join([
            f"Source: {r['filename']}\n{r['text'][:1500]}"
            for r in results [:3]
        ])

        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model = "claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            messages = [
                {
                    "role": "user",
                    "content": f"""Based on the following research excerpts, answer this question: {query}
Research context:
{context}

Provide a concise, accurate summary that directly addresses the question. Cite which source supports each point."""

                }
            ]
        )
    
        return message.content[0].text

    def save_index(self, path: str) -> None:
        """
        Save FAISS index and document metadata to disk for persistence.

        Args:
            path: Directory path to save index files
        """
        import pickle
        from pathlib import Path

        save_dir = Path(path)
        save_dir.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        if self.index is not None:
            faiss.write_index(self.index, str(save_dir / "index.faiss"))

        # Save document metadata and embeddings
        data = {
            'documents': self.documents,
            'embeddings': self.embeddings
        }
        with open(save_dir / "documents.pkl", "wb") as f:
            pickle.dump(data, f)

        print(f"Index saved to {save_dir}")

    def load_index(self, path: str) -> None:
        """
        Load FAISS index and document metadata from disk.

        Args:
            path: Directory path containing saved index files
        """
        import pickle
        from pathlib import Path

        load_dir = Path(path)

        # Load FAISS index
        index_path = load_dir / "index.faiss"
        if index_path.exists():
            self.index = faiss.read_index(str(index_path))
        else:
            raise FileNotFoundError(f"FAISS index not found at {index_path}")

        # Load document metadata and embeddings
        docs_path = load_dir / "documents.pkl"
        if docs_path.exists():
            with open(docs_path, "rb") as f:
                data = pickle.load(f)
                self.documents = data.get('documents', [])
                self.embeddings = data.get('embeddings')
        else:
            raise FileNotFoundError(f"Documents file not found at {docs_path}")

        print(f"Index loaded from {load_dir}: {len(self.documents)} documents")