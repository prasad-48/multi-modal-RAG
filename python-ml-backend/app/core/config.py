import os
import logging
from pathlib import Path
from dotenv import load_dotenv

def load_environment_variables():
    """
    Loads environment variables from a .env file located in the project root.

    The function navigates up from the current file's directory to find the
    project root and load the .env file.
    """
    current_file_path = Path(__file__).resolve()
    project_root = current_file_path.parent.parent.parent
    dotenv_path = project_root / ".env"

    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path)
        logging.info(f"Loaded environment variables from {dotenv_path}")
    else:
        load_dotenv()
        logging.info("Loaded environment variables from default location")

load_environment_variables()

# --- API Keys & Models ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    logging.error("GOOGLE_API_KEY not found in environment variables")
    raise ValueError("GOOGLE_API_KEY environment variable is required")

GENERATION_MODEL_NAME = "gemini-3.8-flash"
EMBEDDING_MODEL_NAME = "text-embedding-004"

# --- ChromaDB ---
CHROMA_DATA_PATH = os.getenv("CHROMA_DATA_PATH", "./chroma_data")
DEFAULT_COLLECTION_NAME = "rag-collection"

# --- Text Splitting ---
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# --- FastAPI ---
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = int(os.getenv("API_PORT", "8001"))

logging.info("Configuration loaded successfully")