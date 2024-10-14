# For San Francisco:
# Assume 15k cases per year
# Assume 3 pages per case
# Assume 50k pages per year (a bit above 15k * 3, at SF's request)

# Document intelligence
# ------------------------------------------------------------------------------
# Source: 
# https://azure.microsoft.com/en-us/pricing/details/ai-document-intelligence/

# Parameters:
# Region: US Gov Arizona
# Currency: USD
# Pricing: Pay as You Go
# Instance: S0 - Web/Container

# Assuming "Read" document type (current approach):
di_read_price_pp    <- 1.875 / 1000
di_annual_cost_low <- 50000 * di_read_price_pp # pages * price per page

# Assuming "Layout" document type (possible alternate approach):
di_layout_price_pp   <- 12.50 / 1000
di_annual_cost_high <- 50000 * di_layout_price_pp # pages * price per page


# Azure OpenAI
# ------------------------------------------------------------------------------
# Source: 
# https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/

# Parameters:
# Region: US Gov Arizona
# Currency: USD

# The below parameters are stats derived from the public data we've collected:
report_all_tokens  <- 400 * 3 # 400 tokens per page, 3 pages per report
report_narr_tokens <- 850 # narrative tokens per report

# The below parameter is a coarse assumption about the prompts we will use:
prompt_tokens <- 1000

# From the above, we can calculate the input/output tokens at each stage:
parse_input_tokens   <- report_all_tokens + prompt_tokens
parse_output_tokens  <- report_narr_tokens

redact_input_tokens  <- report_narr_tokens + prompt_tokens
redact_output_tokens <- report_narr_tokens

qa_input_tokens      <- report_narr_tokens + prompt_tokens
qa_output_tokens     <- report_narr_tokens

# Assuming "GPT-4o Regional API" (current approach):
gpt4o_2024_05_13_input_price_per_token  <- 6.25  / 1e6
gpt4o_2024_05_13_output_price_per_token <- 18.75 / 1e6

gpt4o_2024_05_13_annual_cost <- (
  (parse_input_tokens + redact_input_tokens + qa_input_tokens) * 
    gpt4o_2024_05_13_input_price_per_token + 
  (parse_output_tokens + redact_output_tokens + qa_output_tokens) * 
    gpt4o_2024_05_13_output_price_per_token) * 15000 # tokens * price per token * cases

# Assuming "gpt-4o-2024-08-06 Regional API" (possible alternate approach):
# This model isn't available on Azure Government yet, but has better performance.
# If prices for this model end up being anything like the listed prices 
# for Azure Commercial cloud, they will be about half the price of 
# the "GPT-4o Regional API" model we cite above.

gpt4o_2024_08_06_annual_cost <- gpt4o_2024_05_13_annual_cost / 2

# Low-cost scenario:
# DI "read" model and GPT-4o-2024-08-06:
di_annual_cost_low + gpt4o_2024_08_06_annual_cost
# 93.75 + 635.16 = 728.91

# High-cost scenario:
# DI "layout" model and GPT-4o-2024-05-13:
di_annual_cost_high + gpt4o_2024_05_13_annual_cost
# 625 + 1270.31 = 1895.31