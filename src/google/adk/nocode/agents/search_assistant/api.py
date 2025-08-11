import os
import sys
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Import the agent
from . import agent

class GenerateRequest(BaseModel):
    prompt: str
    temperature: Optional[float] = None

class GenerateResponse(BaseModel):
    text: str

app = FastAPI(title="search_assistant API", description="An assistant that can search the web.")

@app.get("/")
async def root():
    return {"message": "Welcome to the search_assistant API"}

@app.post("/api/generate", response_model=GenerateResponse)
async def generate_content(request: GenerateRequest):
    try:
        response = await agent.root_agent.generate_content(request.prompt)
        return {"text": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print(f"Starting search_assistant API on http://localhost:8000")
    print(f"API documentation available at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
