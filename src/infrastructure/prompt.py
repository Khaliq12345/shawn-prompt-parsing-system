SYSTEM_PROMPT = """
You are an assistant that calculates Brand Counts and Positions in AI-generated responses.
Follow these rules carefully:

Definitions
    Brand Count = The total number of distinct textual occurrences where a brand is explicitly referenced as an entity in the final rendered AI answer text.
    Unit/Type: Integer (count).
    Brand Position = The sequential order of each brand's first appearance relative to other brands in the main answer text (starting from 1).

Core Counting Rules
    1. Count only explicit brand-name mentions
        - Examples: Zendesk, Zendesk Inc, Zendesk (company)
        - Must include the actual brand name in text
        - Case-insensitive and diacritics-insensitive
    
    2. Each distinct textual occurrence = +1
        - Count literal appearances of the brand as separate references
        - Section, paragraph, or intent does not matter
    
    3. Do NOT infer brands
        - Product-only mentions do NOT count (e.g., "Answer Bot" ≠ Zendesk)
        - Feature-only mentions do NOT count
        - Implied ownership is ignored

Brand Block Rule (Critical)
    If a brand is introduced as the primary subject (e.g., header or root list item), branded product mentions nested under that same brand block do NOT increment Brand Count again.
    
    Example:
        "1. Zendesk
         - Live chat (via Zendesk Chat)
         - AI-powered tools (Answer Bot)"
    
    Counting:
        - Zendesk → +1 (primary subject)
        - Zendesk Chat → 0 (nested under Zendesk brand block)
        - Answer Bot → 0 (product only, no brand name)
        Zendesk Brand Count = 1

When Branded Products DO Count
    Branded product names count only if they appear outside an existing brand block (i.e., they function as a new textual reference).
    
    Example:
        "Zendesk is widely used by support teams.
         Some companies rely heavily on Zendesk Chat for live support."
    
    Counting:
        - First Zendesk → +1
        - Zendesk Chat (outside brand block) → +1
        Zendesk Brand Count = 2

Multiple Mentions in One Section
    If the brand name appears multiple times as separate textual references, each counts.
    
    Example:
        "If deep CRM integration is essential, Salesforce Service Cloud or Zendesk may be best.
         If existing CRM assets are elsewhere, Zendesk or Freshdesk offer flexibility."
    
    Counting:
        - First Zendesk → +1
        - Second Zendesk → +1
        Zendesk Brand Count = 2

What Does NOT Count
    ❌ Product-only mentions without the brand name (e.g., "Answer Bot")
    ❌ Feature mentions
    ❌ Citations, URLs, links, images, metadata
    ❌ Human-inferred ownership or brand associations
    ❌ Branded products nested within an existing brand block

Scope & Matching
    - Scope: Final rendered AI answer text only
    - Exclude: Citations, footnotes, links, metadata, sources
    - Matching: Case-insensitive and diacritics-insensitive

Position Output
    For each brand, record the position (starting from 1) based on the first occurrence of that brand relative to other brands.
    Example: If Zendesk appears before Salesforce, Zendesk position = 1, Salesforce position = 2.
"""

USER_PROMPT = """
You are an assistant that calculates Brand Counts and Positions in AI-generated responses.

Count how many times each brand is explicitly mentioned and determine their positions in the following markdown.

Apply these rules:
    1. Count only explicit brand-name mentions (case-insensitive, diacritics-insensitive)
    2. Each distinct textual occurrence = +1
    3. Do NOT count:
        - Product-only mentions without brand name
        - Feature mentions
        - Branded products nested within a brand block
        - Citations, links, or metadata
    4. Apply the Brand Block Rule: If a brand introduces a section, nested branded products under that block don't count
    5. Scope: main answer text only
    6. Position: based on first occurrence of each brand relative to other brands (not words)

Example Input:
    "1. Zendesk
     - Live chat via Zendesk Chat
     - Answer Bot for AI support
     
     2. Salesforce Service Cloud
     - Enterprise CRM integration
     
     For smaller teams, Zendesk or Freshdesk offer flexibility."

Example Output:
    [
        {"brand_count": 2, "position": 1, "brand_name": "Zendesk"},
        {"brand_count": 1, "position": 2, "brand_name": "Salesforce"},
        {"brand_count": 1, "position": 3, "brand_name": "Freshdesk"}
    ]

Explanation:
    - First Zendesk (header) → +1
    - Zendesk Chat (nested in Zendesk block) → 0
    - Answer Bot (product only) → 0
    - Salesforce Service Cloud → +1
    - Second Zendesk (outside brand block) → +1
    - Freshdesk → +1

Now analyze the following markdown:
"""


def get_user_prompt(clean_content: str) -> str:
    return f"""
        {USER_PROMPT}
        Here is the text :
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
"""

SENTIMENT_USER_PROMPT = """
You are given a markdown about brands.
Your task is to parse this text and return results strictly in the JSON format defined in the System Prompt.

- Focus only on the **main body text** (ignore citations, footnotes, and metadata).
- Detect all **brands** and, if mentioned, their **models**.
- Extract short descriptive snippets (phrases) that describe performance, comfort, quality, durability, or design.
- Classify each phrase as 🟢 Positive or 🔴 Negative.
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
