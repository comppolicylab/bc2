import string
from typing import Any, Callable, Literal

from jinja2 import Template

TemplateEngine = Literal["jinja", "string"]

Formatter = Callable[[str, dict[str, Any]], str]

Ctx = dict[str, Any]


def format_jinja(prompt: str, ctx: Ctx) -> str:
    """Format the prompt as a Jinja template."""
    template = Template(prompt)
    return template.render(**ctx)


def format_string(prompt: str, ctx: Ctx) -> str:
    """Format the prompt as a string template."""
    # Check if the prompt has a named `prompt` placeholder
    fmt = string.Formatter()

    if any(field[1] is not None for field in fmt.parse(prompt)):
        return prompt.format(**ctx)

    # Otherwise tack the prompt onto the end of the string
    input = ctx.get("input", "")
    output = prompt
    if input:
        output += "\n" + input
    return output


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
