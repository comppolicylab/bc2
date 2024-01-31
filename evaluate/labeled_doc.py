from functools import cache

import python_jsonschema_objects as pjs
import requests


@cache
def get_pjs_ns(schema_url: str):
    """Get a Python JSON Schema namespace from a schema URL."""
    schema = requests.get(schema_url, verify=False).json()

    # XXX(jnu): apparently the schema changed?? or is wrong??
    # This ugly hack is required all of a sudden to make my documents parse...
    # The error is that the value is not a json-pointer, but
    # the schema expects it to be ?????
    # NOTE that there's a good chance the schema changed and new files that
    # are created will not work with this hack ...
    schema["definitions"]["Label"]["properties"]["label"].pop("format")
    builder = pjs.ObjectBuilder(schema)
    ns = builder.build_classes()
    return ns


schema = (
    "https://schema.cognitiveservices.azure.com/formrecognizer/2021-03-01/labels.json"
)
ns = get_pjs_ns(schema)

LabeledDoc = ns.LabelsJsonSchema
