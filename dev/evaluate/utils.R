
# Extract labeled narratives from Document Intelligence labels
extract_narrative <- function(label_filepath) {
  # Read the JSON file
  json_data <- fromJSON(label_filepath,
                        simplifyVector = TRUE, 
                        simplifyDataFrame = FALSE, 
                        simplifyMatrix = TRUE)
  
  # Extract labels
  # print(json_data$labels)
  labels <- json_data$labels
  
  # Initialize a list to store results
  results <- list()
  
  # Loop through each label to extract desired information
  for (label in labels) {
    if (grepl("^report_narrative", label$label)) {
      # Extract narrative number and type
      parts <- strsplit(label$label, "/")[[1]]
      narrative_num <- parts[2]
      label_type <- parts[3]
      
      # Extract label values
      label_values <- sapply(label$value, function(x) x$text)
      combined_label_value <- paste(label_values, collapse = " ")
      
      # Append to results
      results <- append(results, list(
        tibble(
          label_filepath = label_filepath,
          narrative_num = narrative_num,
          label_type = label_type,
          label_value = combined_label_value
        )
      ))
    }
  }
  
  # Combine all results into a single tibble
  final_result <- bind_rows(results)
  
  if (nrow(final_result) == 0) {
    final_result <- tibble(
      label_filepath = label_filepath,
      narrative_num = NA,
      label_type = NA,
      label_value = NA
    )
  }
  
  return(final_result)
}

remove_special_chars <- function(filename) {
  # Define a pattern for characters to keep (alphanumeric and some common symbols)
  pattern <- "[^A-Za-z0-9._-]"
  
  # Replace special characters with an underscore
  cleaned_filename <- gsub(pattern, "_", filename)
  
  return(cleaned_filename)
}

# Add filepaths for sourcing and saving documents and outputs
add_filepaths_to_inventory <- function(inventory) {
  inventory %>% 
    mutate(agency_dir           = glue("{referring_agency_state}_{referring_agency}"),
           agency_dir           = str_replace_all(agency_dir, " ", "_"),
           agency_dir           = str_to_lower(agency_dir),
           name_base            = str_c(agency_dir, folder_name, 
                                        file_name, sep = "__"),
           orig_pdf_src_path    = file.path(user_dir, onedrive_dir, data_dir, 
                                            "raw", "harvard", agency_dir, "raw",
                                            folder_name, file_name),
           document_id_safe     = remove_special_chars(document_id),
           document_out_name    = str_c(name_base, 
                                        glue("{document_id_safe}.pdf"), 
                                        sep = "__"),
           document_out_path    = file.path(cache_path, input_dir, 
                                            document_out_name)
    ) %>% 
    group_by(name_base, document_id, document_start, document_end) %>% 
    mutate(page = map2(document_start, document_end, seq)) %>%
    unnest(page) %>%
    mutate(page_str             = str_pad(page, 3, pad = 0),
           page_src_name        = str_c(name_base, 
                                        glue("pg{page_str}.pdf"), sep = "__"),
           page_out_name        = str_c(name_base, document_id_safe,
                                        glue("pg{page_str}.pdf"), sep = "__"),
           page_src_path        = file.path(user_dir, onedrive_dir, data_dir, 
                                            label_dir, page_src_name),
           page_out_path        = file.path(cache_path, input_dir,
                                            page_out_name)
    ) %>% 
    ungroup()
}
