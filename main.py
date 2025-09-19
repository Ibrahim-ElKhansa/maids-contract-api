from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import List, Optional
import logging
from pdf_processor import process_pdf_base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PDF Analysis API",
    description="API to extract underlined words, AED 3500 count, and signature analysis from PDF files",
    version="2.0.0"
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

class AnalysisResponse(BaseModel):
    status: str
    hour: int
    day: int
    week: int
    month: int
    aed_3500_count: int
    left_stamp: int
    right_signature: int
    error_message: Optional[str] = None

@app.get("/info")
async def info():
    return {
        "message": "PDF Analysis API",
        "version": "2.0.0",
        "docs": "/docs",
        "features": [
            "Underlined word counting (hour, day, week, month) on page 2",
            "AED 3500 occurrence counting throughout PDF",
            "Signature box content analysis on last page"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/", response_model=AnalysisResponse)
async def analyze_pdf(request: PDFRequest):
    """
    Extract underlined words, AED 3500 count, and signature analysis from a PDF file.
    
    Args:
        request: PDFRequest containing base64 encoded PDF
        
    Returns:
        AnalysisResponse: Contains all analysis results including status
        
    Raises:
        HTTPException: If PDF processing fails
    """
    try:
        logger.info("Processing PDF for complete analysis")
        
        # Process the PDF and extract all analysis data
        result = process_pdf_base64(request.pdf_base64)
        
        logger.info(f"Successfully completed analysis with status: {result['status']}")
        
        return AnalysisResponse(**result)
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)