# Make sure reticulate is installed.
# Separately, you might have to configure reticulate to use the correct version of Python
# (say, if you have `bc2` installed in a virtual environment).
# install.packages("reticulate")

# Load the interface to the `bc2.evaluate` Python library.
# This package provides R bindings for the Azure model training infrastructure.
source("bc2-client.R")

# Connect to the Azure services where the documents / models live.
# We need both the Blob Storage service and also the Form Recognizer service.
connect_to_az("https://blindchargingdev.blob.core.windows.net/",
              "bcdev",
              "https://bc-formr-dev.cognitiveservices.azure.com/",
              Sys.getenv("API_KEY_FORM_RECOGNIZER_JNU"))

## Example use of all the available functions.

# Need to install Azure CLI first
# https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-macos

# Query to find which docs are available for training in the given directory.
docs <- list_docs("autoeval")

# Query to find available document models.
models <- list_extraction_models()

# Train a model. (Takes a long time! only uncomment if you want to wait ~30mins.)
# train_extraction_model("test-from-R", 
#                        filter(docs, has_labels)$name)

# Run the model on a couple documents.
extraction <- run_extraction_model("test-from-R",
                                   c("autoeval/17-182586_Assault_Rpt_R_page_4.pdf",
                                     "autoeval/16-187153_Assault_Rpt_R_page_4.pdf"))

# Load ground-truth labeled documents.
labeled <- load_true_labels(c("autoeval/17-182586_Assault_Rpt_R_page_4.pdf",
                              "autoeval/16-187153_Assault_Rpt_R_page_4.pdf"))
