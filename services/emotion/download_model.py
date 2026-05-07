"""Pre-bake all emotion models into the Docker image so first request never
needs HuggingFace Hub or ModelScope at runtime.

Models cached:
  * iic/emotion2vec_plus_base                       (FunASR audio emotion)
  * j-hartmann/emotion-english-distilroberta-base   (HF text emotion)
"""

import time

from funasr import AutoModel
from transformers import pipeline


def download_with_retry(label, fn, max_retries=5, delay=5):
    for i in range(max_retries):
        try:
            print(f"Attempt {i + 1}: Downloading {label}...")
            obj = fn()
            print(f"Successfully downloaded {label}")
            return obj
        except Exception as exc:
            print(f"Error downloading {label}: {exc}")
            if i < max_retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"Failed to download {label} after {max_retries} attempts.")
                raise


if __name__ == "__main__":
    download_with_retry(
        "iic/emotion2vec_plus_base",
        lambda: AutoModel(model="iic/emotion2vec_plus_base", trust_remote_code=True),
    )
    download_with_retry(
        "j-hartmann/emotion-english-distilroberta-base",
        lambda: pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=None,
        ),
    )
