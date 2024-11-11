library(tidyverse)
library(readxl)
library(glue)
library(writexl)

# Script parameters
data_directory     <- "~/Library/CloudStorage/OneDrive-HarvardUniversity/public_police_reports/inventories"
existing_file_path <- glue("{data_directory}/cpl_inventory_2024-07-29.xlsx")
new_file_path      <- glue("{data_directory}/draft_inventory.csv")
output_file_path   <- glue("{data_directory}/merged_output.xlsx")

# Import data
existing_inventory <- read_excel(existing_file_path, col_types = "text")
new_inventory      <- read_csv(new_file_path, col_types = "c")

# Join data
updated_inventory  <- existing_inventory %>%
  full_join(new_inventory, by = c("file_name", "folder_name",
                                  "referring_agency",
                                  "referring_agency_state",
                                  "file_type")) %>%
  arrange(referring_agency_state,
          referring_agency,
          folder_name,
          file_name) %>%
  mutate(fill = dense_rank(pick(referring_agency_state,
                         referring_agency,
                         folder_name,
                         file_name)),
         fill = fill %% 2,
         fixed_document_id = round(as.numeric(document_id), 3),
         fixed_document_id = as.character(fixed_document_id),
         fixed_document_id = if_else(str_sub(document_id, 1, 1) == "0",
                                     document_id, fixed_document_id),
         fixed_document_id = coalesce(fixed_document_id, document_id),
         document_id = fixed_document_id) %>%
  select(-fixed_document_id)

# Export data
updated_inventory %>%
  mutate_all(as.character) %>%
  write_xlsx(output_file_path)
