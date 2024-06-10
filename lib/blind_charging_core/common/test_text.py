import pytest

from .text import RedactedText, escape_for_xml


def _test_style(text: str, type_: str) -> str:
    return f"<style:{type_}>{text}</style:{type_}>"


def _test_graf(text: str) -> str:
    return f"<p>{text}</p>"


@pytest.mark.parametrize(
    "original,redacted,delimiters,expected",
    [
        (
            "Hello, world!",
            "Hello, <Person 1>!",
            "<>",
            "<p>Hello, <style:Redaction>&lt;Person 1&gt;</style:Redaction>!</p>",
        ),
        (
            "Hello, world!",
            "Hello, [Person 1]!",
            "[]",
            "<p>Hello, <style:Redaction>[Person 1]</style:Redaction>!</p>",
        ),
        (
            "I took photos of Leopold ears.",
            "I took photos of [Subject 1]'s ears.",
            "[]",
            """<p>I took photos of <style:Redaction>[Subject 1]</style:Redaction>\
<style:RedactError>'s</style:RedactError> ears.</p>""",
        ),
        (
            """This text] [includes] [delimiters that Joe does \
not want to treat as redactions.""",
            """This text] [includes] [delimiters that [Person 1] \
does not want to treat as redactions.""",
            "[]",
            """<p>This text] [includes] [delimiters that \
<style:Redaction>[Person 1]</style:Redaction> does not want to treat \
as redactions.</p>""",
        ),
        (
            """\
Just a test narrative where there's nothing very interesting to redact.

My dog Leopold and I were walking in Golden Gate Park last night, \
near 9th Avenue and Lincoln. \
We passed a mother and her son speaking Russian together. \
Leopold really wanted to clean their ears but I wouldn't let him.
""",
            """\
Just a test narrative where there's nothing very interesting to redact.

My dog <(D1)> and I were walking in <(location)> last night, near <(location)>. \
We passed a mother and her son speaking <(language)> together. \
<(D1)> really wanted to clean their ears but I wouldn't let him.
""",
            ("<(", ")>"),
            """\
<p>Just a test narrative where there's nothing very interesting to redact.</p>\
<p></p>\
<p>My dog <style:Redaction>&lt;(D1)&gt;</style:Redaction> and I were walking in \
<style:Redaction>&lt;(location)&gt;</style:Redaction> last night, near \
<style:Redaction>&lt;(location)&gt;</style:Redaction>. \
We passed a mother and her son speaking \
<style:Redaction>&lt;(language)&gt;</style:Redaction> \
together. <style:Redaction>&lt;(D1)&gt;</style:Redaction> \
really wanted to clean their ears \
but I wouldn't let him.</p>\
""",
        ),
    ],
)
def test_format_redaction(original, redacted, delimiters, expected):
    redaction = RedactedText(redacted, original, delimiters)
    assert (
        redaction.format(
            style=_test_style,
            p=_test_graf,
            escape=escape_for_xml,
        )
        == expected
    )
