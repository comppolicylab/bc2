import json
import logging

logger = logging.getLogger(__name__)


def parse_llm_json(s: str, debug: bool = False) -> dict:
    """Parse a JSON response from an LLM.

    Account for potential funkiness in the response, according to
    how LLMs tend to format their responses.

    Args:
        s: The JSON response.

    Returns:
        The parsed JSON response.

    Raises:
        ValueError: If the JSON response is invalid.
    """
    if s.startswith("```json"):
        s = s[7:]
    if s.startswith("```"):
        s = s[3:]
    if s.endswith("```"):
        s = s[:-3]
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        if debug:
            logger.error(f"Error parsing JSON: {e}")
            logger.error("Input:\n" + s)
        raise ValueError("Error parsing JSON") from e
