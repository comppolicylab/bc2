import datetime
import json
import logging

logger = logging.getLogger(__name__)


def date_aware_json_load(fp, **kwargs):
    """
    Load JSON data from a file-like object or a string,
    parsing ISO format date and datetime strings automatically.

    Args:
        fp: File-like object or string containing JSON data.
        **kwargs: Additional json.load options.

    Returns:
        Loaded data with dates/datetimes parsed as datetime objects.
    """

    def parse_dates(obj):
        for k, v in obj.items():
            if isinstance(v, str):
                # Try parsing as datetime, then date
                try:
                    obj[k] = datetime.datetime.fromisoformat(v)
                except ValueError:
                    try:
                        obj[k] = datetime.date.fromisoformat(v)
                    except ValueError:
                        pass
        return obj

    if hasattr(fp, "read"):
        return json.load(fp, object_hook=parse_dates, **kwargs)
    else:
        return json.loads(fp, object_hook=parse_dates, **kwargs)


class _DateTimeJSONEncoder(json.JSONEncoder):
    """Custom encoder that serializes datetime/date objects to ISO strings."""

    def default(self, o):
        if isinstance(o, (datetime.datetime, datetime.date)):
            return o.isoformat()
        return super().default(o)


def date_aware_json_dump(obj, fp, **kwargs):
    """
    Write JSON-serializable object to a file, encoding date/datetime as ISO strings.

    Args:
        obj: The object to serialize.
        fp: The file-like object to write to.
        **kwargs: Additional json.dump options.
    """
    return json.dump(obj, fp, cls=_DateTimeJSONEncoder, **kwargs)


def date_aware_json_dumps(obj, **kwargs):
    """
    Create a JSON string from an object, encoding date/datetime as ISO strings.

    Args:
        obj: The object to serialize.
        **kwargs: Additional json.dumps options.

    Returns:
        JSON string.
    """
    return json.dumps(obj, cls=_DateTimeJSONEncoder, **kwargs)


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
