import chromadb
import logging
from pathlib import Path

class ChromaService:
    """Handles all interactions with the ChromaDB vector database using persistent storage."""

    def __init__(self):
        """
        Initializes the ChromaDB client with persistent storage.
        No server required - data is stored locally.
        """
        try:
            data_path = Path("./chroma_data")
            data_path.mkdir(exist_ok=True)

            self.client = chromadb.PersistentClient(path=str(data_path))

            logging.info(f"Successfully initialized ChromaDB with persistent storage at: {data_path}")
        except Exception as e:
            logging.critical(f"Failed to initialize ChromaDB: {e}")
            raise

    def get_or_create_collection(self, name: str):
        """
        Retrieves an existing collection or creates a new one if it doesn't exist.

        Args:
            name (str): The name of the collection.

        Returns:
            chromadb.Collection: The collection object.
        """
        try:
            collection = self.client.get_or_create_collection(name=name)
            logging.info(f"Successfully retrieved or created collection: '{name}'")
            return collection
        except Exception as e:
            logging.error(f"Error getting or creating collection '{name}': {e}")
            raise

    def add_documents(self, collection, documents: list[str], metadatas: list[dict], ids: list[str]):
        """
        Adds documents and their metadata to the specified collection.

        Args:
            collection (chromadb.Collection): The collection to add documents to.
            documents (list[str]): The list of document text chunks.
            metadatas (list[dict]): A list of metadata dicts for each document.
            ids (list[str]): A list of unique IDs for each document.
        """
        try:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logging.info(f"Added {len(documents)} documents to '{collection.name}'.")
        except Exception as e:
            logging.error(f"Error adding documents to collection '{collection.name}': {e}")
            raise

    def query(self, collection, query_texts: list[str], n_results: int = 5):
        """
        Queries the collection to find documents similar to the query text.

        Args:
            collection (chromadb.Collection): The collection to query.
            query_texts (list[str]): The text(s) to search for.
            n_results (int): The number of results to return.

        Returns:
            dict: The query results from ChromaDB.
        """
        try:
            results = collection.query(
                query_texts=query_texts,
                n_results=n_results
            )
            logging.info(f"Successfully queried collection '{collection.name}'.")
            return results
        except Exception as e:
            logging.error(f"Error querying collection '{collection.name}': {e}")
            raise

    def list_collections(self):
        """
        Lists all collections in the database.

        Returns:
            list: List of collection names.
        """
        try:
            collections = self.client.list_collections()
            collection_names = [col.name for col in collections]
            logging.info(f"Found {len(collection_names)} collections")
            return collection_names
        except Exception as e:
            logging.error(f"Error listing collections: {e}")
            raise

    def delete_collection(self, name: str):
        """
        Deletes a collection from the database.

        Args:
            name (str): The name of the collection to delete.
        """
        try:
            self.client.delete_collection(name=name)
            logging.info(f"Successfully deleted collection: '{name}'")
        except Exception as e:
            logging.error(f"Error deleting collection '{name}': {e}")
            raise

chroma_service = ChromaService()