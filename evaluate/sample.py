import random
import re
from abc import abstractmethod
from collections import defaultdict
from typing import Callable, Generic, Iterator, Protocol, Tuple, TypeVar

T = TypeVar("T")


Group = tuple[T, ...]

Grouper = Callable[[list[T]], list[Group[T]]]
"""A function which groups samples into lists of samples.

The grouper can be used to keep correlated documents together.
"""


def identity_group(samples: list[T]) -> list[Group[T]]:
    """The simplest grouper which returns each sample in its own group.

    Args:
        samples: A list of samples.

    Returns:
        A list of groups, where each group contains one unique sample from
        the input.
    """
    return [(s,) for s in samples]


def ungroup(samples: list[Group[T]]) -> list[T]:
    """Flatten a list of groups into a list of samples.

    Args:
        samples: A list of groups.

    Returns:
        A list of samples.
    """
    return [s for group in samples for s in group]


class RegExMatchGrouper:
    """Group samples by applying a regular expression to a string.

    Args:
        samples: A list of strings.

    Returns:
        A list of tuples of strings.
    """

    def __init__(self, pattern: str):
        """Initialize a RegExMatchGrouper.

        Args:
            pattern: A regular expression pattern with a match group
        """
        self.pattern = re.compile(pattern)

    def __call__(self, samples: list[str]) -> list[Group[str]]:
        """Group samples using a match group from a regular expression.

        Args:
            samples: A list of strings.

        Returns:
            A list of tuples of strings.
        """
        groups = defaultdict(list)
        for sample in samples:
            match = self.pattern.match(sample)
            if match is None:
                raise ValueError(f"Could not parse string {sample}")
            match_group = match.group(1)
            groups[match_group].append(sample)
        return [tuple(v) for v in groups.values()]


class Sampler(Protocol, Generic[T]):
    """Split a list of samples into train and test sets."""

    @abstractmethod
    def __call__(
        self, samples: list[T], seed: int = 0, grouper: Grouper[T] = identity_group
    ) -> Iterator[Tuple[list[T], list[T]]]:
        """Get a list of train and test sets from `samples`.

        Args:
            samples: A list of samples.
            seed: The random seed to use for shuffling the samples.
            grouper: A function which groups samples into lists of samples.

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
        self, samples: list[T], seed: int = 0, grouper: Grouper[T] = identity_group
    ) -> Iterator[Tuple[list[T], list[T]]]:
        if len(samples) < self.k:
            raise ValueError("There must be at least k samples")

        rng = random.Random(seed)
        groups = grouper(samples)
        for g in groups:
            if not g:
                raise ValueError("A group must contain at least one sample")

        rng.shuffle(groups)
        n = len(groups)
        # Get the ideal size of each fold.
        fold_size = n // self.k
        # Get the number of folds that will have one extra group.
        num_folds_with_extra_group = n % self.k
        # Generate the folds.
        cur_idx = 0
        for i in range(self.k):
            # Get the size of this fold.
            size = fold_size
            if i < num_folds_with_extra_group:
                size += 1
            # Get the groups for this fold.
            train = groups[:cur_idx] + groups[cur_idx + size :]
            test = groups[cur_idx : cur_idx + size]

            # Probably should never get to this scenario given the initial
            # sanity checks, but just in case.
            unpacked_test = ungroup(test)
            if not unpacked_test:
                raise ValueError("A fold must contain at least one sample")

            yield ungroup(train), unpacked_test
            cur_idx += size
