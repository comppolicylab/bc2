import io
from unittest.mock import patch

import pytest

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
    opts = {
        "debug": True,
        "in": {
            "buffer": in_buf,
        },
        "out": {
            "buffer": out_buf,
        },
    }
    pipe.validate(opts)

    ctx = pipe.run(opts)

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

    opts = {
        "debug": True,
        "in": {
            "buffer": in_buf,
        },
        "out": {
            "buffer": out_buf,
        },
    }

    # TODO pipe.validate(opts)

    ctx = pipe.run(opts)

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


@patch(
    "bc2.core.inspect.quality.InspectQualityDriver.__call__",
    side_effect=Exception("whoops!"),
)
def test_pipeline_optional_step(_mock):
    cfg = PipelineConfig.model_validate(
        {
            "pipe": [
                {"engine": "in:memory"},
                {"engine": "extract:raw"},
                {"engine": "redact:noop", "delimiters": ["[", "]"]},
                {"engine": "inspect:quality"},  # default is optional=True
                {"engine": "render:text"},
                {"engine": "out:memory"},
            ],
        }
    )

    # Run the pipeline.
    pipe = Pipeline(cfg)

    in_buf = io.BytesIO(b"Hello, with error!")
    out_buf = io.BytesIO()
    opts = {
        "debug": True,
        "in": {
            "buffer": in_buf,
        },
        "out": {
            "buffer": out_buf,
        },
    }

    # TODO pipe.validate(opts)
    ctx = pipe.run(opts)

    assert len(ctx.errors) == 1
    assert isinstance(ctx.errors[0], Exception)
    assert str(ctx.errors[0]) == "whoops!"
    assert out_buf.getvalue() == (
        b"=== Redacted Narrative for Race-Blind Charging ===\n\n\n"
        b"Hello, with error!\n\n\n"
        b"-------------------------------------------------------\n"
        b"The above passages were automatically extracted from referral "
        b"documents and automatically redacted to hide race-related "
        b"information. Occasionally, words or punctuation may be "
        b"automatically added to fix typos. Please report any issues at "
        b"https://bit.ly/report-rbc-bug."
    )


@patch(
    "bc2.core.inspect.quality.InspectQualityDriver.__call__",
    side_effect=Exception("whoops!"),
)
def test_pipeline_nonoptional_step(_mock):
    cfg = PipelineConfig.model_validate(
        {
            "pipe": [
                {"engine": "in:memory"},
                {"engine": "extract:raw"},
                {"engine": "redact:noop", "delimiters": ["[", "]"]},
                {"engine": "inspect:quality", "optional": False},
                {"engine": "render:text"},
                {"engine": "out:memory"},
            ],
        }
    )

    # Run the pipeline.
    pipe = Pipeline(cfg)

    in_buf = io.BytesIO(b"Hello, with error!")
    out_buf = io.BytesIO()

    with pytest.raises(Exception) as excinfo:
        pipe.run(
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
    assert str(excinfo.value) == "whoops!"


def test_pipeline_invalid_optional_step():
    cfg = PipelineConfig.model_validate(
        {
            "pipe": [
                {"engine": "in:memory"},
                {"engine": "extract:raw"},
                {"engine": "redact:noop", "delimiters": ["[", "]"]},
                {"engine": "inspect:quality"},
                {"engine": "render:text"},
                {"engine": "out:memory"},
            ],
        }
    )
    object.__setattr__(cfg.pipe[1], "optional", True)

    # Run the pipeline.
    pipe = Pipeline(cfg)
    in_buf = io.BytesIO(b"Hello, with error!")
    out_buf = io.BytesIO()
    with pytest.raises(ValueError) as excinfo:
        pipe.validate(
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
    assert str(excinfo.value) == (
        "Step [1] `extract:raw` is marked optional, but the input type "
        "<class 'bc2.core.common.file.MemoryFile'> is not compatible with "
        "the output type <class 'bc2.core.common.text.Text'>."
    )
