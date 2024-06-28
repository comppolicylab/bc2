require(tidyverse)
require(glue)
require(readxl)

base_folder <- "~/Library/CloudStorage/OneDrive-HarvardUniversity/public_police_reports/inventories"

inventory <- read_excel(glue("{base_folder}/cpl_inventory_2024-06-20.xlsx"),
                        col_types = "text")

inventory %>% 
  select(document_id) %>% 
  mutate(fixed_document_id = round(as.numeric(document_id), 3),
         fixed_document_id = as.character(fixed_document_id),
         equality = document_id == fixed_document_id,
         fixed_document_id = coalesce(fixed_document_id, document_id)) %>% 
  write_(glue("{base_folder}/floating_point_fix.csv"))
