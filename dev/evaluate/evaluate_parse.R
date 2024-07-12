require(tidyverse)
require(readxl)
require(glue)
require(jsonlite)
require(diffmatchpatch)
require(qpdf)

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

num_samples   <- 100
add_full_pdfs <- TRUE

pipe_folder                <- file.path(user_dir, "Development", 
                                        "blind-charging-secrets", "iterations")
extract_pipe_template_name <- "extract_2024-07-09.toml"
extract_pipe_template_path <- file.path(pipe_folder, extract_pipe_template_name)
parse_pipe_template_name   <- "parse_2024-07-09.toml"
parse_pipe_template_path   <- file.path(pipe_folder, parse_pipe_template_name)



# Set up cache 
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
inventory <- file.path(user_dir, onedrive_dir, data_dir,
                       inventory_dir, inventory_name) %>%
  read_excel(col_types = "text")

redaction_labels <- list.files(file.path(user_dir, onedrive_dir, data_dir, 
                                      "labels", "redactions"), 
                            full.names = TRUE,
                            pattern = "*\\.txt") %>% 
  map_df(~ tibble(page_src_name = basename(.x), 
                  raw_response  = readLines(.x))) %>% 
  mutate(page_src_name = str_replace(page_src_name, "\\.txt$", ".pdf"),
         is_redacted = str_detect(raw_response, 
                                  regex("Yes", ignore_case = TRUE)))

# inventory is one row per subdocument
# master docs are by filename + document_id
# need to drop duplicates first
# then group by filename + document_id
# then filter to docs with any incident included
# then combine across subdocs to get page numbers
# then sample from that

# need separate crosswalk to go from label filename (which is orig filename + pg no)
# to filename + document_id

# Pick sample of documents from inventory, choosing from docs that are labeled
# set.seed(cache_name %>% str_split_1("_") %>% last())
# set.seed("486037")
doc_sample <- inventory %>% 
  filter(document_type == "Incident") %>% 
  add_filepaths_to_inventory(cache_paths = T) %>% 
  inner_join(redaction_labels, by = "page_src_name") %>%
  distinct(page_src_path, .keep_all = TRUE) %>%
  filter(!is_redacted) # %>%
  # group_by(name_base, document_id) %>% 
  # sample_n(1) %>% 
  # ungroup() %>% 
  # # Filter to only labeled docs
  # inner_join(labels, by = "page_src_path") %>% 
  # filter(!is.na(label_narr_and_head_page)) %>% 
  # group_by(referring_agency) %>% 
  # # Set weights to prioritize samples from agencies with fewer samples
  # mutate(n = n(),
  #        max_sample = min(3, n),
  #        weight = max_sample / n) %>% 
  # ungroup() %>% 
  # sample_n(num_samples, 
  #          weight = weight) %>% 
  # ungroup()

# Copy all PDFs into the input_dir
doc_sample %>% 
  select(page_src_path, page_save_name) %>% 
  pwalk(function(page_src_path, page_save_name) {
    file.copy(page_src_path, 
              file.path(cache_path, input_dir, page_save_name))
  })

# Copy the full PDFs into the input_dir
if (add_full_pdfs) {
  doc_sample %>% 
    select(orig_pdf_src_path, document_save_path, 
           document_start, document_end) %>% 
    pwalk(function(orig_pdf_src_path, document_save_path, 
                   document_start, document_end) {
      pdf_subset(input = orig_pdf_src_path, 
                 pages = document_start:document_end, 
                 output = document_save_path)
    })
}


# Prepare pipelines
# ------------------------------------------------------------------------------
# Simply copy over the extract pipe, since it doesn't need any modification
extract_pipe_path <- file.path(cache_path, "pipeline_extract.toml")
file.copy(extract_pipe_template_path, extract_pipe_path)

# Inject the prompt below into the parse pipe
parse_pipe_template_raw <- readLines(parse_pipe_template_path, warn = TRUE)
parse_pipe_template     <- paste(parse_pipe_template_raw, collapse = "\n")
parse_prompt            <- glue("
I am providing you with text extracted from a police report via OCR using Azure Document Intelligence. Please extract ALL freely-written text in this output, including text constituting a police narrative or statement.

A police narrative is a freely-written account of events that occurred during a criminal incident. It typically includes information such as the date, time,  location, and description of the incident, as well as the actions taken by the police officers involved. It may also include legal statements or policing jargon. They often start with \"On MMDDYY, at approximately HH:MM, I...\", or a note about body worn camera footage, e.g., \"BWC activated\". Sometimes they end with \"End of report\" or something similar.

A statement is a recounting of events written from the first person's perspective. It is often written by the victim, witness, or suspect involved in the incident. It often includes statments like \"I was doing X\" or \"He said Y\". These statements may focus on actions, discussions, and even violent events that occurred during the incident. These should include a listed author (e.g., \"Name of Person\"). They may also include line numbers at the beginning of each line, which you can try to remove. A statement can also be a \"probable cause statement\", which is very similar to a narrative. 

Make sure to extract ALL freely-written text, even if it is not explicitly labeled as a narrative or statement. 

Do not include text that seems like a boilerplate part of the police report (e.g., information that appears to be from a header or footer). ONLY include freely written text by a police officer or involved person. Also DO NOT extract long lists of labels and values (e.g., DOB, Zipcode, weight, etc.), unless they are embedded within freely-written text (occasionally a list of labels and freely-written values will be directly included as part of a narrative). When in doubt, opt to include text.

Headers are an important field to extract if it exists. It typically immediately precedes a block of freely written text. It often includes words like \"Main\", \"Primary\", \"Follow-Up\", \"Supplemental\", \"Investigative\", or \"Synposis\" to indicate the type of narrative, or \"Statement\" to indicate a witness, suspect, or victim statement, or probable cause statement. Extract the entire header, not just one of these words. Be sure to only extract this field if it exists on the page. 

Sometimes freely-written text appears without a header. You should still include these passages. For example, freely-written text can spill across multiple pages. As a result, the last few paragraphs of a long narrative may appear without any header at the top of a page. It is very important to extract these stubs so that we can merge them into a single block of text at a later time. These hanging paragraphs may be tricky to identify, especially if the page contains the start of the next block of freely-written text. So keep your eye out for pages with multiple blocks of narratives.

You may need to tweak the output to make it readble to a human. If there appear to be line numbers at the beginning of some extracted lines, remove those to make the output more readable. If it appears there are random line breaks that break up a sentence, remove those as well. 

Important: add a visual divider between each extracted passage. The divider should be a line of dashes like this: \"------------------------------------------------------\". You only need to add this line between narratives if there is more than one extracted narrative; no need to add these breaks at the beginning or end of your output.

Take your time and triple-check your work. Quality is better than moving quickly. Make sure to examine all of the provided content.

If you find one or more narratives or statements, you should return them as simple plain-text paragraphs, with the header (if it exists) followed by the narrative content. Paragraphs should be presented in the order they appeared in the input. 

If you do not find any narratives, or if you are not provided with any text, return \"No narratives found.\" 

NEVER respond with extra text that was not included in the input. Here are some scenarios you should avoid where you may be tempted to create text:
1. Some of the records you are receiving may have been partially redacted, which means there might be missing text. However, the output you receive won't say it's been redacted. There will just be words missing, or ocassionally placeholders where the redactions occurred (like a number or a legal code). It will be very tempting to fill in this missing information. However, DO NOT attempt to fill these gaps in missing text. If it seems like there are missing words, you can add \"[redacted]\" to these gaps to indicate that text seems to be missing.
2. Sometimes freely written text comes with grammatical or spelling errors, which will be very tempting to correct. Hoewever, DO NOT make any grammatical corrections or spelling fixes. 
3. Sometimes a page might present enough factual information that it will be very tempting to create an entirely new narrative from the facts provided. However, it is VERY BAD to create a narrative or statement from the listed details of an incident. NEVER do this.

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
command_prefix <- glue("PYTHONPATH={project_path} poetry run -C {project_path}")
base_command   <- glue("{command_prefix} python -m lib.blind_charging_core")

run_pipeline <- function(source_dir, source_pattern, 
                         output_suffix, output_dir, 
                         pipeline_path) {
                           
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
  
  pipeline_input %>% 
    pmap(function(...) {
      args <- list(...)
      system(args$command)
    })
  
}

run_pipeline(input_dir, "pdf$", 
             "extracted.txt", extract_dir, 
             extract_pipe_path)

run_pipeline(extract_dir, "\\.extracted\\.txt$", 
             "parsed.txt", parsed_dir, 
             parse_pipe_injected_path)


# Evaluate output
# ------------------------------------------------------------------------------
labels <- extract_labels()

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
  left_join(labels, 
            by = c("page_src_path" = "page_src_path")) %>%
  left_join(extract_output, 
            by = c("page_save_name" = "input_filename")) %>%
  left_join(parse_output, 
            by = c("page_save_name" = "input_filename")) %>% 
  left_join(parse_output, 
            by = c("document_save_name" = "input_filename"), 
            suffix = c("_page_raw", "_document_raw"))

raw_eval %>% 
  write_csv(file.path(cache_path, "evaluation.csv"))

eval <- raw_eval %>% 
  mutate(# Replace "No narratives found." with NA_character_
    parse_output_page     = str_replace(parse_output_page_raw, 
                                        "No narratives found.\\n", 
                                        NA_character_),
    parse_output_document = str_replace(parse_output_document_raw, 
                                        "No narratives found.\\n", 
                                        NA_character_),
    # Remove breaks between narratives added by prompt instructions
    parse_output_page     = str_replace_all(parse_output_page, "-{50,}", ""),
    parse_output_document = str_replace_all(parse_output_document, "-{50,}", ""),
    # Collapse multiple linebreaks to a single line break
    parse_output_page     = str_replace_all(parse_output_page, 
                                            "(\\n){2,}", 
                                            "\\\n"),
    parse_output_document = str_replace_all(parse_output_document, 
                                            "(\\n){2,}", 
                                            "\\\n"),
    # parse_output_page     = str_replace(parse_output_page, "\\n$", ""),
    # parse_output_document = str_replace(parse_output_document, "\\n$", ""),
    has_narrative         = !is.na(label_narr_only_page), 
    narrative_extracted   = !is.na(parse_output_page),
    text_diff_page        = pmap(list(label_narr_only_page,
                                      parse_output_page,
                                      "lossless"),
                                 diff_make),
    text_diff_document    = pmap(list(label_narr_only_page,
                                      parse_output_document,
                                      "lossless"),
                                 diff_make)
  )

# How many pages had a narrative extracted at all?
eval %>% 
  count(has_narrative, narrative_extracted)

# What proportion of the original labeled narrative(s) was recovered?
narr_recovery_page <- eval %>% 
  unnest(text_diff_page) %>%
  tibble() %>% 
  mutate(label_narr_only_page_length = str_length(label_narr_only_page),
         op_length = str_length(text),
         op_pct = op_length / label_narr_only_page_length) %>%
  group_by(page_save_name, parse_output_page, label_narr_only_page) %>% 
  summarize(pct_narr_recovered_page = sum(op_pct[op == "EQUAL"]),
            .groups = "drop")

narr_recovery_doc <- eval %>% 
  unnest(text_diff_document) %>%
  tibble() %>% 
  mutate(label_narr_only_page_length = str_length(label_narr_only_page),
         op_length = str_length(text),
         op_pct = op_length / label_narr_only_page_length) %>%
  group_by(page_save_name, parse_output_document, label_narr_only_page) %>% 
  summarize(pct_narr_recovered_doc = sum(op_pct[op == "EQUAL"]),
            .groups = "drop")

narr_recovery <- narr_recovery_page %>% 
  left_join(narr_recovery_doc, by = c("page_save_name",
                                      "label_narr_only_page")) %>% 
  left_join(eval %>% select(page_save_name,
                            extract_output,
                            text_diff_page, 
                            text_diff_document,
                            page_save_path,
                            document_save_path), by = "page_save_name")

narr_recovery %>% 
  summarize(num_narr_recovered_95_page = sum(pct_narr_recovered_page > 0.95),
            num_narr_recovered_95_doc = sum(pct_narr_recovered_doc   > 0.95),
            num_narr_recovered_90_page = sum(pct_narr_recovered_page > 0.9),
            num_narr_recovered_90_doc = sum(pct_narr_recovered_doc   > 0.9),
            num_narr_recovered_80_page = sum(pct_narr_recovered_page > 0.8),
            num_narr_recovered_80_doc = sum(pct_narr_recovered_doc   > 0.8),
            num_narr_recovered_50_page = sum(pct_narr_recovered_page > 0.5),
            num_narr_recovered_50_doc = sum(pct_narr_recovered_doc   > 0.5),
            num_narr_recovered_01_page = sum(pct_narr_recovered_page > 0.01),
            num_narr_recovered_01_doc = sum(pct_narr_recovered_doc   > 0.01)) %>% 
  pivot_longer(cols = everything(), 
               names_to = "metric", 
               values_to = "count")

narr_recovery %>% 
  select(label_narr_only_page, 
         extract_output,
         parse_output_page, parse_output_document,
         pct_narr_recovered_page, pct_narr_recovered_doc) %>% 
  mutate(row_numb = row_number()) %>% 
  relocate(row_numb) %>% 
  View()

examine_doc <- function(ix_num) {
  doc_deets <- narr_recovery %>% 
    slice(ix_num) 
  
  cat(glue("Extract output:\n\n"))
  doc_deets %>% 
    pull(extract_output) %>% 
    cat()
  
  cat(glue("\n\n\n\nLabeled narrative:\n\n"))
  doc_deets %>% 
    pull(label_narr_only_page) %>% 
    cat()
  
  cat(glue("\n\n\n\nExtracted from page:\n\n"))
  doc_deets %>% 
    pull(text_diff_page) %>% 
    print()
  
  cat(glue("\nExtracted from document:\n\n"))
  doc_deets %>% 
    pull(text_diff_document) %>% 
    print()
  
  doc_deets %>% 
    pull(page_save_path) %>%
    map(., ~ rstudioapi::viewer(.))
  
  doc_deets %>% 
    pull(document_save_path) %>%
    map(., ~ rstudioapi::viewer(.))
  
}

examine_doc(42)



# 246: "wi_milwaukee_pd__assaults__232520149" Check label for narrative

# To engineer:
# - Compile narratives across reports and analyze these all together
# - Compare to input to detect hallucination 
# - Something is wrong with #36 Idaho Falls 2023-00033247 -- probably b/c multiple report nums?
# - Same with #37 Idaho Falls same incident number 
# - But somehow #38 is fine, and #39

# To change:
# - Add "hallucination" metric (not extracted text)
# - Add "extra material" metric (extracted text, just not part of the label)

# Ideas for Joe:
# - Quality check vs. input at extraction step (see doc #32)
# Hallucination examples: 27, 

# Muskan re-label:
# - Recommendation letter update?
# - in_bloomington_pd__felonies__B23-51932_redacted.pdf: why label table entries as part of narrative?
# - Lewis County: remove end-matter if it is just "I DECLARE UNDER PENALTY OF PERJURY..." boilerplate
# - NV Elko CAD examples (#83-90)
# - Duluth CAD examples (#52)
# - Yakima CAD examples