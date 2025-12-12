"""
FastAPI application for contract evaluation chatbot.

Provides a streaming chat endpoint that accepts user messages,
extracts Google Docs URLs, and evaluates contracts.
"""

import os
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from streaming_assistant import StreamingContractAssistant


# Initialize FastAPI app
app = FastAPI(
    title="Contract Approval Assistant",
    description="AI-powered contract evaluation against approval matrix policies",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize assistant
assistant = StreamingContractAssistant(
    aws_region=os.environ.get("AWS_REGION", "us-west-2")
)


# Request/Response models
class ChatInput(BaseModel):
    """Chat input model."""
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Please evaluate this contract: https://docs.google.com/document/d/1rHt_qNNnOEdVTS5q4fCMmUxotQNceUNYLjBhs1kqMfE/edit"
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str


# Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


# Streaming chat endpoint
@app.post("/chat/stream")
async def chat_stream(request: ChatInput):
    """Stream chat responses for contract evaluation.

    The endpoint:
    1. Receives user message with Google Docs URL
    2. Extracts the URL from the message
    3. Evaluates the contract against approval matrix
    4. Streams back the evaluation progress and results

    Args:
        request: ChatInput with user message

    Returns:
        StreamingResponse with evaluation progress
    """
    try:
        messages = [{"role": "user", "content": request.message}]

        def generate_response():
            for chunk in assistant.stream_agent(messages):
                yield chunk

        return StreamingResponse(
            generate_response(),
            media_type="text/plain"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@app.post("/chat")
async def chat(request: ChatInput):
    """Non-streaming chat endpoint (for testing).

    Args:
        request: ChatInput with user message

    Returns:
        Complete response as JSON
    """
    try:
        messages = [{"role": "user", "content": request.message}]

        # Collect all chunks
        response_text = ""
        for chunk in assistant.stream_agent(messages):
            response_text += chunk

        return {"response": response_text}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


# Run with: uvicorn app:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
