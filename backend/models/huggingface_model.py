# Hugging Face Transformers를 이용한 로컬 감성 분석 모델 구현
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

# 라이브러리 경고 및 진행바 비활성화 설정
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

class HuggingFaceSentimentModel(BaseModel):
    def __init__(self, modelName: str) -> None:
        # 모델명 저장 및 파이프라인 지연 로딩용 변수 초기화
        self.__ModelName = modelName
        self.__Pipeline = None

    # 표준 출력 및 경고를 억제하며 콜백함수 실행
    def _callSilently(self, callback, *args, **kwargs):
        with io.StringIO() as stdoutBuffer, io.StringIO() as stderrBuffer, warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with contextlib.redirect_stdout(stdoutBuffer), contextlib.redirect_stderr(stderrBuffer):
                return callback(*args, **kwargs)

    # Transformers 파이프라인 인스턴스 싱글톤 로드
    def _getPipeline(self):
        if self.__Pipeline is None:
            from huggingface_hub.utils import logging as huggingfaceLogging
            from transformers import logging as transformersLogging, pipeline
            huggingfaceLogging.set_verbosity_error()
            transformersLogging.set_verbosity_error()
            self.__Pipeline = self._callSilently(
                pipeline, "text-classification", model=self.__ModelName, top_k=None
            )
        return self.__Pipeline

    # 원본 라벨(LABEL_0 등)을 positive/neutral/negative로 정규화
    def _normalizeLabel(self, rawLabel: str) -> str:
        labelText = rawLabel.strip().lower()
        if "neg" in labelText or "1" == labelText: return "negative"
        if "neu" in labelText: return "neutral"
        return "positive"

    # 파이프라인 결과 형식을 리스트 형태로 정규화
    def _normalizeResults(self, pipelineResult: object) -> list[dict[str, float | str]]:
        if isinstance(pipelineResult, list):
            if pipelineResult and isinstance(pipelineResult[0], list):
                return [res for res in pipelineResult[0] if isinstance(res, dict)]
            return [res for res in pipelineResult if isinstance(res, dict)]
        return [pipelineResult] if isinstance(pipelineResult, dict) else []

    # 분석 결과(확률값들)를 종합하여 0~1 사이 가중치 점수 계산
    def _computeSentimentScore(self, resultList: list[dict[str, float | str]]) -> float:
        probabilityMap = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
        for resultData in resultList:
            labelText = self._normalizeLabel(str(resultData.get("label", "neutral")))
            probabilityMap[labelText] += float(resultData.get("score", 0.0))

        total = sum(probabilityMap.values())
        if total <= 0: return SENTIMENT_NEUTRAL_SCORE
        weightedScore = (probabilityMap["positive"] / total) + ((probabilityMap["neutral"] / total) * SENTIMENT_NEUTRAL_SCORE)
        return round(max(0.0, min(1.0, weightedScore)), 4)

    # 점수(0~1)를 별점 범위(1~5)로 변환
    def _scoreToRating(self, scoreValue: float) -> int:
        normalizedScore = max(0.0, min(1.0, scoreValue))
        return max(SENTIMENT_MIN_RATING, min(SENTIMENT_MAX_RATING, int(normalizedScore * 5) + 1))

    # 별점을 기반으로 최종 감성 라벨 결정
    def _ratingToLabel(self, ratingValue: int) -> str:
        if ratingValue <= 2: return "negative"
        if ratingValue == SENTIMENT_NEUTRAL_RATING: return "neutral"
        return "positive"

    # 리뷰 분석 실행 메인 엔트리
    def doAnalyzeReview(self, reviewText: str) -> dict[str, float | str]:
        pipelineModel = self._getPipeline()
        resultList = self._normalizeResults(self._callSilently(pipelineModel, reviewText))
        if not resultList:
            return {"sentimentLabel": "neutral", "sentimentScore": SENTIMENT_NEUTRAL_RATING}

        score = self._computeSentimentScore(resultList)
        rating = self._scoreToRating(score)
        label = self._ratingToLabel(rating)
        return {"sentimentLabel": label, "sentimentScore": rating}
