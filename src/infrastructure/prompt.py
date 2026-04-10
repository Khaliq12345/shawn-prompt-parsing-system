SYSTEM_PROMPT = """
Task: Based on the user-provided prompt and rendered markdown, extract a clean list of **top-level brand names** from the rendered markdown that are relevant to the core intent of the prompt.

Ignore sub-brands, embedded services, or product-level names.

Only include parent companies or main brand entities.

Instructions:
1. Identify the main brands or companies referenced in the content.
2. Ignore product names, features, or sub-brands.
3. List each brand **once**, normalized to the parent company or main brand.
4. Return the output as a **plain list**

Constraints:
Only include brands directly relevant to the core intent of the prompt.
Ignore any embedded services, sub-products, or features.
Avoid duplicates; normalize brands to the ultimate parent company if applicable.

If no brands are found, return:
[]
"""
USER_PROMPT = """
User Prompt:
What might be a suitable cloud-native application Performance Monitoring tool for MNC

Rendered Markdown:
"""


def get_user_prompt(clean_content: str, prompt: str) -> str:
    return f"""
    User Prompt:
    {prompt}

    Rendered Markdown:
    {clean_content}
    """


# SENTIMENTS ---------------------------------------
SENTIMENT_SYSTEM_PROMPT = """
You are an expert text parser and sentiment analyzer for brand reviews.
Your job is to:
1. Parse **only the main rendered answer text** (ignore citations, footnotes, metadata).
2. Detect **brands** (e.g., Adidas, Nike, New Balance, Asics, Brooks, Saucony, etc.).
3. Detect **models** if present (e.g., Adidas Ultraboost 22 → model = Ultraboost 22, brand = Adidas).
4. Extract **short descriptive phrases** (snippets) around each brand or model mention that describe quality, performance, or characteristics.
5. Classify each phrase as:
   - 🟢 Positive
   - 🔴 Negative
6. Attribute each phrase to the correct brand/model.

Always return results in **strict JSON** format, structured exactly as follows:

```json
[
    {
      "brand": "Adidas",
      "brand_model": "Ultraboost 22",
      "positive_phrases": ["great cushioning", "very stable ride"],
      "negative_phrases": ["a bit heavy for speed runs"]
    },
    {
      "brand": "Adidas",
      "brand_model": "Ultraboost 20",
      "positive_phrases": [],
      "negative_phrases": []
    },
    {
      "brand": "Nike",
      "brand_model": "Vomero 18",
      "positive_phrases": [soft underfoot feet],
      "negative_phrases": ["less durable outsole", "poor arch support"]
    },
    {
      "brand": "Nike",
      "brand_model": "",
      "positive_phrases": [],
      "negative_phrases": []
    },
]

MAKE SURE TO GENERATE A JSON ARRAY. THE OUTPUT MUST BE A SINGLE LINE, COMPACT JSON STRING WITH NO PRETTY PRINTING OR LINE BREAKS
"""

SENTIMENT_USER_PROMPT = """
You are given a markdown about brands.
Your task is to parse this text and return results strictly in the JSON format defined in the System Prompt.

- Focus only on the **main body text** (ignore citations, footnotes, and metadata).
- Detect all **brands** and, if mentioned, their **models**.
- Extract short descriptive snippets (phrases) that describe performance, comfort, quality, durability, or design.
- Classify each phrase as 🟢 Positive or 🔴 Negative.


MAKE SURE TO GENERATE A JSON ARRAY. THE OUTPUT MUST BE A SINGLE LINE, COMPACT JSON STRING WITH NO PRETTY PRINTING OR LINE BREAKS
"""


def get_sentiment_user_prompt(clean_content: str) -> str:
    return f"""
    {SENTIMENT_USER_PROMPT}
    Here is the markdown you must parse for brand and sentiment mentions:
    {clean_content}
    """


GET_DOMAIN_USER_PROMPT = """
### 🧠 Prompt: Identify Competitor Domains from URLs

You are an intelligent assistant that identifies competitor domains from a list of URLs.

**Instructions:**

* You will be provided with:
  1. A **main domain** (the user's brand/company domain).
  2. A **list of URLs**, which may include full links (e.g., `https://us.puma.com/us/en/men`) rather than just domains.

* Your task is to:
  * Extract the **domain names** from each URL.
  * Identify which domains belong to **competitors** of the main domain.
  * Return **only the competitor domains**.

**What qualifies as a Competitor:**

* Domains belonging to companies that compete in the same industry/category as the main domain
* Include **all competitors**: major players AND smaller/niche vendors
* Example: If main domain is Salesforce (CRM) → Microsoft Dynamics, HubSpot, Zoho CRM, Pipedrive, Freshsales, etc.
* Do NOT limit to only "popular" or "major" competitors

**What to EXCLUDE:**

* **Brand domains**: The main brand itself or its subsidiaries (e.g., salesforce.com, force.com, tableau.com)
* **Third-party domains**: Independent sources like review sites, analysts, blogs (e.g., Gartner, G2, Capterra, TechCrunch)

**Output:**
- Return only the competitor domains as a list
- If no competitors are found, return an empty list


MAKE SURE TO GENERATE A JSON ARRAY. THE OUTPUT MUST BE A SINGLE LINE, COMPACT JSON STRING WITH NO PRETTY PRINTING OR LINE BREAKS
"""


def get_domain_user_prompt(clean_content: list[str], domain: str) -> str:
    return f"""
    {GET_DOMAIN_USER_PROMPT}

    Here is the user domain
    {domain}

    -----------------------------
    Here is the urls input
    {clean_content}
    """
