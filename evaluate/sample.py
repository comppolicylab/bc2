import random
from abc import abstractmethod
from typing import Generic, Iterator, Protocol, Tuple, TypeVar

T = TypeVar("T")


class Sampler(Protocol, Generic[T]):
    """Split a list of samples into train and test sets."""

    @abstractmethod
    def __call__(
        self, samples: list[T], seed: int = 0
    ) -> Iterator[Tuple[list[T], list[T]]]:
        """Get a list of train and test sets from `samples`.

        Args:
            samples: A list of samples.
            seed: The random seed to use for shuffling the samples.

        Yields:
            Tuples of train and test sets
        """
        ...


class KFoldCrossValidationSampler(Sampler[T]):
    """Split a list of samples into K train and test sets."""

    def __init__(self, k: int):
        """Initialize a KFoldCrossValidationSampler.

        Args:
            k: The number of folds.
        """
        if k < 2:
            raise ValueError("k must be greater than 1")
        self.k = k

    def __call__(
        self, samples: list[T], seed: int = 0
    ) -> Iterator[Tuple[list[T], list[T]]]:
        if len(samples) < self.k:
            raise ValueError("There must be at least k samples")

        rng = random.Random(seed)
        rng.shuffle(samples)
        n = len(samples)
        # Get the ideal size of each fold.
        fold_size = n // self.k
        # Get the number of folds that will have one extra sample.
        num_folds_with_extra_sample = n % self.k
        # Generate the folds.
        cur_idx = 0
        for i in range(self.k):
            # Get the size of this fold.
            size = fold_size
            if i < num_folds_with_extra_sample:
                size += 1
            # Get the samples for this fold.
            train = samples[:cur_idx] + samples[cur_idx + size :]
            test = samples[cur_idx : cur_idx + size]
            yield train, test
            cur_idx += size
