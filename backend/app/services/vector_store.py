"""Vector store interface and ChromaDB persistent storage wrapper.

Specification Section 3 & Section 8.
Encapsulates vector storage and similarity search using ChromaDB so it can be swapped
or mocked easily. Uses sentence-transformers locally or default Chroma embedding function.
"""

import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.app.config import settings


class ChromaVectorStore:
    """Persistent ChromaDB vector store wrapper."""

    def __init__(self, persist_directory: Optional[str] = None):
        path = persist_directory or settings.CHROMA_DIR
        os.makedirs(path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=path)
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="network_kb",
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(
        self,
        document_id: str,
        category_slug: str,
        source_type: str,
        filename: str,
        chunks: List[str]
    ) -> int:
        """Indexes text chunks into the ChromaDB vector collection.

        Args:
            document_id: Unique document ID from MongoDB.
            category_slug: Associated reference category slug.
            source_type: UPLOAD or CHAT.
            filename: Original file name or chat title.
            chunks: List of text chunk strings.

        Returns:
            Number of chunks indexed.
        """
        if not chunks:
            return 0

        # First remove any existing vectors for this document_id (idempotent re-indexing)
        self.delete_document(document_id)

        ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": document_id,
                "category_slug": category_slug,
                "source_type": source_type,
                "filename": filename,
                "chunk_index": i
            }
            for i in range(len(chunks))
        ]

        self.collection.add(
            ids=ids,
            documents=chunks,
            metadatas=metadatas
        )
        return len(chunks)

    def delete_document(self, document_id: str) -> None:
        """Deletes all vector chunks associated with a document ID."""
        try:
            self.collection.delete(
                where={"document_id": document_id}
            )
        except Exception:
            pass

    def search(
        self,
        query: str,
        top_k: int = 6,
        category_slug: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Performs vector similarity search in the knowledge base.

        Args:
            query: User search query or rewritten user context.
            top_k: Number of relevant chunks to retrieve.
            category_slug: Optional filter by reference category.

        Returns:
            List of dicts containing text, metadata, and similarity score.
        """
        if not query or not query.strip():
            return []

        where_clause = {"category_slug": category_slug} if category_slug else None

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_clause
        )

        hits = []
        if results and results.get("documents") and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results.get("distances", [[]])[0]

            for doc, meta, dist in zip(docs, metas, distances):
                # Cosine distance to similarity conversion: score = 1 - distance
                similarity = 1.0 - dist if dist is not None else 0.5
                hits.append({
                    "text": doc,
                    "metadata": meta,
                    "score": similarity
                })

        return hits


# Singleton instance reference
_vector_store_instance: Optional[ChromaVectorStore] = None


def get_vector_store() -> ChromaVectorStore:
    """Returns global vector store singleton instance."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = ChromaVectorStore()
    return _vector_store_instance
