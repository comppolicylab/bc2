import string
from typing import Any, Callable, Literal

from jinja2 import Template

TemplateEngine = Literal["jinja", "string"]

Formatter = Callable[[str, dict[str, Any]], str]

Ctx = dict[str, Any]


def format_jinja(tpl: str, ctx: Ctx) -> str:
    """Format the template with Jinja."""
    template = Template(tpl)
    return template.render(**ctx)


def format_string(tpl: str, ctx: Ctx) -> str:
    """Format the template with string formatting."""
    fmt = string.Formatter()

    # Use string-formatting if there are placeholders.
    if any(field[1] is not None for field in fmt.parse(tpl)):
        return tpl.format(**ctx)

    # If there are no placeholders, just tack on fields to the end.
    outputs: list[str] = [tpl]
    for value in ctx.values():
        outputs.append(str(value))

    return "\n".join(outputs)


def get_formatter(engine: TemplateEngine) -> Formatter:
    """Get the formatter for the given template engine.

    Args:
        engine: The template engine to use.

    Returns:
        The formatter function.
    """
    match engine:
        case "jinja":
            return format_jinja
        case "string":
            return format_string
        case _:
            raise ValueError(f"Unsupported template engine: {engine}")
