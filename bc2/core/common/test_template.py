from typing import Any

import pytest

from .template import TemplateEngine, get_formatter


@pytest.mark.parametrize(
    "engine,template,variables,expected",
    [
        ("jinja", "Hello, {{ name }}!", {"name": "world"}, "Hello, world!"),
        ("string", "Hello, {name}!", {"name": "world"}, "Hello, world!"),
        ("string", "Hello!", {"name": "world"}, "Hello!\nworld"),
        (
            "string",
            "Input: {input}, Aliases: {aliases}",
            {"input": "foo", "aliases": {"bar": "baz"}},
            "Input: foo, Aliases: {'bar': 'baz'}",
        ),
        (
            "string",
            "Input,aliases",
            {"input": "foo", "aliases": {"bar": "baz"}},
            "Input,aliases\nfoo\n{'bar': 'baz'}",
        ),
        (
            "string",
            "Input,aliases",
            {"input": "foo", "aliases": "", "bar": None},
            "Input,aliases\nfoo\n",
        ),
    ],
)
def test_format_template(
    engine: TemplateEngine, template: str, variables: dict[str, Any], expected: str
):
    formatter = get_formatter(engine)
    assert formatter(template, variables) == expected
