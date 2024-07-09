require(tidyverse)
require(readxl)
require(glue)
require(jsonlite)
require(askpass)

source("dev/evaluate/utils.R")

api_key        <- askpass("Enter the OpenAI API key: ")
output_folder  <- file.path(user_dir, onedrive_dir, data_dir, "labels", "redactions")
num_samples    <- 300

# Get labels 
# ------------------------------------------------------------------------------
labels <- extract_labels()


# Prepare evaluation sample 
# ------------------------------------------------------------------------------
inventory <- file.path(user_dir, onedrive_dir, data_dir,
                       inventory_dir, inventory_name) %>%
  read_excel(col_types = "text")

pages_w_narrs <- inventory %>% 
  filter(document_type == "Incident") %>% 
  add_filepaths_to_inventory() %>% 
  group_by(name_base, document_id) %>% 
  sample_n(1) %>% 
  ungroup() %>% 
  # Filter to only labeled docs
  inner_join(labels, by = "page_src_path") %>% 
  filter(!is.na(label_narr_only_page)) %>% 
  group_by(referring_agency) %>% 
  # Set weights to prioritize samples from agencies with fewer samples
  mutate(n = n(),
         max_sample = min(3, n),
         weight = max_sample / n) %>% 
  ungroup() %>% 
  sample_n(num_samples, 
           weight = weight) %>% 
  ungroup()

command_prefix <- glue("PYTHONPATH={project_path} poetry run -C {project_path}")
base_command   <- glue("{command_prefix} python dev/organize/label_redacted_pages.py")

command_input <- pages_w_narrs %>% 
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
