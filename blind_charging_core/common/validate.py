import json
import logging

logger = logging.getLogger(__name__)


def validate_json(raw: str) -> dict:
    """Try to parse a string as a JSON object.

    The response should be a dictonary.

    Args:
        response: The response from the generator.

    Returns:
        A dict of the parsed JSON.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON response: {e}")
        raise ValueError("Error parsing JSON response.") from e

    return data