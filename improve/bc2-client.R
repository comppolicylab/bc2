library(reticulate)
library(dplyr)
library(purrr)
library(tibble)
library(stringr)

dataclasses <- reticulate::import("dataclasses")

#' The local `evaluate` Python module.
evaluate <- reticulate::import("evaluate")


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
#' Generally you should not need to worry about auth if you run `az login`
#' in your terminal prior to using this script. We will try to pull credentials
#' from the global config.
#'
#' @param blob_url The Blob Storage URL (copy from the Azure Portal).
#' @param blob_container Container name within the Blob storage.
#' @param form_endpoint The FormRecognizer account endpoint.
#' @param form_api_key The FormRecognizer API key, if needed.
#' @examples
#' connect_to_az(blob_account_url = "https://blindchargingdev.blob.core.windows.net/",
#'               blob_container = "bcdev",
#'               form_endpoint = "https://bc-formr-dev.cognitiveservices.azure.com/")
connect_to_az <- function(
    blob_account_url = "",
    blob_container = "",
    form_endpoint = "",
    form_api_key = ""
) {
    az_blob_client <<- evaluate$AzureFileIO(
        account_url="https://blindchargingdev.blob.core.windows.net/",
        container="bcdev"
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
    parse_py_table(docs) %>%
        # Fix boolean columns ... there's probably a better way to do this!
        mutate(has_ocr = str_equal(has_ocr, "TRUE"),
               has_labels = str_equal(has_labels, "TRUE"))
}


#' List the document extraction models based on the metadata we have.
#'
#' @return List of extraction model definitions.
list_extraction_models <- function() {
    ensure_az_clients()
    models <- az_fr_client$list_models()
    parse_py_table(models)
}


#' Train a model with the given document names.
#'
#' @param docs List of documents to use for training.
#' @return Model definition.
train_extraction_model <- function(name, docs) {
    # TODO
}


#' Load an existing extraction model by name.
#'
#' @param name Name of extraction model.
#' @return Model definition.
load_extraction_model <- function(name) {
    # TODO
}


#' Run extraction on a set of documents.
#'
#' @param model Model definition to use.
#' @param doc_or_docs Document or list of documents to run extraction on.
#' @return Result of running model on documents.
run_extraction_model <- function(model, doc_or_docs) {
    # TODO
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
