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
        b"Redacted Narrative for Race-Blind Charging\n\n\n"
        b"=== NARRATIVE ===\n"
        b"Hello, world!\n\n\n"
        b"---------------------------------------------------------------------"
        b"---------------------------------------------------------------------"
        b"--------------------"
        b"The above passages have been automatically extracted from referral "
        b"documents and automatically redacted to hide race-related "
        b"information. In rare circumstances, words or punctuation may be "
        b"automatically added to fix typos. These additions will appear in "
        b"light grey. Please report any issues to "
        b"blind_charging@hks.harvard.edu.\n\n\n"
        b"=== END OF DOCUMENT ===\n"
    )
    assert ctx.debug is True
