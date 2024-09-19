require(tidyverse)
require(readxl)
require(glue)
require(jsonlite)
require(diffmatchpatch)
require(qpdf)
require(parallel)

source("dev/evaluate/utils.R")

# To dos:
# Cache Azure DI outputs so we can check hallucination vs. overshooting narrative
# Better handling of line breaks as non-edits (#2)
# Update prompt to discourage hallucination (#6)
# Run an automatic cost estimate for narrative extraction on the sample



# Evaluation parameters 
# ------------------------------------------------------------------------------
# 0.15 cents per page for text extraction (prebuilt-read)
# 2 cents per page for narrative extraction (if fed one page at a time)
# Ten records = about 20 cents
# 100 records = about $2

# With GPT-4 Turbo and 100 records with full PDFs, it took 1.25 hours,
# so about 45 s / record

num_samples   <- 5
add_full_pdfs <- TRUE

inventory_name             <- "cpl_inventory_2024-07-23.xlsx"

pipe_folder                <- file.path(user_dir, 
                                        "Development",
                                        "blind-charging-secrets", 
                                        "dev",
                                        "templates")
extract_pipe_template_name <- "extract.harvard_2024-07-09.toml"
extract_pipe_template_path <- file.path(pipe_folder, extract_pipe_template_name)
parse_pipe_template_name   <- "parse.harvard_2024-07-09.toml"
parse_pipe_template_path   <- file.path(pipe_folder, parse_pipe_template_name)



# Set up evaluation cache 
# ------------------------------------------------------------------------------
evaluation_dir         <- "evaluations/extraction"

cache_name        <- now() %>% str_replace_all(" |:|\\.|\\-", "_")
cache_path        <- file.path(user_dir, onedrive_dir, data_dir,
                               evaluation_dir, cache_name)

input_dir         <- "input"
extract_dir       <- "extracted"
parsed_dir        <- "parsed"
dir.create(file.path(cache_path, input_dir),   recursive = TRUE)
dir.create(file.path(cache_path, extract_dir), recursive = TRUE)
dir.create(file.path(cache_path, parsed_dir),  recursive = TRUE)


# Prepare evaluation sample 
# ------------------------------------------------------------------------------
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

pdf_labels <- extract_labels(inventory_page_basis)

set.seed(cache_name %>% str_split_1("_") %>% last())
doc_sample <- inventory_incident_basis %>% 
  mutate(doc_length = document_end - document_start) %>% filter(doc_length >= 20) %>% ### TEMP filter to long documents 
  # Filter to labeled incidents 
  inner_join(pdf_labels, by = "document_save_name") %>% 
  group_by(referring_agency) %>%
  # Set weights to prioritize samples from agencies with fewer samples
  mutate(n = n(),
         max_sample = min(3, n),
         weight = max_sample / n) %>%
  ungroup() %>%
  sample_n(num_samples,
           weight = weight) %>%
  ungroup()

# Copy the full PDFs into the input_dir
doc_sample %>% 
  select(orig_pdf_src_path, document_save_path, 
         document_start, document_end) %>% 
  pwalk(function(orig_pdf_src_path, document_save_path, 
                 document_start, document_end) {
    pdf_subset(input = orig_pdf_src_path, 
               pages = document_start:document_end, 
               output = document_save_path)
  })

# redaction_labels <- list.files(file.path(user_dir, onedrive_dir, data_dir, 
#                                          "labels", "redactions"), 
#                                full.names = TRUE,
#                                pattern = "*\\.txt") %>% 
#   map_df(~ tibble(page_src_name = basename(.x), 
#                   raw_response  = readLines(.x))) %>% 
#   mutate(page_src_name = str_replace(page_src_name, "\\.txt$", ".pdf"),
#          is_redacted   = str_detect(raw_response, 
#                                     regex("Yes", ignore_case = TRUE))) %>% 
#   left_join(inventory_page_basis, by = "page_src_name") %>% 
#   group_by(document_save_name) %>%
#   summarize(is_redacted = any(is_redacted)) %>% 
#   ungroup()


# Prepare pipelines
# ------------------------------------------------------------------------------
# Simply copy over the extract pipe, since it doesn't need any modification
extract_pipe_path <- file.path(cache_path, "pipeline_extract.toml")
file.copy(extract_pipe_template_path, extract_pipe_path)

# Inject the prompt below into the parse pipe
parse_pipe_template_raw <- readLines(parse_pipe_template_path, warn = TRUE)
parse_pipe_template     <- paste(parse_pipe_template_raw, collapse = "\n")
parse_prompt            <- glue("
I am providing you with text from a police report provided by OCR using Azure Document Intelligence. Review this input and extract ALL freely-written text from the following categories:
1. *Narratives*: A narrative is a freely-written account of events that occurred during a crime. It typically includes information such as the date, time, location, and description of the incident, as well as the actions taken by the police officers involved. It may also include legal statements or policing jargon. They often start with \"On MMDDYY, at approximately HH:MM, I...\", or a couple words about body worn camera (BWC) footage, e.g., \"BWC activated\" or \"No BWC\". Sometimes they end with \"End of report\", a certification under penalty of perjury, a recommendation, or the officer's name.
2. *Synposis*, *Summary*, or *Probable Cause*: These are like narratives. Sometimes they are 1-2 sentences long, but they can be much longer. They also give high-level details of the crime.
3. *Statements*: A statement is a recounting of events written from the first person's perspective. It is often written by the victim, witness, or suspect involved in the incident. It often includes phrases like \"I was doing X\" or \"He said Y\". Statements may focus on actions, discussions, and even violent events that occurred during the incident. These should include a listed author (e.g., \"Name of Person\"). A statement can also be a \"probable cause statement\", which is very similar to a narrative. 

Alongside this text, you should also extract headers if they exist. Headers typically immediately precede a block of freely written text. They often includes words like \"Narrative\", \"Main\", \"Primary\", \"Follow-Up\", \"Supplemental\", \"Investigative\", or \"Synposis\" to indicate the type of narrative, or \"Statement\" to indicate a witness, suspect, or victim statement, or probable cause statement. Extract the entire header, not just one of these words. Be sure to only extract this field if it exists on the page. Sometimes multiple headers are used for the same narrative; make sure to extract them all.

Sometimes freely-written text from the above categories appears without a header. You should still extract ALL freely-written text, even if it is not explicitly labeled as a narrative or statement. For example, freely-written text can spill across multiple pages. As a result, the last few sentence(s) of a long narrative may appear without any header at the top of a page. It is very important to extract these stubs so that we can merge them into a single block of text at a later time. These hanging paragraphs may be tricky to identify, especially if the page contains the start of the next block of freely-written text. So keep your eye out for pages with a hanging sentence or two.

Very often there is more than one narrative or statement in the document provided. You should return ALL narratives and statements. Be VERY careful to read through all the text provided and extract ALL narratives or statements provided without any truncation or omission. 

In the past, you often missed the last few paragraphs of the last narrative of a document. So this time, make sure to look *all the way* to the very end of the provided text, and then be sure to extract all freely written text as instructed. Here are some signs that you may have missed part of a narrative or statement:
- The extracted text ends abruptly in the middle of a sentence
- The extracted text ends without a conclusion or follow-up
- The extracted text ends without a signature or certification

Triple-check the very last line in your extracted text. Does it end in the middle of a sentence? If so, it's highly likely you missed something. Go back and extract the rest of that narrative, and look to see if any more narratives or statements follow. Be highly suspicious and skeptical if you are tempted to end your extracted text with a hanging sentence.

As a sign of how important it is to extract all the provided narratives and statements, YOU WILL BE FINED $20 if you miss part of a narrative or statement, or $50 if you miss an entire narrative or statement. Alternatively, if you perfectly extract all narratives and statements, you will receive a tip of $100.

Extracted text should be returned as simple plain-text paragraphs, with the header (if it exists) followed by the narrative content. Paragraphs should be presented in the order they appeared in the input. Add a visual divider between each extracted narrative. The divider should be a line of dashes like this: \"------------------------------------------------------\". You only need to add this line between narratives if there is more than one extracted narrative. There is also no need to add these breaks at the very beginning or very end of your output.

If you do not find any narratives, return \"No narratives found.\" If you are not provided with any text, return \"No text provided.\"

NEVER include text from the following categories:
1. Do NOT extract lists of labels and values (e.g., DOB, Zipcode, weight, etc.), unless they are embedded within freely-written text. One exception: occasionally a list of labels and freely-written values will be part of a larger narrative, so you can extract these.
2. Do NOT extract text that seems like a boilerplate part of the police report (e.g., information from a page header or page footer). ONLY include freely written text by a police officer or involved person. 
3. Do NOT extract \"CAD Narratives\", which are sometimes labeled as such. You can also recognize CAD narratives as long lists of timestamps and very short notes about actions. 

When in doubt, opt to include text.

You may need to tweak the output to make it readable to a human. If there appear to be line numbers at the beginning of some extracted lines, remove those to make the output more readable. If it appears there are random line breaks that break up a sentence, remove those as well. Remove page footers or headers that appear to interrupt a multi-page narrative.

Take your time and triple-check your work. Quality is better than moving quickly. Make sure to examine all of the provided content.

IMPORTANT: NEVER EVER add to or modify the text that was provided as input. Here are some scenarios you should avoid where you may be tempted to edit text:
1. Some of the records you are receiving may have been partially redacted, which means there might be missing text. However, the output you receive won't say it's been redacted. There will just be words missing, or ocassionally placeholders where the redactions occurred (like a number or a legal code). It will be very tempting to fill in this missing information. However, DO NOT attempt to fill these gaps in missing text. If it seems like there are missing words, you can add \"[redacted]\" to these gaps to indicate that text seems to be missing.
2. Sometimes the input will include grammatical or spelling errors, which will be extremely tempting to correct. For example, you might see text riddled with errors, like \"his sisters store spended $ 4,000\" or \"they went to hous to git ( 3) foods\". DO NOT correct these mistakes or fix any spelling errors in the text you extract. Leave it be.
3. Sometimes a page might present enough factual information that it will be very tempting to create an entirely new narrative from the facts provided. However, it is VERY VERY BAD to create a narrative or statement from the listed details of an incident. NEVER do this.

In other words, ONLY respond with text that was included in the input, and nothing more.

Do not provide any commentary.
")

# Replace the placeholder with the long string
parse_pipe_injected <- gsub("\\{prompt\\}", parse_prompt, parse_pipe_template)

# Write the modified content back to the cache, to be used below
parse_pipe_injected_path <- file.path(cache_path, "pipeline_parse.toml")
writeLines(parse_pipe_injected, parse_pipe_injected_path)


# Run pipelines
# ------------------------------------------------------------------------------
# Run pipeline to extract narrative on sample of documents
# And cache these results 
# export PATH="/home/stfdusr1/.local/bin/:$PATH"; \
command_prefix <- glue('PYTHONPATH={project_path} poetry run -C {project_path}')
base_command   <- glue("{command_prefix} python -m lib.blind_charging_core")

run_pipeline <- function(source_dir, source_pattern, 
                         output_suffix, output_dir, 
                         pipeline_path,
                         n_cores = 1) {
                           
  pipeline_input <- list.files(path = file.path(cache_path, source_dir), 
                               pattern = source_pattern, 
                               full.names = TRUE) %>% 
    tibble(src_filepath = .) %>% 
    mutate(src_filename  = basename(src_filepath),
           output_name   = glue("{src_filename}.{output_suffix}"),
           output_path   = file.path(cache_path, output_dir, output_name),
           src_filepath  = shQuote(src_filepath),
           output_path   = shQuote(output_path),
           pipeline_path = shQuote(pipeline_path),
           input_arg     = glue("--input-path {src_filepath}"),
           output_arg    = glue("--output-path {output_path}"),
           args          = glue("{input_arg} {output_arg}"),
           command = glue("{base_command} {pipeline_path} {args}")
           )
  
  if (n_cores == 1) {
    pipeline_input %>% 
      pmap(function(...) {
        args <- list(...)
        system(args$command)
      })
  } else {
    # Use mclapply from the parallel package for parallel processing
    mclapply(1:nrow(pipeline_input), function(i) {
      args <- pipeline_input[i, ]
      system(args$command)
    }, mc.cores = n_cores) # Specify the number of cores to use
  }
  
}

pyenv_shims <- path.expand("~/.pyenv/shims")
poetry_path <- path.expand("~/.local/bin/")
Sys.setenv(PATH = paste(pyenv_shims, poetry_path, Sys.getenv("PATH"),
                        sep=":"))

system('echo $PATH')
system('python --version')
system('poetry --version')

run_pipeline(input_dir, "pdf$", 
             "extracted.txt", extract_dir, 
             extract_pipe_path,
             n_cores = 5)

run_pipeline(extract_dir, "\\.extracted\\.txt$", 
             "parsed.txt", parsed_dir, 
             parse_pipe_injected_path,
             n_cores = 5)


# Evaluate output
# ------------------------------------------------------------------------------
extract_output <- list.files(file.path(cache_path, extract_dir), 
                             pattern = "\\.txt$", 
                             full.names = TRUE) %>%  
  tibble(extract_output_filepath = .) %>% 
  mutate(extract_output = map_chr(extract_output_filepath, 
                                  ~ paste(readLines(.), 
                                          collapse = "\n")),
         input_filename = str_remove(basename(extract_output_filepath), 
                                     "\\.extracted\\.txt$"))

parse_output <- list.files(file.path(cache_path, parsed_dir), 
                           pattern = "\\.txt$", 
                           full.names = TRUE) %>%  
  tibble(parse_output_filepath = .) %>% 
  mutate(parse_output = map_chr(parse_output_filepath, 
                                ~ paste(readLines(.), 
                                        collapse = "\n")),
         input_filename = str_remove(basename(parse_output_filepath), 
                                     "\\.extracted\\.txt\\.parsed\\.txt$"))

raw_eval <- doc_sample %>% 
  left_join(extract_output, 
            by = c("document_save_name" = "input_filename")) %>%
  left_join(parse_output, 
            by = c("document_save_name" = "input_filename"))

raw_eval %>% 
  write_csv(file.path(cache_path, "evaluation.csv"))

evaluation <- raw_eval %>% 
  mutate(
    # Replace "No narratives found." with NA_character_
    parse_output_raw      = parse_output,
    parse_output          = str_replace(parse_output_raw, 
                                        "No narratives found.\\n", 
                                        NA_character_),
    # Remove breaks between narratives added by prompt instructions
    parse_output          = str_replace_all(parse_output, "-{50,}", ""),
    # Collapse multiple linebreaks to a single line break
    parse_output          = str_replace_all(parse_output, 
                                            "(\\n){2,}", 
                                            "\\\n"),
    # parse_output         = str_replace(parse_output, "\\n$", ""),
    has_narrative         = !is.na(label_narr_only_document), 
    narrative_extracted   = !is.na(parse_output),
    text_diff_narr_only   = pmap(list(label_narr_only_document,
                                      parse_output,
                                      "lossless"),
                                 diff_make_try),
    text_diff_narr_head   = pmap(list(label_narr_and_head_document,
                                      parse_output,
                                      "lossless"),
                                 diff_make_try)
    
  )

# How many pages had a narrative extracted at all?
evaluation %>% 
  count(has_narrative, narrative_extracted)

# What proportion of the original labeled narrative(s) was recovered?
narr_recovery <- evaluation %>% 
  unnest(text_diff_narr_only) %>%
  tibble() %>% 
  mutate(label_narr_only_document_length = str_length(label_narr_only_document),
         op_length = str_length(text),
         op_pct = op_length / label_narr_only_document_length) %>%
  group_by(document_save_name, parse_output, label_narr_only_document) %>% 
  summarize(pct_narr_recovered_doc = sum(op_pct[op == "EQUAL"]),
            .groups = "drop") %>% 
  left_join(evaluation %>% select(-parse_output, 
                            -label_narr_only_document),
            by = "document_save_name")

narr_recovery %>% 
  filter(!is.na(pct_narr_recovered_doc)) %>%
  summarize(num_narr_recovered_95_doc = sum(pct_narr_recovered_doc > 0.95),
            num_narr_recovered_90_doc = sum(pct_narr_recovered_doc > 0.9),
            num_narr_recovered_80_doc = sum(pct_narr_recovered_doc > 0.8),
            num_narr_recovered_50_doc = sum(pct_narr_recovered_doc > 0.5),
            num_narr_recovered_01_doc = sum(pct_narr_recovered_doc > 0.01)) %>% 
  pivot_longer(cols = everything(), 
               names_to = "metric", 
               values_to = "count")

narr_recovery %>% 
  select(label_narr_only_document, 
         extract_output, parse_output,
         pct_narr_recovered_doc) %>% 
  mutate(row_numb = row_number()) %>% 
  relocate(row_numb) %>% 
  View()

# Create a log for notetaking
narr_recovery %>% 
  select(label_narr_only_document, 
         extract_output, parse_output,
         pct_narr_recovered_doc) %>% 
  mutate(row_numb = row_number()) %>% 
  relocate(row_numb) %>% 
  write_csv(file.path(cache_path, "notes.csv"))

examine_doc <- function(ix_num) {
  doc_deets <- narr_recovery %>% 
    slice(ix_num) 
  
  cat(glue("Extract output:\n\n"))
  doc_deets %>% 
    pull(extract_output) %>% 
    cat()
  
  cat(glue("\n\n\n\nLabeled narrative:\n\n"))
  doc_deets %>% 
    pull(label_narr_and_head_document) %>% 
    cat()
  
  cat(glue("\n\n\nParsed from extract:\n\n"))
  doc_deets %>% 
    pull(text_diff_narr_head) %>% 
    print()
  
  doc_deets %>% 
    pull(document_save_path) %>%
    map(., ~ rstudioapi::viewer(.))
  
}

examine_doc(1)


