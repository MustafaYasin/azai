

from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from rag.generation import Generator
from rag.retrieval import Retriever

from frontend.settings import settings


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    conversation_history: list[ChatMessage] = Field(default_factory=list)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)


class ChatResponse(BaseModel):
    message: str = Field(..., description="Generated response")
    sources: list[dict[str, Any]] = Field(default_factory=list)


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(default=5, ge=1, le=20)


class SearchResponse(BaseModel):
    results: list[dict[str, Any]] = Field(..., description="Search results")
    total_found: int = Field(..., description="Total number of results found")


# Create FastAPI app
app = FastAPI(
    title="Aynzam API",
    description="AI-powered document search and chat API",
    version="1.0.0"
)

# Add CORS middleware for Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Use existing Generator class
        generator = Generator(api_key=settings.openai_key)

        # Generate response
        response = generator.generate_answer(
            query=request.message,
            k=3,
            temperature=request.temperature
        )

        # Get sources using existing Retriever
        retriever = Retriever(api_key=settings.openai_key)
        relevant_chunks = retriever.find_relevant_chunks(request.message, k=3)

        # Format sources for frontend
        sources = []
        for chunk in relevant_chunks:
            sources.append({
                "title": chunk.chunk_title,
                "content": chunk.chunk_content[:200] + "..." if len(chunk.chunk_content) > 200 else chunk.chunk_content,
                "page_number": chunk.page_number + 1 if chunk.page_number is not None else None,
                "metadata": chunk.meta
            })

        return ChatResponse(message=response, sources=sources)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {e!s}")


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response using existing streaming generator.
    """
    try:
        generator = Generator(api_key=settings.openai_key)

        def generate_stream():
            try:
                stream = generator.generate_streaming_answer(
                    query=request.message,
                    k=3,
                    temperature=request.temperature
                )

                for chunk in stream:
                    if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, 'content') and delta.content:
                            yield f"data: {delta.content}\n\n"

                yield "data: [DONE]\n\n"

            except Exception as e:
                yield f"data: Error: {e!s}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error streaming response: {e!s}")


@app.post("/api/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    Search documents using existing retrieval system.
    """
    try:
        retriever = Retriever(api_key=settings.openai_key)
        chunks = retriever.find_relevant_chunks(request.query, k=request.limit)

        results = []
        for chunk in chunks:
            result = {
                "content": chunk.chunk_content,
                "title": chunk.chunk_title,
                "page_number": chunk.page_number + 1 if chunk.page_number is not None else None,
                "metadata": chunk.meta or {},
                "score": 1.0  # Placeholder score
            }
            results.append(result)

        return SearchResponse(
            results=results,
            total_found=len(results)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {e!s}")


@app.get("/api/sources")
async def list_sources():
    """List available document sources."""
    return {
        "sources": [
            {"name": "Confluence", "type": "wiki", "status": "connected"},
            {"name": "OneDrive", "type": "cloud_storage", "status": "connected"},
            {"name": "Company Wiki", "type": "wiki", "status": "connected"},
            {"name": "Presentations", "type": "documents", "status": "connected"}
        ]
    }


@app.post("/api/chat/openai", response_model=ChatResponse)
async def chat_openai_direct(request: ChatRequest):
    """
    Generate chat response using OpenAI directly (no RAG).
    Used as fallback when documents don't contain the answer.
    """
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_key)

        messages = [
            {"role": "system", "content": "Sie sind ein hilfsreicher KI-Assistent. Beantworten Sie Fragen ausführlich, strukturiert und gut formatiert auf Deutsch. Verwenden Sie Absätze, Aufzählungen und klare Strukturen um die Information verständlich zu präsentieren. Geben Sie detaillierte und umfassende Antworten."}
        ]

        # Add conversation history
        for msg in request.conversation_history:
            messages.append({"role": msg.role, "content": msg.content})

        # Add current message
        messages.append({"role": "user", "content": request.message})

        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=request.temperature,
            max_tokens=2000
        )

        return ChatResponse(
            message=response.choices[0].message.content,
            sources=[]  # No sources for direct OpenAI responses
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error with OpenAI direct response: {e!s}")


@app.post("/api/chat/openai/stream")
async def chat_openai_direct_stream(request: ChatRequest):
    """
    Stream chat response using OpenAI directly (no RAG).
    """
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_key)

        def generate_stream():
            try:
                messages = [
                    {"role": "system", "content": "Sie sind ein hilfsreicher KI-Assistent. Beantworten Sie Fragen ausführlich, strukturiert und gut formatiert auf Deutsch. Verwenden Sie Absätze, Aufzählungen und klare Strukturen um die Information verständlich zu präsentieren. Geben Sie detaillierte und umfassende Antworten."}
                ]

                # Add conversation history
                for msg in request.conversation_history:
                    messages.append({"role": msg.role, "content": msg.content})

                # Add current message
                messages.append({"role": "user", "content": request.message})

                stream = client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    temperature=request.temperature,
                    max_tokens=2000,
                    stream=True
                )

                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield f"data: {chunk.choices[0].delta.content}\n\n"

                yield "data: [DONE]\n\n"

            except Exception as e:
                yield f"data: Error: {e!s}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error streaming OpenAI direct response: {e!s}")


@app.get("/api/projects")
async def list_projects():
    """List available projects."""
    return {
        "projects": [
            {"id": "kb", "name": "Internal Knowledge Base", "description": "Company internal documentation"},
            {"id": "support", "name": "Customer Support Docs", "description": "Support documentation and FAQs"},
            {"id": "analytics", "name": "Product Analytics", "description": "Analytics and reporting data"}
        ]
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
