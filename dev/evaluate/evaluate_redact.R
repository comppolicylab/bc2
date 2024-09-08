require(tidyverse)
require(glue)
require(janitor)
require(diffmatchpatch)

# Evaluation parameters 
# ------------------------------------------------------------------------------
num_samples    <- 5
raw_narratives <- read_delim(file.path("/home", "alex", "data", 
                                       "yolo", "narratives",
                                    "Stanford_Redaction_Engine_IO_tidied.txt"),
                           delim = "|") %>% 
  clean_names() %>% 
  mutate(across(everything(), as.character),
         report_narrative = iconv(report_narrative, 
                                  from = "windows-1252", to = "UTF-8"))

bc2_path <- file.path("/home", "alex", "bc2")

template_folder           <- file.path("/home", "alex", 
                                       "blind-charging-secrets", 
                                       "dev", "templates")
redact_pipe_template_name <- "redact.hks.L3_2024-08-06.toml"
redact_pipe_template_path <- file.path(template_folder, 
                                       redact_pipe_template_name)


# Set up evaluation cache 
# ------------------------------------------------------------------------------
evaluation_dir         <- "evaluations/redaction"

cache_name        <- now() %>% str_replace_all(" |:|\\.|\\-", "_")
cache_path        <- file.path("/home", "alex", "data", 
                               "yolo", 
                               evaluation_dir, cache_name)

input_dir         <- "input"
redact_dir        <- "redacted"
assess_dir        <- "assessments"
dir.create(file.path(cache_path, input_dir),   recursive = TRUE)
dir.create(file.path(cache_path, redact_dir), recursive = TRUE)
dir.create(file.path(cache_path, assess_dir), recursive = TRUE)


# Draw sample and write to files
# ------------------------------------------------------------------------------
set.seed(cache_name %>% str_split_1("_") %>% last())
narrative_sample <- raw_narratives %>% 
  sample_n(num_samples) 

write_narrative <- function(report_narrative, case_id, ...) {
  writeLines(report_narrative, 
             paste0(file.path(cache_path, input_dir, case_id), ".txt"))
}

narrative_sample %>%
  rowwise() %>%
  pmap(write_narrative)


# Prepare pipeline 
# ------------------------------------------------------------------------------
# Inject the prompt below into the redact pipe
redact_pipe_template_raw <- readLines(redact_pipe_template_path, warn = TRUE)
redact_pipe_template     <- paste(redact_pipe_template_raw, collapse = "\n")

Sys.setenv(PATH = paste("/home/alex/.local/bin", Sys.getenv("PATH"), sep = ":"))
Sys.setenv(PATH = paste("/home/alex/.pyenv/bin", Sys.getenv("PATH"), sep = ":"))
command_prefix <- glue("PYTHONPATH={bc2_path} poetry run -C {bc2_path}")
base_command   <- glue("{command_prefix} python -m lib.blind_charging_core")

run_pipeline <- function(source_dir, source_pattern,
                         output_dir, cache_path, 
                         pipe_template, prompt, 
                         suffix) {

  # Replace the placeholder with the long string
  pipe_injected <- gsub("\\{prompt\\}", prompt, pipe_template)
  
  # Write the modified content back to the cache, to be used below
  pipe_injected_path <- file.path(cache_path, 
                                  glue("pipeline_{suffix}.toml"))
  writeLines(pipe_injected, pipe_injected_path)
    
  pipeline_input <- list.files(path = file.path(cache_path, source_dir), 
                               pattern = source_pattern, 
                               full.names = TRUE) %>% 
    tibble(src_filepath = .) %>% 
    mutate(src_filename  = basename(src_filepath),
           output_name   = glue("{src_filename}.{suffix}.txt"),
           output_path   = file.path(cache_path, output_dir, output_name),
           src_filepath  = shQuote(src_filepath),
           output_path   = shQuote(output_path),
           pipeline_path = shQuote(pipe_injected_path),
           input_arg     = glue("--input-path {src_filepath}"),
           output_arg    = glue("--output-path {output_path}"),
           args          = glue("{input_arg} {output_arg}"),
           command = glue("{base_command} {pipe_injected_path} {args}")
    )
  
  pipeline_input %>% 
    pmap(function(...) {
      args <- list(...)
      system(args$command)
    })
  
}

# run_pipeline(input_dir, "txt$", 
#              "redacted.txt", redact_dir, 
#              redact_pipe_injected_path)


# Run redaction 
# ------------------------------------------------------------------------------
redact_prompt <- glue("
Your job is to redact all race-related information in the provided text. Race-related information is any word from the following categories: 
- Explicit mentions of race or ethnicity
- Close proxies for race or ethnicity, like a person's nationality or the language they speak
- People's names, nicknames, and social media handles
- Physical descriptions: ONLY hair color, hairstyle, eye color, or skin color 
- Location information: Addresses, neighborhood names, store names, restaurant names, or major landmarks

Do NOT redact ANY other types of information, e.g., do not redact dates, objects, or colors that do not refer to a person's skin tone, or other types of entities (e.g., vehicles) not explicitly listed above.
            
Replace any person's name, nickname, or social media handle with a placeholder in angular brackets indicating the person's role in the incident, and a number indicating the order the person appeared in the document. For example, for the first mentioned victim, use \"[Victim 1]\". Then for the second mentioned victim, use \"[Victim 2]\". If you cannot UNIQUELY identify a person when they are mentioned, DO NOT add a number to the placeholder. E.g., \"then victim, victim, and victim reported the crime\" should become \"then [Victim], [Victim], and [Victim] reported the crime. You should redact the names, nickname, and social media handles of every single person mentioned. By the time you are done, there should be zero person names, nicknames, or social media handles remaining in the redacted text.

Be as specific as possible about a person's role (e.g., \"Officer Smith and Sergeant Doe\" should become \"[Officer 1] and [Sergeant 1]\"). As a hint, roles are often abbreviated in police reports, e.g., \"S1\" refers to \"Suspect 1\", and \"V1\" refers to \"Victim 1\". Other common roles are \"Witness\" (W), \"Accused\" (A), \"Reporting Party\" (RP), or \"Reporting Victim\" (RV). If a person's role in the incident is never mentioned, use a generic “[Man X]” or “[Woman X]” (with X indicating a number when it is appropriate to include). If no gender information is present, you can use “[Person X]” instead. If their role is explicitly mentioned alongside their name, replace everything with a bracketed placeholder, e.g., the phrase \"Victim #9 Jane Doe met (S1) John Doe and went to a party\" should become \"[Victim 9] met [Suspect 1] and went to a party\".

Make sure to redact explicit mentions of race or ethnicity, including racial slurs. Also be sure to redact any mention of a spoken language, e.g., the phrase \"I conducted the interview in English\" should become \"I conducted the interview in [Language X].\"

Other listed categories should be redacted in a similar manner, with a generic placeholder like [Street X] or [Neighborhood X] replacing the redacted text. The X represents a counter for that specific redacted concept, NOT any other associated entities. For example, e.g., the phrase \"Victim 1 (a black woman) and Victim 2 (an African-American man)\" should become \"[Victim 1] (a [Race 1] woman) and [Victim 2] (a [Race 1] man)\".

Be descriptive with the placeholders. For example, the phrase \"her Afro hair\" should become \"her [Hairstyle X]\". Make sure to capitalize the placeholder text in title case so it appears professional.

You should keep an eye out for nicknames and variations. For example, if \"John Doe\" appears in the list of individuals, and then \"Johnny D.\" appears in the narrative, use context to decide if \"Johnny D.\" should be redacted with the same replacement as \"John Doe.\" Or if \"ANDRE JONES\" is mentioned as suspect 1, and then later a witness says, \"'Yes, it was Andre'\" then \"Andre\" should be redacted as \"[Suspect 1]\".Similarly, if \"Safeway\" appears in the list of locations with abbreviation [Store 1], \"Safeway Deli\" should be redacted as \"[Store 1] Deli\". Finally, note that race can be represented as an abbreviation like \"W/M\" for a white male, or \"B/F\" for a Black female. E.g., \"the suspect was A/M and the victim was described as a Hispanic female\" should become \"the suspect was [a Race 1 male] and the victim was described as a [Race 2] female.\"

Make sure you redact race-related information even if it is part of quote. For example, the sentence \"The witness said, 'Yes, I knew them as as Skip or Skipper'\" should become \"The witness said, 'Yes, I knew the suspect as [Suspect 1] or [Suspect 1].'\"

For location information, represent it as its component parts: \"123 Main St.\" should be redacted as \"[Address 1 on Street 1]\". This allows you to later reference the street specifically, e.g., you could later say \"Then [Suspect 1] escaped on [Street 1].\"

DO NOT CHANGE ANY characters outside of these brackets. The ONLY changes you make to the narrative should occur entirely within brackets. This means that if you want to to fix a grammatical error, the fix should occur WITHIN brackets. For example, if the original text reads \"Ms. Smith black bag went missing\", the redacted text should read \"[Person 1's] black bag went missing\", without an apostrophe. Or if the original text reads \"The car went to the house of Ms. Jones\" (with a missing period at the end of the sentence), the redacted text should read \"The car went to the house of [Person 1.]\" DO NOT translate text into English and DO NOT modify the appearance of text, e.g., by changing capitalization. Also, do not add or subtract spacing between paragraphs. 

Finally, NEVER truncate the provided text; you should redact the entire block of text that was given to you. Do not remove any headers or titles in the text provided.

Take your time and triple-check your work, quality is better than moving quickly. Make sure to follow these instructions closely.

Please provide the redacted text as simple plain-text paragraphs. If you do not find any narratives, or if you are not provided with any text, return \"No narratives found.\" 

Do not provide any commentary.
")

run_pipeline(input_dir, "txt$", 
             redact_dir, cache_path,
             redact_pipe_template, redact_prompt,
             "redaction")


# Run diff between original and redacted narratives
# ------------------------------------------------------------------------------
load_txt_files <- function(file_dir, search_pattern,
                           strip_pattern, colname_base) {
  file_paths <- list.files(file.path(cache_path, file_dir), 
             pattern = search_pattern, 
             full.names = TRUE) 
  tibble(!!paste0(colname_base, "_filepath") := file_paths) %>% 
    mutate(!!colname_base := 
             map_chr(!!sym(paste0(colname_base, "_filepath")), 
                                    ~ paste(readLines(.), 
                                            collapse = "\n")),
           input_filename := str_remove(basename(!!sym(paste0(colname_base, "_filepath"))), 
                                       strip_pattern))
}

redact_input  <- load_txt_files(input_dir,  "\\.txt$", "\\.txt$", 
                                "redact_input")
redact_output <- load_txt_files(redact_dir, "\\.txt$", 
                                "\\.txt\\.redaction\\.txt$", 
                                "redact_output")

raw_eval <- narrative_sample %>% 
  left_join(redact_input, 
            by = c("case_id" = "input_filename")) %>%
  left_join(redact_output, 
            by = c("case_id" = "input_filename"))

raw_eval %>% 
  write_csv(file.path(cache_path, "evaluation.csv"))

diff_make_try <- function(target, current, method) {
  tryCatch(
    {
      diff_make(target, current, method)
    },
    error = function(cond) {
      message(conditionMessage(cond))
      NA_character_
    }
  )
}

evaluation <- raw_eval %>% 
  mutate(text_diff   = pmap(list(redact_input,
                                 redact_output,
                                 "lossless"),
                            diff_make_try))

evaluation %>% 
  slice(1) %>% 
  pull(text_diff)


# Run individual checks on redacted narratives
# ------------------------------------------------------------------------------
assess_names_prompt <- glue("
You will be given a police narrative that has been automatically redacted. Redactions should have been applied as generic placeholders surrounded by square brackets, i.e., replacing  \"Destiny Green\" with \"[Victim 1]\". 

Your job is to assess whether the automated redaction process missed any person's name, nickname, or social media handle. You will do so by examining whether any person's name or nickname remains unredacted in the narrative provided.

You are only assessing whether people's names, nicknames, or social media handles still appear in the redacted narrative. However, here are some important exceptions:
- It is OK if person names appear as part of a brand name, like \"Jack in the Box\" or \"Dave's Killer Bread\". 
- It is OK if the names of institutions, businesses, government entities, or locations appear in the narrative. 
- It is OK if an obviously generic name like \"Jane Doe\" or \"John Doe\" appears in the narrative---unredacted generic names should NOT be considered a failure.
- It is OK if generic placeholders appear in the narrative, like \"[Officer 3]\".

Respond with OK if there are no person names listed anywhere in the narrative.
Respond with FAIL if there are any person names listed in the narrative. If there are person names, list all the names you see in a bulleted list.

Provide your response in the following YAML format:
assessment: OK or FAIL
failures:
- name 1
- name 2
- etc.
")

run_pipeline(redact_dir, "txt$", 
             assess_dir, cache_path,
             redact_pipe_template, assess_names_prompt,
             "assess_names")


assess_race_prompt <- glue("
You will be given a police narrative that has been automatically redacted. Redactions should have been applied as generic placeholders surrounded by square brackets, i.e., replacing  \"Destiny Green\" with \"[Victim 1]\". 

Your job is to assess whether the automated redaction process missed any explicit mentions of race. You will do so by examining whether any explicit mentions of a person's race, ethnicity, nationality, or language.

It is OK if generic placeholders appear in the narrative, like \"[Race 1]\" or \"[Language 1]\".

Respond with OK if there is not mention of race, ethnicity, nationality, or language anywhere in the narrative.
Respond with FAIL if there is a mention of race, ethnicity, nationality, or language in the narrative. If there are such mentions, list them in a bulleted list.

Provide your response in the following YAML format exactly as it appears:

```yaml
assessment: OK or FAIL
failures: []
```
")

run_pipeline(redact_dir, "txt$", 
             assess_dir, cache_path,
             redact_pipe_template, assess_race_prompt,
             "assess_race")

load_txt_files(assess_dir, "\\.assess_race.txt$", "\\.txt$", "assess_race") %>% 
  mutate(assessment = str_detect(assess_race, "assessment: OK"))
