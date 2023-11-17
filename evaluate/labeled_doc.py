from functools import cache

import python_jsonschema_objects as pjs
import requests


@cache
def get_pjs_ns(schema_url: str):
    """Get a Python JSON Schema namespace from a schema URL."""
    schema = requests.get(schema_url, verify=False).json()
    builder = pjs.ObjectBuilder(schema)
    ns = builder.build_classes()
    return ns


schema = (
    "https://schema.cognitiveservices.azure.com/formrecognizer/2021-03-01/labels.json"
)
ns = get_pjs_ns(schema)

LabeledDoc = ns.LabelsJsonSchema
