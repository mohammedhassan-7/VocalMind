from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import uvicorn
import os
import shutil
import tempfile
import subprocess
import numpy as np
import torch
from funasr import AutoModel
from transformers import pipeline
from starlette.concurrency import run_in_threadpool
from contextlib import asynccontextmanager
import asyncio
import logging
from fastapi import Request

# Global dictionary to hold the loaded model
ml_models = {}
inference_lock = asyncio.Lock()
MAX_INFERENCE_SECONDS = int(os.getenv("EMOTION_MAX_AUDIO_SECONDS", "30"))
logger = logging.getLogger(__name__)

class TextPredictRequest(BaseModel):
    text: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Check if CUDA is available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")

    # Initialize the audio model
    logger.info("Loading model iic/emotion2vec_plus_base inside worker...")
    # SECURITY NOTE: trust_remote_code=True allows arbitrary code execution from the
    # model repository. This is intentional for this model but means the security
    # posture of this service depends on the integrity of the upstream HF repo.
    # Model should be pinned to a specific commit hash in production, not a tag.
    # Reviewed and accepted: 2026-06-16 — revisit if model source changes.
    ml_models["emotion2vec"] = AutoModel(model="iic/emotion2vec_plus_base", trust_remote_code=True, disable_update=True, device=device)
    logger.info("Audio model loaded successfully.")

    # Initialize the text model. Failure to load must NOT break the container —
    # /predict_text will return 503 and callers fall back to the rule-based
    # text emotion provider in the backend (emotion_fusion._HF_PROVIDER_DISABLED_REASON).
    try:
        logger.info("Loading text emotion model j-hartmann/emotion-english-distilroberta-base...")
        hf_device = 0 if device == "cuda" else -1
        ml_models["text_emotion"] = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            device=hf_device,
            top_k=None,
        )
        logger.info("Text emotion model loaded successfully.")
    except Exception as exc:
        logger.warning(f"WARNING: text emotion model failed to load: {exc}. /predict_text will return 503.")

    yield
    # Clean up the ML models and release the resources
    ml_models.clear()

app = FastAPI(title="Emotion Recognition API", lifespan=lifespan)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")
    if request_id:
        logger.info("[request_id=%s] Emotion request %s %s", request_id, request.method, request.url.path)
    response = await call_next(request)
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response


def _run_inference(filepath):
    logger.info(f"Starting inference on file: {filepath}")
    return ml_models["emotion2vec"].generate(input=filepath, extract_embedding=False)

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    filename = (file.filename or "").lower()
    if not (filename.endswith('.wav') or filename.endswith('.mp3')):
        raise HTTPException(status_code=400, detail="Only .wav or .mp3 files are supported.")

    suffix = '.wav' if filename.endswith('.wav') else '.mp3'

    # Save the uploaded file temporarily
    fd, temp_path = tempfile.mkstemp(suffix=suffix)
    normalized_wav_path = None
    try:
        with os.fdopen(fd, 'wb') as f:
            shutil.copyfileobj(file.file, f)

        # Normalize all inputs to a bounded mono 16k wav to avoid unstable inference on long/raw files.
        fd_wav, normalized_wav_path = tempfile.mkstemp(suffix='.wav')
        os.close(fd_wav)
        subprocess.run(
            [
                "ffmpeg",
                "-nostdin",
                "-y",
                "-i",
                temp_path,
                "-ac",
                "1",
                "-ar",
                "16000",
                "-t",
                str(MAX_INFERENCE_SECONDS),
                normalized_wav_path,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        inference_path = normalized_wav_path

        # Run inference using the pre-loaded FunaSR model via threadpool
        async with inference_lock:
            results = await run_in_threadpool(_run_inference, inference_path)
        logger.info(f"Inference finished. Results: {results}")

        # Parse result
        if results and len(results) > 0:
            res = results[0]
            highest_score_idx = np.argmax(res['scores'])
            raw_label = res['labels'][highest_score_idx]

            # The label comes as "中文/english" like "开心/happy"
            emotion = raw_label.split('/')[-1] if '/' in raw_label else raw_label
            confidence = float(res['scores'][highest_score_idx])

            return {
                "emotion": emotion,
                "confidence": confidence,
                "raw_result": {
                    "labels": [lbl.split('/')[-1] if '/' in lbl else lbl for lbl in res['labels']],
                    "scores": [float(s) for s in res['scores']]
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Model inference returned empty results.")

    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or b"").decode(errors="ignore")
        raise HTTPException(status_code=400, detail=f"Failed to decode/convert audio: {stderr[:400]}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")
    finally:
        # Clean up the temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if normalized_wav_path and os.path.exists(normalized_wav_path):
            os.remove(normalized_wav_path)

@app.get("/health")
async def health():
    return {
        "status": "ok", 
        "audio_model_loaded": "emotion2vec" in ml_models,
        "text_model_loaded": "text_emotion" in ml_models
    }

@app.post("/predict_text")
async def predict_text(request: TextPredictRequest):
    if not request.text or not request.text.strip():
        return {"emotion": "neutral", "confidence": 0.2}

    if "text_emotion" not in ml_models:
        raise HTTPException(
            status_code=503,
            detail="Text emotion model unavailable; backend will fall back to rule-based provider.",
        )

    try:
        # Run inference using the pre-loaded HF pipeline
        raw_result = ml_models["text_emotion"](request.text)
        
        # Pipeline with top_k=None returns a list of lists of dicts: [[{'label': 'joy', 'score': 0.9}, ...]]
        scores = raw_result[0] if raw_result and isinstance(raw_result[0], list) else []
        
        if not scores:
            return {"emotion": "neutral", "confidence": 0.3}
            
        # Get the top score
        top_emotion = max(scores, key=lambda x: x["score"])
        
        return {
            "emotion": top_emotion["label"],
            "confidence": float(top_emotion["score"]),
            "raw_result": scores
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text emotion inference failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
