from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from numpy.typing import NDArray

from ..task import TaskException


class BaseEffect(ABC):
    """
    Abstract Base Class for Effects
    """

    @property
    def name(self):
        return self.__class__.__name__

    @abstractmethod
    def apply(self, data: NDArray, sr: float) -> tuple[NDArray, float]:
        """
        Apply the audio effect

        Args:
            data: NDArray of audio
            sr: Sample Rate as float

        Returns: NDArray of processed audio
        """
        ...  # pragma: no cover

    def apply_trace(self, data: NDArray, sr: float) -> tuple[NDArray, float]:
        """
        Apply the audio effect with exception tracing

        Args:
            data: NDArray of audio
            sr: Sample Rate as float

        Returns: NDArray of processed audio
        """
        try:
            return self.apply(data, sr)
        except Exception as e:
            # Raise with current class name
            raise TaskException(e, self.__class__.__name__)
