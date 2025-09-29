"""
Embedding models for vectorizing text.
"""

from typing import List

from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer

# Import the cache
from app.core.constants import DEFAULT_EMBEDDING_MODEL
from app.core.init import get_cached_model


class SentenceTransformerEmbeddings(Embeddings):
    """
    Wrapper for sentence_transformers models to use in LangChain.
    """

    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL):
        """
        Initialize with a sentence_transformers model.

        Args:
            model_name (str): Name of the sentence_transformers model to use
        """
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of texts.

        Args:
            texts (List[str]): List of texts to embed

        Returns:
            List[List[float]]: List of embeddings
        """
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single text.

        Args:
            text (str): Text to embed

        Returns:
            List[float]: Embedding for the text
        """
        embedding = self.model.encode(text)
        return embedding.tolist()


def get_embeddings(model_name: str = DEFAULT_EMBEDDING_MODEL) -> Embeddings:
    """
    Get an instance of SentenceTransformerEmbeddings.
    Uses cached instance if available to avoid reloading the model.

    Args:
        model_name (str): Name of the sentence_transformers model to use

    Returns:
        Embeddings: An instance of SentenceTransformerEmbeddings
    """
    # Try to get from cache first
    cached_embeddings = get_cached_model("embeddings")
    if cached_embeddings is not None:
        return cached_embeddings

    # If not in cache, create a new instance
    return SentenceTransformerEmbeddings(model_name=model_name)
