"""
FAISS Vector Store for ContextMemory.

This module provides fast vector similarity search using FAISS.
Each conversation has its own index for isolation.
"""

import faiss
import numpy as np
from typing import List, Dict, Optional
import os
import json


class FAISSVectorStore:
    """
    A FAISS-backed vector store for fast similarity search.
    
    Attributes:
        dimension: The size of embedding vectors (1536 for OpenAI)
        index: The FAISS index
        id_map: Maps memory_id -> faiss_index
        reverse_map: Maps faiss_index -> memory_id
    """
    
    def __init__(self, dimension: int = 1536):
        """
        Initialize a new vector store.
        
        Args:
            dimension: Size of vectors (default 1536 for OpenAI embeddings)
        """
        self.dimension = dimension
        
        # IndexFlatIP = Inner Product (cosine similarity after normalization)
        self.index = faiss.IndexFlatIP(dimension)
        
        # Bidirectional mapping between memory IDs and FAISS indices
        self.id_map: Dict[int, int] = {}  # memory_id -> faiss_index
        self.reverse_map: Dict[int, int] = {}  # faiss_index -> memory_id
    
    def add(self, memory_id: int, embedding: List[float]) -> None:
        """
        Add a memory embedding to the index.
        
        Args:
            memory_id: The database ID of the memory
            embedding: The 1536-dimensional embedding vector
        """
        if memory_id in self.id_map:
            # Already exists, skip (use update method for changes)
            return
            
        # Convert to numpy array with correct shape
        vector = np.array([embedding], dtype=np.float32)
        
        # Normalize for cosine similarity
        # After normalization, inner product = cosine similarity
        faiss.normalize_L2(vector)
        
        # Get the index position before adding
        faiss_idx = self.index.ntotal
        
        # Add to FAISS
        self.index.add(vector)
        
        # Update mappings
        self.id_map[memory_id] = faiss_idx
        self.reverse_map[faiss_idx] = memory_id
    
    def search(self, query_embedding: List[float], k: int = 10) -> List[Dict]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: The query vector
            k: Number of results to return
            
        Returns:
            List of dicts with memory_id and score
        """
        if self.index.ntotal == 0:
            return []
        
        # Prepare query vector
        vector = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(vector)
        
        # Don't request more than we have
        k = min(k, self.index.ntotal)
        
        # Search
        scores, indices = self.index.search(vector, k)
        
        # Map back to memory IDs
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and idx in self.reverse_map:
                results.append({
                    "memory_id": self.reverse_map[idx],
                    "score": float(score)
                })
        
        return results
    
    def remove(self, memory_id: int) -> None:
        """
        Remove a memory from tracking (soft delete).
        
        Note: FAISS doesn't support true deletion. The vector remains
        in the index but won't be returned in results.
        """
        if memory_id in self.id_map:
            faiss_idx = self.id_map[memory_id]
            if faiss_idx in self.reverse_map:
                del self.reverse_map[faiss_idx]
            del self.id_map[memory_id]
    
    def save(self, path: str) -> None:
        """
        Save index and mappings to disk.
        
        Args:
            path: Base path (without extension)
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        faiss.write_index(self.index, f"{path}.faiss")
        with open(f"{path}.map.json", "w") as f:
            json.dump({
                "id_map": {str(k): v for k, v in self.id_map.items()},
                "reverse_map": {str(k): v for k, v in self.reverse_map.items()}
            }, f)
    
    def load(self, path: str) -> bool:
        """
        Load index and mappings from disk.
        
        Args:
            path: Base path (without extension)
            
        Returns:
            True if loaded successfully, False if files don't exist
        """
        if not os.path.exists(f"{path}.faiss"):
            return False
        
        try:
            self.index = faiss.read_index(f"{path}.faiss")
            with open(f"{path}.map.json", "r") as f:
                data = json.load(f)
                self.id_map = {int(k): v for k, v in data["id_map"].items()}
                self.reverse_map = {int(k): v for k, v in data["reverse_map"].items()}
            return True
        except Exception:
            return False
    
    @property
    def count(self) -> int:
        """Number of vectors in the index."""
        return len(self.id_map)


# Global cache of vector stores (one per conversation)
_vector_stores: Dict[int, FAISSVectorStore] = {}


def get_index_path(conversation_id: int) -> str:
    """Get the file path for a conversation's index."""
    index_dir = os.path.expanduser("~/.contextmemory/indexes")
    os.makedirs(index_dir, exist_ok=True)
    return os.path.join(index_dir, f"conv_{conversation_id}")


def get_vector_store(conversation_id: int) -> FAISSVectorStore:
    """
    Get or create a vector store for a conversation.
    
    This is the main entry point for using FAISS in ContextMemory.
    
    Args:
        conversation_id: The conversation to get the store for
        
    Returns:
        FAISSVectorStore instance
    """
    global _vector_stores
    
    if conversation_id not in _vector_stores:
        store = FAISSVectorStore()
        path = get_index_path(conversation_id)
        store.load(path)  # Load if exists, otherwise empty
        _vector_stores[conversation_id] = store
    
    return _vector_stores[conversation_id]


def save_vector_store(conversation_id: int) -> None:
    """Save a conversation's vector store to disk."""
    if conversation_id in _vector_stores:
        path = get_index_path(conversation_id)
        _vector_stores[conversation_id].save(path)


def rebuild_index_from_db(db, conversation_id: int) -> FAISSVectorStore:
    """
    Rebuild FAISS index from database.
    
    Use this when:
    - Index file is missing or corrupted
    - After bulk operations
    - For initial migration
    
    Args:
        db: SQLAlchemy session
        conversation_id: Conversation to rebuild
        
    Returns:
        New FAISSVectorStore with all memories indexed
    """
    from contextmemory.db.models.memory import Memory
    
    store = FAISSVectorStore()
    
    # Fetch all memories with embeddings
    memories = db.query(Memory).filter(
        Memory.conversation_id == conversation_id,
        Memory.is_active == True,
        Memory.embedding.isnot(None)
    ).all()
    
    # Add each to the index
    for mem in memories:
        if mem.embedding:
            store.add(mem.id, mem.embedding)
    
    # Cache and save
    _vector_stores[conversation_id] = store
    save_vector_store(conversation_id)
    
    return store


def reset_vector_stores() -> None:
    """Clear all cached vector stores. Useful for testing."""
    global _vector_stores
    _vector_stores = {}
