import re

import requests

from common.defines import SENTIMENT_NEUTRAL_RATING
from backend.models.base_model import BaseModel


class OllamaSentimentModel(BaseModel):
    def __init__(self, modelName: str, baseUrl: str, timeoutSec: int) -> None:
        self.__ModelName = modelName
        self.__BaseUrl = baseUrl.rstrip("/")
        self.__TimeoutSec = timeoutSec

    def _buildPrompt(self, reviewText: str) -> str:
        return (
            "너는 냉철한 영화 평론가야. "
            "다음 영화 리뷰의 감정을 분석해서 1점(최악)에서 5점(최고) 사이의 정수 점수만 출력해줘.\n"
            f"리뷰: {reviewText}"
        )

    def _parseRating(self, responseText: str) -> int:
        matches = re.findall(r"\b([1-5])\b", responseText)
        return int(matches[0]) if matches else 3

    def _ratingToLabel(self, rating: int) -> str:
        if rating <= 2:
            return "negative"
        if rating == SENTIMENT_NEUTRAL_RATING:
            return "neutral"
        return "positive"

    def doAnalyzeReview(self, reviewText: str) -> dict[str, float | str]:
        responseData = requests.post(
            f"{self.__BaseUrl}/api/generate",
            json={
                "model": self.__ModelName,
                "prompt": self._buildPrompt(reviewText),
                "stream": False,
                "options": {"temperature": 0},
            },
            timeout=self.__TimeoutSec,
        )
        responseData.raise_for_status()

        payloadData = responseData.json()
        resultText = str(payloadData.get("response", ""))
        rating = self._parseRating(resultText)
        sentimentLabel = self._ratingToLabel(rating)

        return {"sentimentLabel": sentimentLabel, "sentimentScore": rating}
