# Multi-Modal RAG Chatbot

A full-stack, multi-modal Retrieval-Augmented Generation (RAG) application that lets users interact with PDF documents through a conversational chat interface. The application processes both text and images from uploaded PDFs to provide context-aware responses.

The project uses a **Next.js frontend** and an asynchronous **FastAPI backend**, with ChromaDB for persistent vector storage and Google Gemini for AI-powered response generation.

## Key Features

- **Multi-Modal PDF Processing:** Processes text and images extracted from uploaded PDF documents.
- **Chat with Documents:** Upload PDFs and ask questions about their content through an interactive chat interface.
- **AI-Powered Responses:** Uses Google Gemini to generate responses based on retrieved document context.
- **Asynchronous Backend:** Uses FastAPI to handle document-processing and API operations asynchronously where supported.
- **Vector Search:** Uses ChromaDB for persistent vector storage and document retrieval.
- **Modern User Interface:** Built with Next.js, React, TypeScript, Tailwind CSS, and shadcn/ui.
- **Full-Stack Architecture:** Separates the frontend and Python backend for easier development and maintenance.

## Technologies Used

### Frontend
- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- Axios

### Backend
- Python 3.12
- FastAPI
- Uvicorn

### AI and Document Processing
- Google Gemini (`gemini-3.8-flash`)
- PyMuPDF
- Pillow
- ChromaDB

## Project Structure

```text
multi-modal-RAG/
├── nextjs-app/
│   └── src/
├── python-ml-backend/
│   ├── app/
│   │   ├── core/
│   │   └── services/
│   ├── requirements.txt
│   └── chroma_data/        # Generated locally; not committed
├── .gitignore
└── Readme.md
```

## Prerequisites

Make sure you have the following installed:

- Python 3.12
- Node.js 18.17 or later
- npm
- Git
- A Google AI API key with access to the configured Gemini model

## Local Setup and Installation

The frontend and backend run separately. Follow the steps below to start the application locally.

### 1. Clone the Repository

```bash
git clone https://github.com/prasad-48/multi-modal-RAG.git
cd multi-modal-RAG
```

### 2. Configure Environment Variables

Create a `.env` file in the project root and add your Google AI API key:

```env
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY_HERE
```

Replace `YOUR_GOOGLE_API_KEY_HERE` with your actual API key from [Google AI Studio](https://aistudio.google.com/).

**Security:** Never commit your `.env` file or expose your API key in source code, screenshots, or public repositories.

### 3. Set Up the Python Backend

Open a terminal in the project root and navigate to the backend:

```powershell
cd python-ml-backend
python -m venv venv
```

Activate the virtual environment on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

If you use Command Prompt instead of PowerShell:

```bat
venv\Scripts\activate.bat
```

On macOS or Linux:

```bash
source venv/bin/activate
```

Install the backend dependencies:

```bash
python -m pip install -r requirements.txt
```

Start the backend server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

The backend should be accessible at:

- API: `http://localhost:8001`
- Interactive API documentation: `http://localhost:8001/docs`

Keep this terminal running.

### 4. Configure and Run the Next.js Frontend

Open a second terminal and navigate to the frontend directory from the project root:

```powershell
cd nextjs-app
```

Create a `.env.local` file inside `nextjs-app` containing:

```env
NEXT_PUBLIC_PYTHON_API_URL=http://localhost:8001
```

Install the frontend dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Keep this terminal running.

### 5. Open the Application

Open your browser and navigate to:

**http://localhost:3000**

You can now upload supported PDF documents and interact with their content through the chat interface.

## Configuration Notes

- Ensure the Gemini model configured in the backend is available to your Google AI API key.
- Keep the frontend API URL consistent with the backend host and port.
- The `chroma_data/` directory is generated locally by ChromaDB and should not be committed to Git.
- Environment files, virtual environments, dependency folders, and generated database files should remain excluded from version control.

## Development and Validation

To build the frontend for production:

```bash
cd nextjs-app
npm run build
```

To check Python syntax from the backend directory:

```bash
python -m compileall app
```

## Contributions and Attribution

This repository contains project setup and development changes made for this version. Contributions should accurately reflect the work performed.

If this project is based on or adapted from another repository, retain any required copyright notices, license terms, and attribution applicable to the original code.

## License

No license is declared by this README. Before distributing or reusing this project, verify the licensing terms and attribution requirements that apply to the original source code.
