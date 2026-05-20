"""
Vector Database for RAG System
Manages document storage and retrieval using ChromaDB.
"""

import chromadb
from pathlib import Path
from typing import List


class CompanyKnowledgeBase:
    """Manages company guidelines in vector database for retrieval."""

    def __init__(self):
        """Initialize ChromaDB client and collection."""
        self.client = chromadb.PersistentClient(path="./chroma_data")

        try:
            self.collection = self.client.get_collection("company_guidelines")
            print("Loaded existing guidelines collection")
        except:
            self.collection = self.client.create_collection(
                name="company_guidelines",
                metadata={"description": "AURON company guidelines and policies"}
            )
            print("Created new guidelines collection")

    def chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """
        Split text into chunks for embedding.

        Args:
            text: Full text to split
            chunk_size: Approximate characters per chunk

        Returns:
            List of text chunks
        """
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line)
            if current_size + line_size > chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size

        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def load_guidelines(self, file_path: str = "company_guidelines.txt"):
        """
        Load and index company guidelines into vector database.

        Args:
            file_path: Path to guidelines file
        """
        guidelines_path = Path(file_path)

        if not guidelines_path.exists():
            print(f"Guidelines file not found: {file_path}")
            return

        with open(guidelines_path, "r") as f:
            content = f.read()

        chunks = self.chunk_text(content)
        print(f"Split guidelines into {len(chunks)} chunks")

        if self.collection.count() > 0:
            print("Guidelines already loaded, skipping...")
            return

        self.collection.add(
            documents=chunks,
            ids=[f"chunk_{i}" for i in range(len(chunks))],
            metadatas=[{"chunk_id": i, "source": "company_guidelines"} for i in range(len(chunks))]
        )

        print(f"Loaded {len(chunks)} chunks into vector database")

    def search_relevant_guidelines(self, query: str, n_results: int = 3) -> str:
        """
        Search for relevant guideline sections based on a query.

        Args:
            query: Search query (feedback text and category)
            n_results: Number of relevant chunks to retrieve

        Returns:
            Combined text of relevant guideline sections
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        if not results['documents'] or not results['documents'][0]:
            return "No specific guidelines found."

        relevant_sections = results['documents'][0]
        combined = "\n\n---\n\n".join(relevant_sections)

        print(f"Retrieved {len(relevant_sections)} relevant guideline sections")
        return combined


knowledge_base = CompanyKnowledgeBase()