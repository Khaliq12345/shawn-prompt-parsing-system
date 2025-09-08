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
