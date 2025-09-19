# PDF Underline Extractor API

A FastAPI application that extracts underlined words from PDF files.

## Features

- Accept PDF files as base64 encoded strings
- Extract text and identify underlined words
- Return array of underlined words
- RESTful API with automatic documentation

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### POST /extract-underlines

Extract underlined words from a PDF file.

**Request Body:**
```json
{
  "pdf_base64": "base64_encoded_pdf_content"
}
```

**Response:**
```json
{
  "underlined_words": ["word1", "word2", "word3"],
  "total_count": 3,
  "message": "Successfully extracted underlined words"
}
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc