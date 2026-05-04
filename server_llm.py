from fastapi import FastAPI
from pydantic import BaseModel
import openvino_genai as ov_genai
import time
import uuid

MODEL_PATH = "/models/openvino/gemma-4-E2B-it"
DEVICE = "GPU"

pipe = ov_genai.LLMPipeline(MODEL_PATH, DEVICE)

app = FastAPI()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str = "gemma-4-E2B-it-openvino"
    messages: list[Message]
    temperature: float = 0.7
    max_tokens: int = 512
    stream: bool = False

@app.get("/v1/models")
def models():
    return {
        "object": "list",
        "data": [
            {
                "id": "gemma-4-E2B-it-openvino",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "local-openvino"
            }
        ]
    }

@app.post("/v1/chat/completions")
def chat(req: ChatRequest):
    prompt = ""

    for msg in req.messages:
        if msg.role == "system":
            prompt += f"System: {msg.content}\n"
        elif msg.role == "user":
            prompt += f"User: {msg.content}\n"
        elif msg.role == "assistant":
            prompt += f"Assistant: {msg.content}\n"

    prompt += "Assistant:"

    result = pipe.generate(
        prompt,
        max_new_tokens=req.max_tokens,
        temperature=req.temperature,
        do_sample=req.temperature > 0
    )

    text = str(result)

    return {
        "id": "chatcmpl-" + str(uuid.uuid4()),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": text
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }
