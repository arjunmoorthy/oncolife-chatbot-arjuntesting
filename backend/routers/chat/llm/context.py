import os
import json
import docx
import numpy as np
from pypdf import PdfReader
from typing import List, Dict, Any

# Lazy-load sentence-transformers and faiss to avoid loading them on every import
sentence_transformers = None
faiss = None

def _import_embedding_libraries():
    global sentence_transformers, faiss
    if sentence_transformers is None:
        import sentence_transformers as st
        sentence_transformers = st
    if faiss is None:
        import faiss as f
        faiss = f

class ContextLoader:
    """
    Loads context from files and pre-computed vector stores.
    """
    def __init__(self, directory: str, model_name='all-MiniLM-L6-v2'):
        self.directory = directory
        self.model_name = model_name
        self.vector_store_path = os.path.join(self.directory, "ctcae_index.faiss")
        self.documents_path = os.path.join(self.directory, "ctcae_documents.json")
        self.model = None
        self.index = None
        self.documents = []
        self._load_vector_store()

    def _initialize_model(self):
        if self.model is None:
            _import_embedding_libraries()
            self.model = sentence_transformers.SentenceTransformer(self.model_name)

    def _load_vector_store(self):
        """Loads the pre-computed FAISS vector store from disk."""
        if os.path.exists(self.vector_store_path) and os.path.exists(self.documents_path):
            print("Loading existing FAISS index and documents.")
            _import_embedding_libraries()
            self.index = faiss.read_index(self.vector_store_path)
            with open(self.documents_path, 'r') as f:
                self.documents = json.load(f)
        else:
            print("Warning: Pre-built vector store not found. Symptom context will be disabled.")
            print(f"Please run `python backend/scripts/build_vector_store.py` to generate it.")
            self.index = None
            self.documents = []

    def retrieve_symptom_context_from_vector_store(self, symptoms: List[str], k: int = 5) -> str:
        """
        Retrieves the top-k relevant CTCAE criteria from the vector store based on symptoms.
        """
        if not self.index or not symptoms:
            return ""

        self._initialize_model()
        query = ", ".join(symptoms)
        query_embedding = self.model.encode([query])[0]
        
        # FAISS expects a 2D array for searching
        query_embedding_np = np.array([query_embedding], dtype='float32')

        distances, indices = self.index.search(query_embedding_np, k)
        
        relevant_docs = [self.documents[i] for i in indices[0]]
        
        if not relevant_docs:
            return ""

        formatted_context = "### Relevant CTCAE v5 Criteria (from knowledge base)\n"
        formatted_context += "\n---\n".join(relevant_docs)
        
        print("\n==================== CTCAE Context Retrieved ====================")
        print(formatted_context)
        print("=================================================================\n")

        return formatted_context

    def load_context(self, symptoms: List[str] = None) -> str:
        """
        Loads general documents and retrieves symptom-specific context using the vector store.
        """
        full_context = []
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

        # Add symptom-specific context if symptoms are provided
        if symptoms:
            symptom_context = self.retrieve_symptom_context_from_vector_store(symptoms)
            if symptom_context:
                full_context.insert(0, symptom_context) # Prepend for importance
        
        return "\n\n---\n\n".join(full_context)

    # Keep the existing loader methods (_load_docx, _load_pdf, _load_txt, _load_json, load_system_prompt)
    def _load_docx(self, file_path: str) -> str:
        """Loads text from a .docx file."""
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    def _load_pdf(self, file_path: str) -> str:
        """Loads text from a .pdf file."""
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    def _load_txt(self, file_path: str) -> str:
        """Loads text from a .txt file."""
        with open(file_path, 'r') as f:
            return f.read()

    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """Loads data from a .json file."""
        with open(file_path, 'r') as f:
            return json.load(f)

    def load_system_prompt(self) -> str:
        """
        Loads the system prompt from 'system_prompt.txt'.
        """
        system_prompt_path = os.path.join(self.directory, "system_prompt.txt")
        if os.path.exists(system_prompt_path):
            return self._load_txt(system_prompt_path)
        return ""