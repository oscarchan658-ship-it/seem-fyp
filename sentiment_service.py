"""Sentiment is a response-style signal, never a questionnaire scoring input."""

import re
from functools import lru_cache
from pathlib import Path

from terra_client import TerraClient

MODEL_PATH = Path(__file__).parent / "results/tweeteval-20261126/sentiment_model.joblib"


@lru_cache(maxsize=1)
def local_model():
    import joblib

    return joblib.load(MODEL_PATH)


def analyze(text, backend):
    if backend == "off":
        return "unavailable", "情緒分析未啟用"
    try:
        if backend == "terra":
            label, _ = TerraClient().sentiment(text)
            return label, "GPT-6.1 Terra · 第三方端點回報，非診斷"
        if backend != "local" or re.search(r"[\u3400-\u9fff]", text):
            return "unavailable", "本地模型只評估過英文；繁中輸入不作推論"
        label = ("negative", "neutral", "positive")[
            int(local_model().predict([text])[0])
        ]
        return label, "TweetEval 英文 TF-IDF + Linear SVM"
    except Exception:
        return "unavailable", "情緒模型暫不可用；問卷仍可繼續"
