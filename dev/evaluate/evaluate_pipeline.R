require(tidyverse)
require(glue)
require(janitor)
require(diffmatchpatch)

# Evaluation parameters
# ------------------------------------------------------------------------------
bc2_path <- file.path("/data", "bc2")

template_folder    <- file.path("/data", "templates")
pipe_template_name <- "pipeline_bc.org_demo.toml"
pipe_template_path <- file.path(template_folder,
                                pipe_template_name)


# Set up evaluation cache
# ------------------------------------------------------------------------------
evaluation_dir         <- "evaluations/pipeline"

cache_name        <- now() %>% str_replace_all(" |:|\\.|\\-", "_")
cache_path        <- file.path("/data", evaluation_dir, cache_name)

input_dir         <- "input"
output_dir        <- "output"
dir.create(file.path(cache_path, input_dir),   recursive = TRUE)
dir.create(file.path(cache_path, output_dir), recursive = TRUE)


# Copy over sample
# ------------------------------------------------------------------------------
file.copy(list.files("/data/data/demo_pdfs/original/", full.names = TRUE),
          file.path(cache_path, input_dir),
          overwrite = TRUE)


# Prepare pipeline
# ------------------------------------------------------------------------------
# Inject the prompt below into the redact pipe
pipe_template_raw <- readLines(pipe_template_path, warn = TRUE)
pipe_template     <- paste(pipe_template_raw, collapse = "\n")

# Sys.setenv(PATH = paste("/home/alex/.local/bin", Sys.getenv("PATH"), sep = ":"))
# Sys.setenv(PATH = paste("/home/alex/.pyenv/bin", Sys.getenv("PATH"), sep = ":"))
# command_prefix <- glue("PYTHONPATH={bc2_path} poetry run -C {bc2_path}")
# base_command   <- glue("{command_prefix} python -m blind_charging_core")
base_command   <- glue("python -m blind_charging_core")

run_pipeline <- function(source_dir, source_pattern,
                         output_dir, cache_path,
                         pipe_template,
                         redact_prompt, parse_prompt,
                         suffix) {

  # Replace the placeholder with the long string
  pipe_injected <- gsub("\\{redact_prompt\\}", redact_prompt, pipe_template)
  pipe_injected <- gsub("\\{parse_prompt\\}",  parse_prompt,  pipe_injected)

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


# Run pipeline
# ------------------------------------------------------------------------------
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

redact_prompt <- glue("
Your job is to redact all race-related information in the provided text. Race-related information is any word from the following categories:
- Explicit mentions of race or ethnicity
- Close proxies for race or ethnicity, like a person's nationality or the language they speak
- People's names, nicknames, and social media handles
- Physical descriptions: ONLY hair color, hairstyle, eye color, or skin color
- Location information: Addresses, streets, intersections, zip codes, store names, restaurant names,  major landmarks, neighborhood names, city names, and police department names or abbreviations

Do NOT redact ANY other types of information, e.g., do not redact dates, objects, or colors that do not refer to a person's skin tone, or other types of entities (e.g., vehicles) not explicitly listed above.

Replace any person's name, nickname, or social media handle with a placeholder in angular brackets indicating the person's role in the incident, and a number indicating the order the person appeared in the document. For example, for the first mentioned victim, use \"[Victim 1]\". Then for the second mentioned victim, use \"[Victim 2]\". If you cannot UNIQUELY identify a person when they are mentioned, DO NOT add a number to the placeholder. E.g., \"then victim, victim, and victim reported the crime\" should become \"then [Victim], [Victim], and [Victim] reported the crime. You should redact the names, nickname, and social media handles of every single person mentioned. By the time you are done, there should be zero person names, nicknames, or social media handles remaining in the redacted text.

Be as specific as possible about a person's role (e.g., \"Officer Smith and Sergeant Doe\" should become \"[Officer 1] and [Sergeant 1]\"). As a hint, roles are often abbreviated in police reports, e.g., \"S1\" refers to \"Suspect 1\", and \"V1\" refers to \"Victim 1\". Other common roles are \"Witness\" (W), \"Accused\" (A), \"Reporting Party\" (RP), or \"Reporting Victim\" (RV). Be VERY careful not to redact a suspect as [Victim 1] or vice versa: it is extremely important to consistently identify the suspect vs. everyone else involved in the incident.

If a person's role in the incident is never mentioned, use a generic “[Man X]” or “[Woman X]” (with X indicating a number when it is appropriate to include). If no gender information is present, you can use “[Person X]” instead. If their role is explicitly mentioned alongside their name, replace everything with a bracketed placeholder, e.g., the phrase \"Victim #9 Jane Doe met (S1) John Doe and went to a party\" should become \"[Victim 9] met [Suspect 1] and went to a party\".

Make sure to redact explicit mentions of race or ethnicity, including racial slurs. Also be sure to redact any mention of a spoken language, e.g., the phrase \"I conducted the interview in English\" should become \"I conducted the interview in [Language X].\"

Other listed categories should be redacted in a similar manner, with a generic placeholder like [Street X] or [Neighborhood X] replacing the redacted text. The X represents a counter for that specific redacted concept, NOT any other associated entities. For example, e.g., the phrase \"Victim 1 (a black woman) and Victim 2 (an African-American man)\" should become \"[Victim 1] (a [Race 1] woman) and [Victim 2] (a [Race 1] man)\".

Be descriptive with the placeholders. For example, the phrase \"her Afro hair\" should become \"her [Hairstyle X]\". Make sure to capitalize the placeholder text in title case so it appears professional.

You should keep an eye out for people's nicknames and variations. For example, if \"John Doe\" appears in the list of individuals, and then \"Johnny D.\" appears in the narrative, use context to decide if \"Johnny D.\" should be redacted with the same replacement as \"John Doe.\" Or if \"ANDRE JONES\" is mentioned as suspect 1, and then later a witness says, \"'Yes, it was Andre'\" should become \"'Yes, it was [Suspect 1]'\". Sometimes nicknames can be pretty different than the original name, i.e., \"SKIPPY was later identified as Thomas Jones\" should become \"[Suspect 1] was later identified as [Suspect 1]\". Under NO circumstances should nicknames appear in their original form; they should be redacted just like normal first and last names. Also, make sure you redact names even if they are part of quote. For example, the sentence \"The witness said, 'Yes, I knew the suspect Thomas as Tommy, AKA Skipper'\" should become \"The witness said, 'Yes, I knew the suspect [Suspect 1] as [Suspect 1], AKA [Suspect 1].'\"

Other variations should be handled in similar ways. For example, if \"Safeway\" appears with abbreviation [Store 1], \"Safeway Deli\" should be redacted as \"[Store 1] Deli\". If race is represented as an abbreviation like \"W/M\" for a white male, or \"BF\" for a Black female. E.g., \"the suspect was A/M and the victim was an elderly HF\" should become \"the suspect was [a Race 1 male] and the victim was an elderly [Race 2 female].\"

Redact addresses and intersections in each of its component parts: \"123 Main St.\" should be redacted as \"[Address 1 on Street 1]\", or \"the incident occurred at Main Street and Oak Court\" should become \"the incident occurred at [Street 1] and [Street 2]\". This allows you to later reference the street specifically, e.g., you could later say \"Then [Suspect 1] escaped on [Street 1].\"

Make sure to redact location information for cities or more local jurisdictions, e.g., city names, police departments, local agency names, precinct names, and neighborhood names. You do NOT need to redact regional geographic indicators, like county or state names, since they do not give away race information; but you should redact country names, since they may indicate someone's country of origin. For example, the phrase \"CPD arrested the Brazilian suspect in Chicago and booked them in Cook County Jail in Illinois\" should become \"[Police Department 1] arrested the [Ethnicity 1] suspect in [City 1] and booked them in Cook County Jail in Illinois.\"

DO NOT CHANGE ANY characters outside of these brackets. The ONLY changes you make to the narrative should occur entirely within brackets. This means that if you want to to fix a grammatical error, the fix should occur WITHIN brackets. For example, if the original text reads \"Ms. Smith black bag went missing\", the redacted text should read \"[Person 1's] black bag went missing\", without an apostrophe. Or if the original text reads \"The car went to the house of Ms. Jones\" (with a missing period at the end of the sentence), the redacted text should read \"The car went to the house of [Person 1.]\" DO NOT translate text into English and DO NOT modify the appearance of text, e.g., by changing capitalization. Also, do not add or subtract spacing between paragraphs.

Finally, NEVER truncate the provided text; you should redact the entire block of text that was given to you. Do not remove any headers or titles in the text provided.

Take your time and triple-check your work, quality is better than moving quickly. Make sure to follow these instructions closely.

Please provide the redacted text as simple plain-text paragraphs. If you do not find any narratives, or if you are not provided with any text, return \"No narratives found.\"

Do not provide any commentary.
")

run_pipeline(input_dir, "pdf$",
             output_dir, cache_path,
             pipe_template,
             redact_prompt, parse_prompt,
             "processed")
