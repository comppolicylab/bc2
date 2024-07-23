require(tidyverse)
require(readxl)
require(glue)
require(jsonlite)
require(askpass)

source("dev/evaluate/utils.R")

api_key        <- askpass("Enter the OpenAI API key: ")
output_folder  <- file.path(user_dir, onedrive_dir, data_dir, "labels", "redactions")
num_samples    <- 400

# Get labels 
# ------------------------------------------------------------------------------
inventory_incident_basis <- file.path(user_dir, onedrive_dir, data_dir,
                                      inventory_dir, inventory_name) %>%
  read_excel(col_types = "text") %>% 
  # Drop hand-noted duplicates and PRR douments
  filter(duplicate_notes != "Ignore" | is.na(duplicate_notes),
         document_type != "PRR Document") %>% 
  # For Muskan to fix: doc_num should be consistent across a doc
  # Fix document ID for now to represent documents
  mutate(document_id = str_remove(document_id, "(\\-|\\.|/)\\d{0,2}$")) %>%
  # Group by original document + document ID (should be document_num after fix)
  group_by(referring_agency_state, referring_agency, folder_name, file_name, 
           document_id) %>% 
  # Filter to documents that include at least one incident
  filter(any(document_type == "Incident")) %>% 
  # Combine across subdocuments to get page numbers
  summarize(document_start = min(document_start),
            document_end   = max(document_end),
            .groups = "drop") %>%
  # Add filepaths for later parsing
  add_filepaths_to_inventory(cache_paths = T) 

inventory_page_basis <- inventory_incident_basis %>% 
  incident_to_page_crosswalk()

labels <- extract_labels(inventory_page_basis)



# Prepare evaluation sample 
# ------------------------------------------------------------------------------
set.seed(2024)
documents_w_labeled_narratives <- inventory_incident_basis %>% 
  # Filter to labeled incidents 
  inner_join(labels, by = "document_save_name") %>% 
  # Filter to incidents with narratives 
  filter(!is.na(label_narr_only_document)) %>% 
  group_by(referring_agency) %>%
  # Set weights to prioritize samples from agencies with fewer samples
  mutate(n = n(),
         max_sample = min(3, n),
         weight = max_sample / n) %>%
  ungroup() %>%
  sample_n(num_samples,
           weight = weight) %>%
  ungroup()

pages_in_labeled_documents_w_narratives <- documents_w_labeled_narratives %>% 
  left_join(inventory_page_basis %>% select(document_save_name,
                                            page_src_path), by = "document_save_name",
            relationship = "one-to-many") 

command_prefix <- glue("PYTHONPATH={project_path} poetry run -C {project_path}")
base_command   <- glue("{command_prefix} python dev/organize/label_redacted_pages.py")

command_input <- pages_in_labeled_documents_w_narratives %>% 
  mutate(api_key_arg = glue("--api_key {api_key}"),
         src_arg     = glue("--input_pdf {shQuote(page_src_path)}"),
         out_arg     = glue("--output_folder {output_folder}"),
         args        = glue("{api_key_arg} {src_arg} {out_arg} --copy_pdf"),
         command     = glue("{base_command} {args}")
  )

command_input %>% 
  pmap(function(...) {
    args <- list(...)
    system(args$command)
  })
