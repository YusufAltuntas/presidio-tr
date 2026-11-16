"""Presidio analyzer HTTP API'siyle uyumlu, presidio-tr tanıyıcılarını kullanan sunucu.

LiteLLM'in Presidio guardrail'i bu sunucunun /analyze ucunu çağırır.
PRESIDIO_TR_NER=1 ortam değişkeni isim tanımayı (PERSON) açar; `presidio-tr[ner]` ekini ister.
"""

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from presidio_tr import LANGUAGE, build_analyzer

app = FastAPI(title="presidio-tr analyzer")
analyzer = build_analyzer(ner=os.environ.get("PRESIDIO_TR_NER") == "1")


class AnalyzeRequest(BaseModel):
    text: str
    language: str = LANGUAGE
    entities: list[str] | None = None
    # Presidio API'sindeki alan; 0.7 verilirse bağlam kademesi (0.6) elenir.
    score_threshold: float | None = None


@app.get("/health")
def health() -> str:
    return "Presidio Analyzer service is up"


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> list[dict]:
    if request.language != LANGUAGE:
        raise HTTPException(status_code=400, detail=f"Desteklenmeyen dil: {request.language}")
    results = analyzer.analyze(
        text=request.text,
        language=request.language,
        entities=request.entities,
        score_threshold=request.score_threshold,
    )
    return [{"entity_type": r.entity_type, "start": r.start, "end": r.end, "score": r.score} for r in results]
