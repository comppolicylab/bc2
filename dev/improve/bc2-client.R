library(reticulate)
library(dplyr)
library(purrr)
library(tibble)
library(stringr)
library(tidyr)

dataclasses <- reticulate::import("dataclasses")

#' The local `evaluate` Python module.
evaluate <- reticulate::import("dev.evaluate")


#' Global / shared Azure Blob Storage client.
#' Use the `connect_to_az` function to set this.
#' @keywords internal
az_blob_client <- NULL


#' Global / shared Azure FormRecognizer client.
#' Use the `connect_to_az` function to set this.
#' @keywords internal
az_fr_client <- NULL


#' Ensure that the Azure clients are configured
#'
#' A sanity check to make sure client is configured before trying to use it.
#' @keywords internal
ensure_az_clients <- function() {
    if (is.null(az_blob_client)) {
        stop("No Azure Storage Client configured. Use `connect_to_az` first!")
    }
    if (is.null(az_fr_client)) {
        stop("No Azure FormRecognizer Client configured. Use `connect_to_az` first!")
    }
}


#' Connect to the Azure services.
#'
#' You can pass API keys for the Blob Storage service and the
#' Form Recognizer service directly here. If you do not, we will
#' try to pull credentials from the global config. You can generally
#' set the global authentication through the Azure Command Line tools,
#' by running the `az login` command and signing in with an account
#' that has the appropriate authorizations.
#'
#' @param blob_url The Blob Storage URL (copy from the Azure Portal).
#' @param blob_container Container name within the Blob storage.
#' @param blob_api_key The Blob storage API key, if needed.
#' @param form_endpoint The FormRecognizer account endpoint.
#' @param form_api_key The FormRecognizer API key, if needed.
#' @examples
#' connect_to_az(blob_account_url = "https://blindchargingdev.blob.core.windows.net/",
#'               blob_container = "bcdev",
#'               form_endpoint = "https://bc-formr-dev.cognitiveservices.azure.com/")
connect_to_az <- function(
    blob_account_url = "",
    blob_container = "",
    blob_api_key = "",
    form_endpoint = "",
    form_api_key = ""
) {
    az_blob_client <<- evaluate$AzureFileIO(
        account_url=blob_account_url,
        container=blob_container,
        key=blob_api_key
    )
    az_fr_client <<- evaluate$AzureModelClient(endpoint=form_endpoint, key=form_api_key)
}


#' List available documents in the given directory.
#'
#' @param base_path Directory, relative to the root of the container.
#' @param has_ocr Whether to filter for files that have been OCRed.
#' @return A tibble with document path and `has_ocr` and `has_labels` features.
#' @examples
#' list_docs(base_path = "cleveland")
list_docs <- function(base_path = "", has_ocr = TRUE) {
    ensure_az_clients()
    docs <- evaluate$list_docs(az_blob_client, base_path=base_path, ocr=has_ocr, labels=FALSE)
    if (length(docs) == 0) {
        stop("No documents found in base_path!")
    } else {
      parse_py_table(docs) %>%
          # Fix boolean columns ... there's probably a better way to do this!
          mutate(has_ocr = str_equal(has_ocr, "TRUE"),
                 has_labels = str_equal(has_labels, "TRUE"))
    }
}


#' List all models of the given type.
#'
#' @param type Either "extractor" or "classifier"
#' @return Information about all models of the requested type
list_models <- function(type) {
    ensure_az_clients()
    models <- az_fr_client$list_models(type)
    parse_py_table(models)
}


#' List the document extraction models based on the metadata we have.
#'
#' @return List of extraction model definitions.
list_extraction_models <- function() {
    list_models("extractor")
}


#' List the document classification models based on the metadata we have.
#'
#' @return List of classifier model definitions.
list_classifiers <- function() {
    list_models("classifier")
}


#' Train an extraction model with the given document names.
#'
#' @param name Name for the model (must be unique in your FormRecognizer account).
#' @param docs List of documents to use for training from the blob store.
#' @param description Optional text describing this model
#' @param tags Optional key/value tags to help identify this model
#' @return Model name
#' @examples
#' train_extraction_model("my-new-model", filter(docs, has_labels)$name)
train_extraction_model <- function(name,
                                   docs,
                                   description = "Custom extraction model",
                                   tags = NULL) {
    ensure_az_clients()
    if (az_fr_client$model_exists("extractor", name)) {
        stop(str_c("Model already exists with name ", name, "!"))
    }
    trainer <- az_fr_client$trainer(az_blob_client)
    trainer$train_extractor(name=name, docs=docs, description=description, tags=tags)
}


#' Train a classifier with the given document labels.
#'
#' @param name Name for the model (must be unique in your FormRecognizer account).
#' @param files List of document paths in the Blob Store to use for training
#' @param labels List of labels corresponding to the files list
#' @param description Optional text describing this model
#' @return Model name
#' @examples
#' train_classifier("my-new-model", docs$name, docs$label)
train_classifier <- function(name,
                             files,
                             labels,
                             description = "Custom classifier"
                            ) {
    ensure_az_clients()
    if (az_fr_client$model_exists("classifier", name)) {
        stop(str_c("Model already exists with name ", name, "!"))
    }
    trainer <- az_fr_client$trainer(az_blob_client)
    trainer$train_classifier(name=name, files=files, labels=labels, description=description)
}


#' Run a model, either classifier or extractor.
#'
#' @param type Either `classifier` or `extractor`.
#' @param model Model ID to use.
#' @param doc_or_docs Document(s) to run model on.
#' @param Tibble with results for each document.
#' @keywords internal
run_model <- function(type, model, doc_or_docs, threads = 4) {
    ensure_az_clients()
    if (!az_fr_client$model_exists(type, model)) {
        stop(str_c("No model exists with name ", model, "!"))
    }
    runner <- az_fr_client$runner(az_blob_client)
    runner$multi_run(type, model, as.list(doc_or_docs), threads=threads)
}


#' Run extraction on a set of documents.
#'
#' @param model Model definition to use.
#' @param doc_or_docs Document(s) to run extraction on.
#' @param threads Number of threads to use for loading data.
#' @return Tibble with extracted labels for each document (one per row).
#' @examples
#' run_extraction_model("my-new-model",
#'                      c("doc-num-1.pdf",
#'                        "doc-num-2.pdf"))
run_extraction_model <- function(model, doc_or_docs, threads = 4) {
    run_model("extractor", model, doc_or_docs, threads) %>%
        parse_py_labels_map
}


#' Run classifier on a set of documents.
#'
#' @param model Model definition to use.
#' @param doc_or_docs Document(s) to run classification on.
#' @param threads Number of threads to use for loading data.
#' @return Tibble with predicted label for each input document.
#' @examples
#' run_classifier("my-new-model",
#'                c("doc-num-1.pdf",
#'                  "doc-num-2.pdf"))
run_classifier <- function(model, doc_or_docs, threads = 4) {
    x <- run_model("classifier", model, doc_or_docs, threads)
    do.call(rbind, x) %>%
        as.data.frame %>%
        rownames_to_column("file") %>%
        as_tibble %>% rename(label = V1)
}


#' Load true labels for a document.
#'
#' Labels pertain to extraction models, not classifiers.
#'
#' @param doc_or_docs Document(s) to load true labels for.
#' @param threads Number of threads to use for loading data.
#' @return Tibble with true labels for documents
#' @examples
#' load_true_labels("my-labeled-doc.pdf")
load_true_labels <- function(doc_or_docs, threads = 4) {
    ensure_az_clients()
    evaluate$get_true_labels(az_blob_client, as.list(doc_or_docs), threads=threads) %>%
        parse_py_labels_map
}


#' Visualize bounding boxes on the given document.
#'
#' @param doc Document to view (as a path in the Blob storage).
#' @param ... Object(s) with a `bbox` field and optionally a `label` field.
#' @return PNG
#' @examples
#' labeled <- load_true_labels("my-labeled-doc.pdf")
#' show_bounds("my-labeled-doc.pdf", labeled[1,])
show_bounds <- function(doc, ...) {
    ensure_az_clients()

    evaluate$render_bounds(az_blob_client, doc, ...) %>%
        (base64enc::base64decode) %>%
        (png::readPNG) %>%
        (grid::grid.raster)
}


#' Convert a Python dataclass to an R vector.
#'
#' @param dc Original Python dataclass object.
#' @return Equivalent R Vector (with NAs instead of NULLs).
#' @keywords internal
py_dc_to_vector <- function(dc) {
    # Convert to sample "dict" (named list)
    tmp <- dataclasses$asdict(dc)
    tmp[sapply(tmp, is.null)] <- NA
    return(unlist(tmp))
}


#' Parse a list of Python dataclasses into a tibble.
#'
#' @param X Input table as a list of original Python dataclass objects.
#' @return Equivalent R tibble
#' @keywords internal
parse_py_table <- function(X) {
    df <- do.call(rbind, lapply(X, py_dc_to_vector))
    as_tibble(df)
}


#' Parse a labels map from Python.
#'
#' @param X Python dictionary mapping filenames to Labels.
#' @return Tibble containing all labels
#' @keywords internal
parse_py_labels_map <- function(X) {
    tbl <- do.call(rbind, lapply(X, function(x) { parse_py_table(x$flat()) })) %>%
        rownames_to_column("file")
    # Get a reasonable representation of bounding box -- not sure what's most useful.
    tbl$bbox <- lapply(tbl$bbox, function(x) { x['__repr__']() })
    tbl %>%
        unnest(c("name", "value", "bbox")) %>%
        rename(label=name,
               content=value)
}
