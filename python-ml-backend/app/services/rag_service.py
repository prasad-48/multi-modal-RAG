import logging
import io
import time
from typing import List, Dict, Any, Tuple
import fitz
from PIL import Image
import docx
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core import config
from app.services.chroma_service import chroma_service

IMAGE_CACHE: Dict[str, List[Image.Image]] = {}

class RAGService:
    """Handles Multi-Modal RAG operations with performance optimizations."""

    def __init__(self):
        """Initialize the RAG service with Google AI configuration."""
        genai.configure(api_key=config.GOOGLE_API_KEY)
        model_name = getattr(config, 'GENERATION_MODEL_NAME', 'gemini-1.5-flash')
        self.generation_model = genai.GenerativeModel(model_name)

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        logging.info("Multi-Modal RAG Service initialized successfully")

    def process_document(self, file_bytes: bytes, filename: str, collection_name: str):
        """
        Extracts text and images from a document, stores text embeddings, and caches images.
        """
        start_time = time.time()
        logging.info(f"Starting document processing: {filename} ({len(file_bytes)} bytes)")

        try:
            file_extension = filename.lower().split('.')[-1]
            text_content = ""
            images = []

            if file_extension == 'pdf':
                logging.info("Step 1/4: Extracting text and images from PDF...")
                text_content, images = self._extract_text_and_images_from_pdf(file_bytes)
            elif file_extension == 'docx':
                logging.info("Step 1/4: Extracting text from DOCX...")
                text_content = self._extract_text_from_docx(file_bytes)
            elif file_extension == 'txt':
                logging.info("Step 1/4: Reading text file...")
                text_content = file_bytes.decode('utf-8')
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")

            if not text_content.strip() and not images:
                raise ValueError("Document is empty or content could not be extracted.")

            # Store the extracted images in our cache
            if images:
                logging.info("Step 2/4: Caching extracted images...")
                # Optimize images
                optimized_images = [self._optimize_image(img) for img in images]
                IMAGE_CACHE[collection_name] = optimized_images
                logging.info(f"Cached {len(optimized_images)} images for collection '{collection_name}'")

            # Process and store text chunks
            if text_content.strip():
                logging.info("Step 3/4: Splitting text into chunks...")
                chunks = self.text_splitter.split_text(text_content)
                logging.info(f"Split document into {len(chunks)} text chunks")

                if chunks:
                    logging.info("Step 4/4: Storing chunks in vector database...")
                    collection = chroma_service.get_or_create_collection(collection_name)
                    self._store_chunks_in_batches(collection, chunks, filename, collection_name)

            total_time = time.time() - start_time
            logging.info(
                f"Document processing completed in {total_time:.2f}s - Text chunks: {len(chunks) if 'chunks' in locals() else 0}, Images: {len(images)}")

        except Exception as e:
            logging.error(f"Error processing document {filename}: {e}")
            raise

    def _extract_text_and_images_from_pdf(self, file_bytes: bytes) -> Tuple[str, List[Image.Image]]:
        """Extracts both text and images from a PDF file using PyMuPDF."""
        text = ""
        images = []
        pdf_document = None

        try:
            pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
            total_pages = len(pdf_document)
            logging.info(f"Processing PDF with {total_pages} pages")

            for page_num, page in enumerate(pdf_document):
                try:
                    # Extract text
                    page_text = page.get_text()
                    text += page_text + "\n"

                    # Extract images
                    for img_info in page.get_images(full=True):
                        try:
                            xref = img_info[0]
                            base_image = pdf_document.extract_image(xref)
                            image_bytes = base_image["image"]
                            pil_image = Image.open(io.BytesIO(image_bytes))

                            # Image validation
                            if pil_image.size[0] > 50 and pil_image.size[1] > 50:
                                images.append(pil_image)

                        except Exception as e:
                            logging.warning(f"Failed to extract image from page {page_num + 1}: {e}")

                except Exception as e:
                    logging.warning(f"Failed to process page {page_num + 1}: {e}")

        except Exception as e:
            logging.error(f"Failed to open PDF document: {e}")
            raise
        finally:
            if pdf_document:
                pdf_document.close()

        logging.info(f"Extracted {len(text)} characters of text and {len(images)} images")
        return text, images

    def _extract_text_from_docx(self, file_bytes: bytes) -> str:
        """Extract text from DOCX file."""
        try:
            doc_file = io.BytesIO(file_bytes)
            doc = docx.Document(doc_file)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            logging.error(f"Error extracting text from DOCX: {e}")
            raise

    def _optimize_image(self, image: Image.Image, max_size: Tuple[int, int] = (800, 600)) -> Image.Image:
        """Optimize image size for better performance."""
        try:
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)

            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')

            return image
        except Exception as e:
            logging.warning(f"Failed to optimize image: {e}")
            return image

    def _store_chunks_in_batches(self, collection, chunks: List[str], filename: str, collection_name: str):
        """Store chunks in ChromaDB using batches for better performance."""
        batch_size = 100
        total_chunks = len(chunks)

        for i in range(0, total_chunks, batch_size):
            batch_end = min(i + batch_size, total_chunks)
            batch_chunks = chunks[i:batch_end]

            logging.info(
                f"Processing batch {i // batch_size + 1}/{(total_chunks - 1) // batch_size + 1} ({len(batch_chunks)} chunks)")

            # Prepare batch data
            documents = batch_chunks
            metadatas = [
                {
                    "filename": filename,
                    "chunk_index": i + j,
                    "total_chunks": total_chunks,
                    "batch_id": i // batch_size
                }
                for j in range(len(batch_chunks))
            ]
            ids = [f"{collection_name}_{i + j}" for j in range(len(batch_chunks))]
            chroma_service.add_documents(collection, documents, metadatas, ids)

    def generate_response(self, query: str, collection_name: str) -> str:
        """
        Generates a multi-modal response using text from RAG and images from cache.
        """
        start_time = time.time()
        logging.info(f"Generating multi-modal response for query: '{query[:100]}...'")

        try:
            # Retrieve relevant text chunks
            collection = chroma_service.get_or_create_collection(collection_name)
            results = chroma_service.query(
                collection=collection,
                query_texts=[query],
                n_results=5
            )

            # Extract text context
            text_context = ""
            if results and results.get('documents') and results['documents'][0]:
                relevant_chunks = results['documents'][0]
                text_context = "\n\n---\n\n".join(relevant_chunks)

                max_context_length = 4000
                if len(text_context) > max_context_length:
                    text_context = text_context[:max_context_length] + "..."

            # Retrieve cached images
            images_context = IMAGE_CACHE.get(collection_name, [])

            # Build the prompt for the Gemini model
            prompt_parts = [
                f"Question: {query}\n\n",
                "Please answer the following question based ONLY on the provided context.",
                "If the information is not available in the text or images, clearly state that you cannot find the answer in the document.\n",
                "--- TEXT CONTEXT ---",
                text_context if text_context else "No relevant text was found in the document.",
                "--- END TEXT CONTEXT ---\n"
            ]

            # Add images to the prompt if they exist
            if images_context:
                logging.info(f"Attaching {len(images_context)} images to the prompt")
                prompt_parts.append(
                    f"\nAdditionally, {len(images_context)} images from the document are provided for context:")
                prompt_parts.extend(images_context)

            prompt_parts.append("\nProvide a clear, concise answer based on the available context.")

            # Generate the final response
            response = self.generation_model.generate_content(prompt_parts)

            generation_time = time.time() - start_time
            logging.info(f"Response generated in {generation_time:.2f} seconds")

            if response.text:
                return response.text
            else:
                return "I'm sorry, I couldn't generate a response. Please try rephrasing your question."

        except Exception as e:
            logging.exception("Error generating response")
            return "I encountered an error while generating the response. Please try again."

    def clear_collection_cache(self, collection_name: str):
        """Clear cached images for a specific collection."""
        if collection_name in IMAGE_CACHE:
            del IMAGE_CACHE[collection_name]
            logging.info(f"Cleared image cache for collection '{collection_name}'")

    def clear_all_cache(self):
        """Clear all cached images."""
        IMAGE_CACHE.clear()
        logging.info("Cleared all image cache")

    def get_cache_info(self) -> Dict[str, int]:
        """Get information about cached images."""
        return {
            collection_name: len(images)
            for collection_name, images in IMAGE_CACHE.items()
        }

    def extract_text_from_file(self, file_bytes: bytes, filename: str) -> str:
        """
        Extract text content from various file formats.
        """
        try:
            file_extension = filename.lower().split('.')[-1]

            if file_extension == 'pdf':
                text, _ = self._extract_text_and_images_from_pdf(file_bytes)
                return text
            elif file_extension == 'docx':
                return self._extract_text_from_docx(file_bytes)
            elif file_extension == 'txt':
                return file_bytes.decode('utf-8')
            else:
                return file_bytes.decode('utf-8')

        except Exception as e:
            logging.error(f"Error extracting text from {filename}: {e}")
            raise Exception(f"Failed to extract text from {filename}: {str(e)}")

rag_service = RAGService()
