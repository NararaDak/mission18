from abc import ABC, abstractmethod


class BaseModel(ABC):
    @abstractmethod
    def doAnalyzeReview(self, reviewText: str) -> dict[str, float | str]:
        raise NotImplementedError()
