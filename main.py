from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import List
import logging
from pdf_processor import process_pdf_base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PDF Underline Extractor API",
    description="API to extract underlined words from PDF files",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PDFRequest(BaseModel):
    pdf_base64: str
    
    @field_validator('pdf_base64')
    @classmethod
    def validate_base64(cls, v):
        if not v or not v.strip():
            raise ValueError('PDF base64 content cannot be empty')
        return v.strip()

class UnderlineResponse(BaseModel):
    underlined_words: List[str]
    total_count: int
    message: str

@app.get("/")
async def root():
    return {
        "message": "PDF Underline Extractor API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/extract-underlines", response_model=UnderlineResponse)
async def extract_underlines(request: PDFRequest):
    """
    Extract underlined words from a PDF file provided as base64 string.
    
    Args:
        request: PDFRequest containing base64 encoded PDF
        
    Returns:
        UnderlineResponse: Contains list of underlined words and metadata
        
    Raises:
        HTTPException: If PDF processing fails
    """
    try:
        logger.info("Processing PDF for underlined words extraction")
        
        # Process the PDF and extract underlined words
        underlined_words = process_pdf_base64(request.pdf_base64)
        
        logger.info(f"Successfully extracted {len(underlined_words)} underlined words")
        
        return UnderlineResponse(
            underlined_words=underlined_words,
            total_count=len(underlined_words),
            message="Successfully extracted underlined words"
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)