from __future__ import annotations
from abc import ABC, abstractmethod
from numpy.typing import NDArray
from ..scheduler import TaskException


class BaseEffect(ABC):
    """
    Protected Base Effect
    """

    @property
    def name(self):
        return self.__class__.__name__

    # Main method to apply effect, takes and returns a numpy ndarray.
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

    # Wrapper to run apply with exception tracing
    # Do not override this method in subclasses !
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
