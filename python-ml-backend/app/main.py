import logging
import uuid
import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict

from app.services.rag_service import rag_service
from app.services.chroma_service import chroma_service


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize FastAPI app
app = FastAPI(title="RAG Multi-Modal API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store processing status
processing_status: Dict[str, dict] = {}

class ChatRequest(BaseModel):
    """Request model for the /chat endpoint."""
    query: str
    collection_name: str


class ProcessingStatus(BaseModel):
    """Response model for processing status."""
    status: str
    message: str
    progress: int  # 0-100
    collection_name: str = None


async def process_document_async(file_bytes: bytes, filename: str, collection_name: str, task_id: str):
    """Process document asynchronously with status updates."""
    try:
        processing_status[task_id] = {
            "status": "processing",
            "message": "Starting document processing...",
            "progress": 0,
            "collection_name": collection_name
        }

        # Update progress at each step
        processing_status[task_id].update({
            "message": "Extracting text from document...",
            "progress": 25
        })

        # Run the processing in a thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            rag_service.process_document,
            file_bytes,
            filename,
            collection_name
        )

        processing_status[task_id].update({
            "status": "completed",
            "message": f"Document '{filename}' processed successfully!",
            "progress": 100
        })

    except Exception as e:
        processing_status[task_id].update({
            "status": "failed",
            "message": f"Error processing document: {str(e)}",
            "progress": 0
        })
        logging.error(f"Error in async processing: {e}")


@app.get("/")
def read_root():
    """A simple health check endpoint."""
    return {"status": "ok", "message": "Welcome to the RAG Multi-Modal API"}


@app.post("/api/upload")
async def upload_document(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...)
):
    """
    Handles file uploads and starts async processing.
    Returns immediately with a task ID for status tracking.
    """
    try:
        logging.info(f"Received file: {file.filename}")

        # Check file size
        max_size = 50 * 1024 * 1024  # Limit to 50MB
        file_bytes = await file.read()

        if len(file_bytes) > max_size:
            raise HTTPException(
                status_code=413,
                detail="File too large. Maximum size is 50MB."
            )

        logging.info(f"File size: {len(file_bytes)} bytes")

        # Generate identifiers
        task_id = str(uuid.uuid4())
        collection_name = f"doc_{uuid.uuid4().hex[:8]}"

        background_tasks.add_task(
            process_document_async,
            file_bytes,
            file.filename,
            collection_name,
            task_id
        )

        return {
            "message": f"File '{file.filename}' upload started.",
            "task_id": task_id,
            "collection_name": collection_name
        }

    except Exception as e:
        logging.error(f"Error during file upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status/{task_id}")
async def get_processing_status(task_id: str):
    """Check the processing status of a document."""
    if task_id not in processing_status:
        raise HTTPException(status_code=404, detail="Task not found")

    return processing_status[task_id]


@app.post("/api/chat")
async def chat_with_document(request: ChatRequest):
    """
    Receives a user query and returns a RAG-based response.
    """
    if not request.query or not request.collection_name:
        raise HTTPException(status_code=400, detail="Query and collection_name are required.")

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            rag_service.generate_response,
            request.query,
            request.collection_name
        )

        return {"response": response}

    except Exception as e:
        logging.error(f"Error during chat processing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/collections")
async def list_collections():
    """List all available collections."""
    try:
        collections = chroma_service.list_collections()
        return {"collections": collections}
    except Exception as e:
        logging.error(f"Error listing collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/collections/{collection_name}")
async def delete_collection(collection_name: str):
    """Delete a collection."""
    try:
        chroma_service.delete_collection(collection_name)
        return {"message": f"Collection '{collection_name}' deleted successfully"}
    except Exception as e:
        logging.error(f"Error deleting collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))