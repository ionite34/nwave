# Base Audio Processing Effects and Resample Filters
from abc import ABC, abstractmethod
from ..exceptions import TaskException
import logging
import traceback
from numpy.typing import NDArray


class BaseEffect(ABC):
    """
    Protected Base Effect
    """

    def __init__(self):
        pass

    @property
    def name(self):
        return self.__class__.__name__

    # Main method to apply effect, takes and returns a numpy ndarray.
    @abstractmethod
    def _apply(self, data: NDArray, sr: float) -> tuple[NDArray, float]:
        """
        Apply the audio effect

        Args:
            data: NDArray of audio
            sr: Sample Rate as float

        Returns: NDArray of processed audio

        """
        raise NotImplementedError('Must implement apply method')

    # Wrapper to run apply with exception tracing
    # Do not override this method in subclasses !
    def apply_trace(self, data: NDArray, sr: float) -> tuple[NDArray, float]:
        # noinspection PyBroadException
        try:
            result = self._apply(data, sr)
            if not isinstance(result, tuple) or len(result) != 2 or not isinstance(result[0], NDArray) or not isinstance(result[1], float):
                raise ValueError(f"Effect [{self.name}] must return a tuple of (NDArray, float),"
                                 f" got [{type(result)}] as [{result}].")
            return result
        except Exception as e:
            # Get the current class name
            _trace = traceback.format_exc()
            raise TaskException(e, self.__class__.__name__).with_traceback(e.__traceback__)
