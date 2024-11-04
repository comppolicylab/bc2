require(tidyverse)
require(glue)
require(readxl)

source("dev/evaluate/utils.R")

inventory_name             <- "cpl_inventory_2024-07-23.xlsx"

# These next two blocks are pulled from `evaluate_parse.R`
inventory_incident_basis <- file.path(user_dir, onedrive_dir, data_dir,
                                      inventory_dir, inventory_name) %>%
  read_excel(col_types = "text") %>%
  # Drop hand-noted duplicates and PRR documents
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
  summarize(document_start = min(as.numeric(document_start)),
            document_end   = max(as.numeric(document_end)),
            .groups = "drop") %>%
  # Add filepaths for later parsing
  add_filepaths_to_inventory(cache_paths = T)

inventory_page_basis <- inventory_incident_basis %>%
  incident_to_page_crosswalk()

# This block is pulled from the extract_labels() function in `utils.R`
label_files <- tibble(
  label_filepath = list.files(path = file.path(user_dir, onedrive_dir,
                                               data_dir, label_dir),
                              pattern = "\\.pdf.labels.json$",
                              full.names = TRUE)) %>%
  mutate(label_filename = basename(label_filepath),
         page_src_name  = str_remove(label_filename, "\\.labels\\.json$"))


# Now to the new code!
unlabeled_docs_page_basis <- inventory_page_basis %>%
  left_join(label_files, by = "page_src_name",
            relationship = "one-to-many") %>%
  # filter(document_id %in% sample(.$document_id, 3)) %>%
  # filter(document_id %in% c("2023-00023303", "2324600413", "23C11342")) %>%
  # select(referring_agency_state, referring_agency, folder_name,
  #        file_name, document_id, label_filepath) %>% View()
  group_by(referring_agency_state, referring_agency, folder_name,
           file_name, document_id) %>%
  mutate(all_pages_labeled = all(!is.na(label_filepath))) %>%
  ungroup() %>%
  filter(!all_pages_labeled)

files_to_copy <- unlabeled_docs_page_basis %>%
  select(page_src_name, label_filepath) %>%
  mutate(page_src_path = glue("{user_dir}/Downloads/split_pdfs/incident/{page_src_name}")) %>%
  select(-page_src_name) %>%
  mutate(ocr_filepath = str_replace(label_filepath, "\\.labels\\.json$", ".ocr.json")) %>%
  pivot_longer(cols = c(page_src_path, ocr_filepath, label_filepath),
               names_to = "file_type", values_to = "file_path") %>%
  filter(!is.na(file_path))

file.copy(files_to_copy$file_path,
          file.path(user_dir, "Downloads", "upload_to_azure"),
          overwrite = TRUE)

# To do:
# Some reports have the same ID and seem like they should be grouped as such
# and all labeled together.
# For example, Lakewood #2324600413 has three reports listed under the same
# document ID:
# first, an incident report;
# and second, a couple other reports that are listed under the same ID,
# but which aren't clearly "attached" to the original incident report.
# We should probably assume that all of these should be labeled,
# but for now we'll skip them BECAUSE the pages for the other two reports
# aren't officially labeled as part of an "Incident" report,
# so we'll skip them in the page generation process.
# Would be good to talk this over with Muskan as well.
# The suggestion is that Muskan reviews inventory lines with the same document ID,
# and if they should be grouped together, label the overarching incident report as
# including all of the foreign pages.
# Some other issues:
# - The Lakewood sub-ID issue is probably a reflection of whihc version of the report it is,
#   we can probably assume that all Lakewood reports take on the same base ID (without a decimal)
# - Lewis County 23C9308 -- these really should all be grouped under one ID,
#   so expanding the idea of what foreign pages are
# We should probably make a flow chart about what constitutes what:
# a) a report with foreign pages (something like "this all seems like a single bundle) -- these should all have the same document_num, same document_id
# b) a compilation of reports on the same case (something like "These were just stapled together") -- these should all have diff document_nums, but same document_id

# I *think* if Muskan just re-labels the docs with foreign pages all as the same doc_num,
# that will be enough?
