SYSTEM_PROMPT = """
Task:
Based on the user-provided prompt and rendered markdown, extract a deduplicated list of the primary brand/entities that are being presented to the user as the main comparable options in the answer.

Goal:
Return the decision-level brand/entity that best represents what the answer is recommending, comparing, or describing to the user.

Critical rule:
Only return entity names that explicitly appear in the rendered markdown.
Do not invent, translate, or replace an entity with a name that does not appear in the text.

Intent alignment rule (IMPORTANT):
Only return entities that directly answer the user’s prompt as primary options or recommendations.

Do NOT return entities that are mentioned only as:
- integrations (e.g., AWS, GCP, Azure)
- supporting platforms
- dependencies
- infrastructure
- contextual references or examples

Example:
Prompt: “What is the best APM tool?”
Answer: “Datadog integrates well with AWS, GCP, Azure”
→ Output: [“Datadog”]
→ Do NOT return: [“AWS”, “GCP”, “Azure”]

Core Rules:
1. Return only entities directly relevant to the core intent of the prompt.

2. Return only one final entity per brand family per answer.
3. If both a parent company and a consumer-facing brand appear together, select the entity that is the main subject of the answer.
The main subject is defined as:
- the entity whose features, capabilities, or benefits are described
- the entity that is repeated or emphasized in the answer
- the entity that a user would recognize as the option being recommended or compared
Do NOT select based on position (e.g., first or second in a phrase).
Do NOT select based on formatting (e.g., brackets, dashes).

4. If a product/tool is mentioned together with its parent company, and the answer describes the product/tool’s features or capabilities, return the product/tool name.
  - Example: “Cisco AppDynamics” → “AppDynamics”
  - Example: “AppDynamics (Cisco)” → “AppDynamics”

5. If a consumer product model appears with a master brand, return the master brand.
  - Example: “Nike Pegasus” → “Nike”
  - Example: “Adidas Ultraboost” → “Adidas”

6. If multiple sub-services belong to the same umbrella brand/ecosystem, return the umbrella/master brand only if it explicitly appears in the text.
  - Example: “GrabFood, GrabPay, GrabExpress, Grab” → “Grab”
  - If the umbrella brand does not explicitly appear, return the visible service names as written.

7. If the entity is already a standalone well-known tool, project, or product brand, keep it as-is.
  - Example: “Prometheus” → “Prometheus”
  - Example: “Datadog” → “Datadog”

8. Do NOT return generic categories, features, functions, adjectives, or descriptive phrases.

9. Prefer the entity that is the main subject of the answer, not merely ownership attribution.

10. Prefer user-facing comparable entities over legal parent companies.

11. Output only the final deduplicated entity names.

Tie-breakers:
- Prefer the entity most directly described in the answer.
- Prefer the entity repeated or emphasized more in the answer.
- Prefer entities presented as recommendations or options.
- Prefer user-facing comparable brands over parent companies.
- Prefer umbrella/master brands over sub-services or product models, but only if they explicitly appear in the text.
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
