"""
Optimized Context Loader for Cloud Deployment

This version pre-loads models and caches data to work better on cloud platforms.
"""

import os
import json
import docx
import numpy as np
from pypdf import PdfReader
from typing import List, Dict, Any
import threading
import time

# Global cache for models and data
_model_cache = {}
_index_cache = {}
_documents_cache = {}
_initialized = False
_init_lock = threading.Lock()

def _import_embedding_libraries():
    """Lazy import to avoid loading on every request."""
    global sentence_transformers, faiss
    if 'sentence_transformers' not in _model_cache:
        import sentence_transformers as st
        _model_cache['sentence_transformers'] = st
    if 'faiss' not in _model_cache:
        import faiss as f
        _model_cache['faiss'] = f

class OptimizedContextLoader:
    """
    Optimized context loader that pre-loads everything at startup.
    """
    def __init__(self, directory: str, model_name='all-MiniLM-L6-v2'):
        self.directory = directory
        self.model_name = model_name
        self.vector_store_path = os.path.join(self.directory, "ctcae_index.faiss")
        self.documents_path = os.path.join(self.directory, "ctcae_documents.json")
        
        # Initialize everything at startup
        self._initialize_all()
    
    def _initialize_all(self):
        """Initialize all models and data at startup."""
        global _initialized
        
        with _init_lock:
            if _initialized:
                return
                
            print("🚀 Initializing optimized context loader...")
            start_time = time.time()
            
            try:
                # Load embedding model
                _import_embedding_libraries()
                st = _model_cache['sentence_transformers']
                _model_cache['model'] = st.SentenceTransformer(self.model_name)
                print(f"✅ Loaded embedding model in {time.time() - start_time:.2f}s")
                
                # Load FAISS index
                if os.path.exists(self.vector_store_path) and os.path.exists(self.documents_path):
                    f = _model_cache['faiss']
                    _index_cache['index'] = f.read_index(self.vector_store_path)
                    with open(self.documents_path, 'r') as file:
                        _documents_cache['documents'] = json.load(file)
                    print(f"✅ Loaded FAISS index in {time.time() - start_time:.2f}s")
                else:
                    print("⚠️ FAISS index not found, using fallback mode")
                    _index_cache['index'] = None
                    _documents_cache['documents'] = []
                
                _initialized = True
                print(f"🎉 Context loader ready in {time.time() - start_time:.2f}s")
                
            except Exception as e:
                print(f"❌ Error initializing: {e}")
                # Fallback to basic mode
                _index_cache['index'] = None
                _documents_cache['documents'] = []
                _initialized = True

    def retrieve_symptom_context_from_vector_store(self, symptoms: List[str], k: int = 5) -> str:
        """
        Fast symptom context retrieval using pre-loaded models.
        """
        if not _index_cache.get('index') or not symptoms:
            return ""

        try:
            model = _model_cache.get('model')
            if not model:
                return ""
                
            query = ", ".join(symptoms)
            query_embedding = model.encode([query])[0]
            query_embedding_np = np.array([query_embedding], dtype='float32')

            f = _model_cache['faiss']
            distances, indices = _index_cache['index'].search(query_embedding_np, k)
            
            relevant_docs = [_documents_cache['documents'][i] for i in indices[0]]
            
            if not relevant_docs:
                return ""

            formatted_context = "### Relevant CTCAE v5 Criteria (from knowledge base)\n"
            formatted_context += "\n---\n".join(relevant_docs)
            
            return formatted_context
            
        except Exception as e:
            print(f"⚠️ Error in vector search: {e}")
            return ""

    def load_context(self, symptoms: List[str] = None) -> str:
        """
        Fast context loading with pre-loaded data.
        """
        full_context = []
        
        # Load static documents (cached)
        for filename in os.listdir(self.directory):
            if filename.endswith((".faiss", ".json", "system_prompt.txt")):
                continue
            
            file_path = os.path.join(self.directory, filename)
            content = ""
            
            if filename.endswith(".pdf"):
                content = self._load_pdf(file_path)
            elif filename.endswith(".docx"):
                content = self._load_docx(file_path)
            elif filename.endswith(".txt"):
                content = self._load_txt(file_path)
            
            if content:
                full_context.append(content)

        # Add symptom-specific context
        if symptoms:
            symptom_context = self.retrieve_symptom_context_from_vector_store(symptoms)
            if symptom_context:
                full_context.insert(0, symptom_context)
        
        return "\n\n---\n\n".join(full_context)

    def _load_docx(self, file_path: str) -> str:
        """Loads text from a .docx file."""
        try:
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            print(f"⚠️ Error loading DOCX: {e}")
            return ""

    def _load_pdf(self, file_path: str) -> str:
        """Loads text from a .pdf file."""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e:
            print(f"⚠️ Error loading PDF: {e}")
            return ""

    def _load_txt(self, file_path: str) -> str:
        """Loads text from a .txt file."""
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"⚠️ Error loading TXT: {e}")
            return ""

    def load_system_prompt(self) -> str:
        """Loads the system prompt."""
        try:
            prompt_path = os.path.join(self.directory, "oncolifebot_instructions.txt")
            with open(prompt_path, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"⚠️ Error loading system prompt: {e}")
            return "" 