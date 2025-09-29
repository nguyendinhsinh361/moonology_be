"""
Vector store for message retrieval using Qdrant.
"""

from typing import Any, Dict, List, Optional, Union

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import settings
from app.core.constants import DEFAULT_SIMILARITY_THRESHOLD
from app.core.init import get_cached_model
from app.models.embedding import get_embeddings


def message_to_document(
    message: BaseMessage, metadata: Optional[Dict[str, Any]] = None
) -> Document:
    """
    Convert a message to a document for storage in vector store.

    Args:
        message (BaseMessage): The message to convert
        metadata (Dict[str, Any], optional): Additional metadata

    Returns:
        Document: A document suitable for vector store
    """
    # Default metadata
    meta = {
        "type": message.type,
        "session_id": metadata.get("session_id", "") if metadata else "",
        "timestamp": metadata.get("timestamp", 0) if metadata else 0,
    }

    # Debug metadata

    # Add additional metadata if provided
    if metadata:
        meta.update(metadata)

    return Document(page_content=message.content, metadata=meta)


def document_to_message(doc: Document) -> BaseMessage:
    """
    Convert a document from vector store back to a message.

    Args:
        doc (Document): The document to convert

    Returns:
        BaseMessage: The message
    """
    content = doc.page_content
    msg_type = doc.metadata.get("type", "human")

    if msg_type == "human":
        return HumanMessage(content=content)
    elif msg_type == "ai":
        return AIMessage(content=content)
    else:
        # Default to human message if type is unknown
        return HumanMessage(content=content)


class MessageVectorStore:
    """
    Vector store for chat messages using Qdrant.
    """

    def __init__(self, embeddings: Optional[Embeddings] = None, namespace: str = "chat_messages"):
        """
        Initialize the vector store.

        Args:
            embeddings (Embeddings, optional): Embedding model to use
            namespace (str): Namespace in Qdrant (used as collection name suffix)
        """
        self.embeddings = embeddings or get_embeddings()
        self.namespace = namespace
        self.collection_name = f"{settings.QDRANT_COLLECTION_NAME}"

        # Initialize Qdrant
        self._init_qdrant()

        # Get embedding dimension from model
        sample_embedding = self.embeddings.embed_query("Sample text")
        self.dimension = len(sample_embedding)

        # Create the vector store
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
        )

    def _init_qdrant(self):
        """Initialize Qdrant client and create collection if it doesn't exist."""
        # Initialize Qdrant client
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            https=True,  # Use HTTPS for secure connection
        )

        # Check if collection exists, if not create it
        collections = self.client.get_collections().collections
        collection_names = [collection.name for collection in collections]

        if self.collection_name not in collection_names:
            # Create a new collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=384,  # default dimension for all-MiniLM-L6-v2
                    distance=models.Distance.COSINE,
                ),
            )

    def add_message(
        self, message: BaseMessage, session_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a message to the vector store.

        Args:
            message (BaseMessage): The message to add
            session_id (str): The session ID
            metadata (Dict[str, Any], optional): Additional metadata

        Returns:
            str: The document ID
        """
        # Create metadata dict
        meta = metadata or {}
        meta["session_id"] = session_id

        # Convert message to document
        doc = message_to_document(message, meta)

        # Add to vector store
        ids = self.vector_store.add_documents([doc])

        return ids[0] if ids else ""

    def search_similar_messages(
        self,
        query: str,
        session_id: Optional[str] = None,
        k: int = 10,
        filter_type: Optional[str] = None,
        score_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    ) -> List[BaseMessage]:
        """
        Search for messages similar to the query.

        Args:
            query (str): The query text
            session_id (str, optional): If provided, filter by session ID
            k (int): Number of results to return
            filter_type (str, optional): If provided, filter by message type (e.g., "human", "ai")
            score_threshold (float): Minimum similarity score (0.0 to 1.0) to include in results

        Returns:
            List[BaseMessage]: List of similar messages
        """
        # Build filter if session_id is provided
        filter_dict = None

        if session_id or filter_type:
            must_conditions = []

            if session_id:
                must_conditions.append(
                    {"key": "metadata.session_id", "match": {"value": session_id}}
                )

            if filter_type:
                must_conditions.append({"key": "metadata.type", "match": {"value": filter_type}})

            filter_dict = {"must": must_conditions}

        # Debug information
        print(f"Vector search query: '{query}'")
        print(f"Filter: {filter_dict}")
        print(f"Score threshold: {score_threshold}")

        try:
            # Search for similar documents with scores
            docs_with_scores = self.vector_store.similarity_search_with_score(
                query=query, k=k, filter=filter_dict
            )

            # Filter by similarity score (Qdrant uses cosine similarity where 1.0 is perfect match)
            # Convert to percentage for easier understanding
            filtered_docs = [
                (doc, score) for doc, score in docs_with_scores if score >= score_threshold
            ]

            # Debug information
            print(f"Found {len(filtered_docs)} documents with score >= {score_threshold}")
            for doc, score in filtered_docs:
                print(f"Score: {score:.2f} - Content: {doc.page_content[:50]}...")

            # Convert documents back to messages
            return [document_to_message(doc) for doc, _ in filtered_docs]
        except Exception as e:
            print(f"Error in vector search: {str(e)}")
            return []


def get_vector_store(collection_name: str = "chat_messages") -> MessageVectorStore:
    """
    Get an instance of the message vector store.
    Uses cached instance if available for better performance.

    Args:
        collection_name (str): Name of the collection/namespace in Qdrant

    Returns:
        MessageVectorStore: An instance of the message vector store
    """
    # Try to get from cache if requesting the default collection
    if collection_name == "chat_messages":
        cached_store = get_cached_model("vector_store")
        if cached_store is not None:
            return cached_store

    # Create a new instance if not in cache or requesting a different collection
    return MessageVectorStore(namespace=collection_name)
