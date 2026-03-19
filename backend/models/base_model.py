# 감성 분석 모델의 추상 인터페이스 정의
from abc import ABC, abstractmethod

class BaseModel(ABC):
    # 리뷰 텍스트를 분석하여 감성 라벨과 점수를 반환하는 추상 메서드
    @abstractmethod
    def doAnalyzeReview(self, reviewText: str) -> dict[str, float | str]:
        raise NotImplementedError()
