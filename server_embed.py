from fastapi import FastAPI
from pydantic import BaseModel
import openvino as ov
from transformers import AutoTokenizer
import numpy as np
import time

MODEL_PATH = "/models/openvino/nomic-embed-text-v1.5"
DEVICE = "GPU"

core = ov.Core()
model = core.read_model(f"{MODEL_PATH}/openvino_model.xml")
compiled_model = core.compile_model(model, DEVICE)

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)

app = FastAPI()

class EmbeddingRequest(BaseModel):
    model: str = "nomic-embed-text-v1.5-openvino"
    input: str | list[str]

def mean_pooling(last_hidden_state, attention_mask):
    mask = np.expand_dims(attention_mask, axis=-1)
    masked = last_hidden_state * mask
    summed = masked.sum(axis=1)
    counts = np.clip(mask.sum(axis=1), a_min=1e-9, a_max=None)
    return summed / counts

def normalize(vectors):
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.clip(norms, a_min=1e-12, a_max=None)

@app.get("/v1/models")
def models():
    return {
        "object": "list",
        "data": [
            {
                "id": "nomic-embed-text-v1.5-openvino",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "local-openvino"
            }
        ]
    }

@app.post("/v1/embeddings")
def embeddings(req: EmbeddingRequest):
    texts = req.input if isinstance(req.input, list) else [req.input]

    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=8192,
        return_tensors="np"
    )

    outputs = compiled_model(encoded)

    # tenta pegar a primeira saída automaticamente
    hidden = list(outputs.values())[0]

    vectors = mean_pooling(hidden, encoded["attention_mask"])
    vectors = normalize(vectors)

    data = []
    for i, vec in enumerate(vectors):
        data.append({
            "object": "embedding",
            "index": i,
            "embedding": vec.astype(float).tolist()
        })

    return {
        "object": "list",
        "data": data,
        "model": req.model,
        "usage": {
            "prompt_tokens": 0,
            "total_tokens": 0
        }
    }
