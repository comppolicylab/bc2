BC2
===

Race-blind charging redaction library.


## Overview

This Python library provides tools for race-blind redaction of charging documents.

The library is generally intended to work with the `blind-charging-api` project,
but can be used as a stand-alone redaction library as well.

### Pre-requisites

While the modular design of this library means there are no strict dependencies,
the quality of redaction almost entirely depends on the quality of models you choose to use.

In particular we recommend setting up the following services:
 - **Azure Document Intelligence**. The built-in `prebuilt-read` model works reasonably well for extracting data from PDFs.
 - **OpenAI**. `GPT-4o` provides a good balance of performance, quality, and cost for parsing, redacting, and analyzing documents. It is also available on Azure GovCloud via the Azure OpenAI service.


### Design

This library implements redaction as a `Pipeline` of sequential operations.
Each step of the redaction is modular and can be implemented with different backends.
Some steps can be omitted entirely.

The basic concept looks like this:

```
Input -> Extract -> Parse -> Redact -> Inspect -> Render -> Output
```

#### Pipeline operations
- **Input**: Read a document from some source, such as `stdin`, `file`, `azureblob`, or `memory`. The document at this point is a binary blob.
- **Extract**: Extracts content from the input document. This is an important pre-processing step and generally does _not_ produce a human-readable output. We recommend using Azure DI for this step. After extraction, the document is represented as a textual blob.
- **Parse**: Parsing cleans the extracted text and distills it into a text object for redaction. We consider the text produced from this step as the "original" text that we need to redact. OpenAI's `gpt-4o` model with our built-in `parse` prompt does a good job at this step.
- **Redact**: Redaction is the process of removing sensitive information from the text and replacing it with convenient placeholders. OpenAI's `gpt-4o` model with our built-in `redact` prompt provides quality redactions.
- **Inspect**: Inspection modules don't alter the input at all, but perform some sort of analysis on the redacted text. These steps are optional, but provide important information about the redaction process. For example, the `quality` module will compute some statistics about redaction quality which can be used to reject redactions that appear incorrect or of low quality. Other inspection modules, such as `placeholders`, produce structured informationa about the redactions, which can in turn be fed back into future redaction runs to improve the quality of redactions. (For example, to keep placeholders consistent across multiple documents.)
- **Render**: Rendering will conver the redacted document into a presentable format. We implement multiple rendering backends, such as `text`, `html`, `pdf`, and `json`.
- **Output**: Write the redacted document to some output, such as `stdout`, `file`, `azureblob`, or `memory`.


## Usage

### Pipeline definition

Pipelines can either be defined in code (as Python object) or inflated from a `dict`.
(This `dict` can itself be serialized in any format you like, such as JSON, YAML, or TOML).

For example:

```py
from bc2 import Pipeline

pipe = Pipeline.create([
    {"engine": "in:file"},
    {"engine": "extract:azuredi", ...},
    {"engine": "parse:openai", ...},
    {"engine": "redact:openai", ...},
    {"engine": "render:html"},
    {"engine": "out:file"},
])
```

We expect in most cases the pipeline configuration will be somewhat immutable.
That is, you will usually define one pipeline configuration suitable to your use case that will be hard-coded into your app.

Many of the parameters for modules will be secrets, such as an OpenAI access key.
It often makes sense to treat the entire pipeline config as a secret and store it appropriately.

### Running the pipeline

The pipeline is additionally parameterized by a runtime configuration.
These are the parameters that are likely to change between runs, such as the input document, output destination, placeholders to use, etc.

For example:

```py
result = pipe.run({
    "in": {
        "path": "file://path/to/document.pdf",
    },
    "out": {
        "path": "file://path/to/redacted.html",
    },
})
```

The output of the pipeline is the `Context` object that accumulates various pieces of information throughout the run.

The specific type of this object depends entirely on the pipeline configuration.

Most commonly, results from the `inspect` modules will be stored here.
For example, if you use the `inspect:quality` module, `context.quality` will contain those results.

#### Validation

The pipeline will validate correctness before it runs.
If you have strung together incompatible modules, the pipeline will raise an exception before running.

#### Error handling

Certain modules will attempt retries on failure,
until finally raising an exception if the operation cannot be completed.
See module documentation to know what to expect.

## Advanced concepts

### Chunking

Many LLMs have a limit on the number of tokens they can process or produce at once.

To work around these limitations, you will need to express a chunking strategy in your pipeline.

We have built-in support for the most common case, where the output token limit of a model is exceeded.

To use this, configure the problem step (`parse` or `redact` or both) with a `$chunk` module:

```py
pipe = Pipeline.create([
    ...,
    {
        "engine": "$chunk",
        "max_iterations": 5,
        "processor": {
            "engine": "parse:openai",
            ...
        },
    },
    ...,
])
```

You might also find the `$compose` module useful,
especially for the `redact` step which requires placeholder inference after each chunk in order to produce consistent results between runs.
