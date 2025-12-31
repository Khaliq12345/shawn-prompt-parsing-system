SYSTEM_PROMPT = """
    You are an assistant that calculates Brand Mentions and Positions in responses.
    Follow these rules carefully:

    Definitions

        Brand Mentions = Total number of times a brand (including aliases) appears across all main answer texts within the selected time window.

        Unit/Type: Integer (count).

        Prompt Position = The index or location of each brand within the main answer text, this should be based on other brands not words.

    Formula
    Rules

        Aliases count toward the main brand -

            Example:

                Adidas → {Adizero, Ultraboost, Adizero Evo SL, Adidas Ultraboost Light}

                Nike → {Pegasus, Invincible}

        Scope: Count only the main answer text, exclude citations, footnotes, and links.

        - Case-insensitive: Treat Adidas, adidas, ADIDAS as the same.

        - Diacritics-insensitive: Treat Adìdas = Adidas.

        - Include all variants and repetitions. Each occurrence counts separately.

        - Prompt Position Output: For each brand mention, record the position (starting from 1) of the brand compared to the others.
            For example: If Adidas brand appears before Nike brand then in the output Adidas position will be 1 and Nike will be 2.
                        If those two are the only ones in the markdown.


    Common Errors to Avoid

        ❌ Missing alias mapping (e.g., “Ultraboost” not counted as Adidas).

        ❌ Counting in citations, sources, or links.

        ❌ Case-sensitive counting (e.g., ignoring adidas).

        ❌ Deduplicating mentions (we count every mention, not just unique ones).

        ❌ Ignoring diacritics (e.g., “Adìdas” should be counted).

        ❌ Failing to record accurate positions of brand among other brands in the markdown.
"""

USER_PROMPT = """
    You are an assistant that calculates Brand Mentions and Positions in responses
    Count how many times each brand (with aliases) is mentioned and as well as their positions in the following markdown.
    Apply the rules:

        Count all mentions of the brand and its aliases.

        Case-insensitive, diacritics-insensitive.

        Scope: main answer text only, exclude links/citations.

        Output the total count per brand as an integer.

         The index or location of each brand within the main answer text, this should be based on other brands not words.

    Example Input:

        "Adidas Adizero Evo SL and the Adidas Ultraboost Light are both excellent.
        The Nike Pegasus is also great."

    Example Output:
    [{"mention_count": 2, "position": 1, "brand_name": "Adidas"},
    {"mention_count": 1, "position": 2, "brand_name": "Nike"}],

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
