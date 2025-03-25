import io

from .pipeline import Pipeline, PipelineConfig


def test_pipeline_simple_debug():
    cfg = PipelineConfig.model_validate(
        {
            "pipe": [
                {"engine": "in:memory"},
                {"engine": "extract:raw"},
                {"engine": "redact:noop", "delimiters": ["[", "]"]},
                {"engine": "render:text"},
                {"engine": "out:memory"},
            ],
        }
    )
    # Run the pipeline.
    pipe = Pipeline(cfg)

    in_buf = io.BytesIO(b"Hello, world!")
    out_buf = io.BytesIO()

    ctx = pipe.run(
        {
            "debug": True,
            "in": {
                "buffer": in_buf,
            },
            "out": {
                "buffer": out_buf,
            },
        }
    )

    assert out_buf.getvalue() == (
        b"=== Redacted Narrative for Race-Blind Charging ===\n\n\n"
        b"Hello, world!\n\n\n"
        b"-------------------------------------------------------\n"
        b"The above passages were automatically extracted from referral "
        b"documents and automatically redacted to hide race-related "
        b"information. Occasionally, words or punctuation may be "
        b"automatically added to fix typos. Please report any issues at "
        b"https://bit.ly/report-rbc-bug."
    )
    assert ctx.debug is True


def test_pipeline_chunk():
    cfg = PipelineConfig.model_validate(
        {
            "pipe": [
                {"engine": "in:memory"},
                {"engine": "extract:raw"},
                {
                    "engine": "$chunk",
                    "processor": {"engine": "redact:noop", "delimiters": ["[", "]"]},
                },
                {"engine": "render:text"},
                {"engine": "out:memory"},
            ],
        }
    )

    # Run the pipeline.
    pipe = Pipeline(cfg)

    in_buf = io.BytesIO(b"Hello, world!")
    out_buf = io.BytesIO()

    ctx = pipe.run(
        {
            "debug": True,
            "in": {
                "buffer": in_buf,
            },
            "out": {
                "buffer": out_buf,
            },
        }
    )

    assert out_buf.getvalue() == (
        b"=== Redacted Narrative for Race-Blind Charging ===\n\n\n"
        b"Hello, world!\n\n\n"
        b"-------------------------------------------------------\n"
        b"The above passages were automatically extracted from referral "
        b"documents and automatically redacted to hide race-related "
        b"information. Occasionally, words or punctuation may be "
        b"automatically added to fix typos. Please report any issues at "
        b"https://bit.ly/report-rbc-bug."
    )
    assert ctx.debug is True
