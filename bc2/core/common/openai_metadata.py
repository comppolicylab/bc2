from dataclasses import dataclass


@dataclass
class ModelMeta:
    name: str
    context: int
    output: int


_MODELS = {
    meta.name.lower(): meta
    ##########################################################
    # NOTE(jnu): ADD NEW MODELS HERE AS WE SUPPORT THEM.
    ##########################################################
    for meta in [
        ModelMeta(name="gpt-4o-2024-05-13", context=128_000, output=4_096),
        ModelMeta(name="gpt-4o-2024-08-06", context=128_000, output=16_384),
        ModelMeta(name="gpt-4o-2024-11-20", context=128_000, output=16_384),
        ModelMeta(name="o3-mini-2025-01-31", context=200_000, output=100_000),
        ModelMeta(name="o1-mini-2024-09-12", context=128_000, output=65_536),
        ModelMeta(name="gpt-4.5-preview-2025-02-27", context=128_000, output=16_384),
        ModelMeta(name="gpt-4o-mini-2024-07-18", context=128_000, output=16_384),
        ModelMeta(name="gpt-4-turbo-2024-04-09", context=128_000, output=4_096),
        ModelMeta(name="gpt-4-0125-preview", context=128_000, output=4_096),
        ModelMeta(name="gpt-4-0613", context=8_192, output=8_192),
        ModelMeta(name="gpt-4-0314", context=8_192, output=8_192),
        ModelMeta(name="gpt-3.5-turbo-0125", context=16_385, output=4_096),
        ModelMeta(name="gpt-3.5-turbo-1106", context=16_385, output=4_096),
    ]
}


class ModelNotFound(Exception):
    """Raised when a model is not found in the metadata."""

    pass


def get_model_meta(model: str) -> ModelMeta:
    """Get metadata for a model by name.

    Args:
        model: The fully-specified name of the model (e.g. 'gpt-4o-2024-05-13').

    Returns:
        The metadata for the model.

    Raises:
        ModelNotFound: If the model is not found.
    """
    # NOTE(jnu): We could support fuzzy matching to pull metadata when a
    # specific version is unspecified. There is a risk that our metadata is
    # out of date in this case and that the real model that OpenAI/Azure will
    # use in this case has different properties (such as an expanded context).
    # It's better to just throw an error and remind us to update the metadata.
    try:
        return _MODELS[model.lower()]
    except KeyError as e:
        raise ModelNotFound(f"Model '{model}' not found in metadata.") from e
