from .common import Renderer

_REGISTRY: dict[str, Renderer] = {}


def register(renderer: Renderer) -> None:
    """Register a renderer.

    Args:
        renderer: The renderer to register.
    """
    _REGISTRY[renderer.name.lower()] = renderer


def get_renderer(name: str) -> Renderer:
    """Get a renderer by name.

    Args:
        name: The name of the renderer to get.

    Returns:
        The renderer.

    Raises:
        ValueError: If the renderer is not found.
    """
    key = name.lower()
    if key not in _REGISTRY:
        raise ValueError(f"Unknown renderer: {name}")
    return _REGISTRY[key]
