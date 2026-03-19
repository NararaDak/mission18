import contextlib
import io
import os
import warnings

from common.defines import (
    SENTIMENT_MAX_RATING,
    SENTIMENT_MIN_RATING,
    SENTIMENT_NEUTRAL_RATING,
    SENTIMENT_NEUTRAL_SCORE,
)
from backend.models.base_model import BaseModel


os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")


class HuggingFaceSentimentModel(BaseModel):
    def __init__(self, modelName: str) -> None:
        self.__ModelName = modelName
        self.__Pipeline = None

    def _callSilently(self, callback, *args, **kwargs):
        with io.StringIO() as stdoutBuffer, io.StringIO() as stderrBuffer, warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with contextlib.redirect_stdout(stdoutBuffer), contextlib.redirect_stderr(stderrBuffer):
                return callback(*args, **kwargs)

    def _getPipeline(self):
        if self.__Pipeline is None:
            from huggingface_hub.utils import logging as huggingfaceLogging
            from transformers import logging as transformersLogging, pipeline

            huggingfaceLogging.set_verbosity_error()
            transformersLogging.set_verbosity_error()
            self.__Pipeline = self._callSilently(
                pipeline,
                "text-classification",
                model=self.__ModelName,
                top_k=None,
            )
        return self.__Pipeline

    def _normalizeLabel(self, rawLabel: str) -> str:
        labelText = rawLabel.strip().lower()
        if "neg" in labelText or "1" == labelText:
            return "negative"
        if "neu" in labelText:
            return "neutral"
        return "positive"

    def _normalizeResults(self, pipelineResult: object) -> list[dict[str, float | str]]:
        if isinstance(pipelineResult, list):
            if pipelineResult and isinstance(pipelineResult[0], list):
                nestedResults = pipelineResult[0]
                return [result for result in nestedResults if isinstance(result, dict)]
            return [result for result in pipelineResult if isinstance(result, dict)]
        if isinstance(pipelineResult, dict):
            return [pipelineResult]
        return []

    def _computeSentimentScore(self, resultList: list[dict[str, float | str]]) -> float:
        probabilityMap = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
        for resultData in resultList:
            labelText = self._normalizeLabel(str(resultData.get("label", "neutral")))
            probabilityMap[labelText] += float(resultData.get("score", 0.0))

        totalProbability = sum(probabilityMap.values())
        if totalProbability <= 0:
            return SENTIMENT_NEUTRAL_SCORE

        positiveProbability = probabilityMap["positive"] / totalProbability
        neutralProbability = probabilityMap["neutral"] / totalProbability
        weightedScore = positiveProbability + (neutralProbability * SENTIMENT_NEUTRAL_SCORE)
        return round(max(0.0, min(1.0, weightedScore)), 4)

    def _scoreToRating(self, scoreValue: float) -> int:
        normalizedScore = max(0.0, min(1.0, scoreValue))
        return max(SENTIMENT_MIN_RATING, min(SENTIMENT_MAX_RATING, int(normalizedScore * 5) + 1))

    def _ratingToLabel(self, ratingValue: int) -> str:
        if ratingValue <= 2:
            return "negative"
        if ratingValue == SENTIMENT_NEUTRAL_RATING:
            return "neutral"
        return "positive"

    def doAnalyzeReview(self, reviewText: str) -> dict[str, float | str]:
        pipelineModel = self._getPipeline()
        resultList = self._normalizeResults(self._callSilently(pipelineModel, reviewText))
        if not resultList:
            return {"sentimentLabel": "neutral", "sentimentScore": SENTIMENT_NEUTRAL_RATING}

        sentimentScore = self._computeSentimentScore(resultList)
        sentimentRating = self._scoreToRating(sentimentScore)
        sentimentLabel = self._ratingToLabel(sentimentRating)
        return {"sentimentLabel": sentimentLabel, "sentimentScore": sentimentRating}
