# CampusSaarthi-AI

### Your AI-Powered Campus Knowledge Assistant

CampusSaarthi AI is an AI-powered university information assistant designed to help students find answers to common campus-related questions, including examination procedures, fee structures, registration guidelines, and academic resources.

The project aims to make university information easier to access through a conversational interface powered by Retrieval-Augmented Generation (RAG).

## Problem Statement

University information is often distributed across notices, PDFs, academic documents, and other resources. Students may struggle to locate accurate information quickly.

CampusSaarthi AI aims to simplify this process by providing a unified interface for searching campus information.

## Proposed Solution

- **Conversational Interface:** Ask campus-related questions in natural language.
- **Document-Based Retrieval:** Retrieve relevant information from a curated document collection.
- **Source Attribution:** Provide document references to help users verify answers.
- **Responsible AI:** Avoid unsupported claims when relevant evidence is unavailable.
- **Extensible Architecture:** Support adding verified university documents over time.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | Next.js, React, TypeScript |
| Styling | Tailwind CSS |
| Backend | Python, FastAPI |
| Document Processing | PyMuPDF |
| Embeddings | Sentence Transformers |
| Vector Search | FAISS |
| AI Architecture | Retrieval-Augmented Generation (RAG) |

*The final model and configuration are subject to implementation and testing.*

## Project Architecture

1. Ingest campus documents.
2. Extract and split document text into chunks.
3. Generate embeddings for semantic search.
4. Retrieve relevant passages for a student query.
5. Generate a response grounded in retrieved evidence.
6. Return source references or indicate insufficient evidence.

## Current Development Status

**Status: MVP in progress**

The repository contains the initial frontend and backend project structure, document-processing and retrieval components, test files, and illustrative demo documents.

Features and integrations are still being developed and validated. The production build and end-to-end workflow have not yet been fully verified.

## Getting Started

### Prerequisites

- Node.js and npm
- Python 3.11 or a compatible Python version
- Git

### Clone the repository

```bash
git clone https://github.com/DevanshAIBuilder/CollegeSaarthi-AI.git
cd CollegeSaarthi-AI
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

Open a separate terminal:

```bash
cd backend
python -m venv .venv
```

Activate the environment on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Check `backend/app/main.py` and the project configuration for the correct application entry point before starting the API.

## Responsible AI

CampusSaarthi AI is designed to prioritize evidence-backed responses, source transparency, and clear communication of uncertainty. Official campus information should be verified against authorized and up-to-date documents.

## Future Improvements

- Complete and validate the end-to-end RAG pipeline.
- Integrate and evaluate a compatible open-weight language model.
- Improve source citations and unsupported-query handling.
- Add document upload and indexing management.
- Complete automated testing and deployment.

## Hacktoberfest Hack Day 2026

**Team Name:** Nexus Coders  
**Participation:** Solo participant  
**Track:** Education

---

*Built as an educational project to explore open-source AI, document retrieval, and responsible question answering.*
