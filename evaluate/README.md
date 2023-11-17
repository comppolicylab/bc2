Evaluation
===

TODO(jnu): add more instructions

## Run

The whole evaluate procedure can be run with the following command:

```
poetry run python -m evaluate \
    --account https://<my-storage-instance>.blob.core.windows.net/ \
    --container <my-container> \
    --evalpath <path/in/container/for/eval/results> \
    run \
    --formrecognizer https://<my-form-recognizer>.cognitiveservices.azure.com/ \
    --formrecognizer-key <my-form-recognizer-key> \
    --k <number-of-folds> \
    --seed <random-seed-for-shuffling> \
    --docpath <path/to/labeled/documents>
```

This will split the documents in the given `docpath`, train models, evaluate them, and compute precions & recall metrics.


## Permissions (IAM)

For the storage blob access, to run the script, the user must login to Azure:

```
az login
```

and also possess the `Storage Blob Data Contributor` on the relevant Azure Storage Blob.
