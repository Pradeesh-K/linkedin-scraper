scraped_jobs_link = "job_scrape_11_05_13_36.xlsx"

import pandas as pd
import re

# ==================================================
# LOAD EXCEL
# ==================================================

df = pd.read_excel(scraped_jobs_link)

# ==================================================
# GERMAN KEYWORDS
# ==================================================

# broader german-language requirement keywords
keywords = [

    # direct language mentions
    "german",
    "deutsch",
    "german language",
    "german speaking",
    "german speaker",
    "german skills",
    "german proficiency",
    "german fluency",
    "fluent german",
    "native german",
    "business german",

    # german proficiency levels
    "c1",
    "c2",
    "b2",
    "cefr",

    # german-specific phrases
    "deutschkenntnisse",
    "deutsch kenntnisse",
    "sehr gute deutschkenntnisse",
    "gute deutschkenntnisse",
    "verhandlungssicher deutsch",
    "deutsch in wort und schrift",

    # requirement wording
    "must speak german",
    "german required",
    "german is required",
    "german preferred",
    "knowledge of german",
    "written and spoken german",
    "spoken german",
    "excellent german",
    "professional german",

    # multilingual requirement patterns
    "english and german",
    "german and english",
    "both german and english"
]
# ==================================================
# FUNCTION TO EXTRACT MATCH CONTEXT
# ==================================================

def extract_german_skills(text):

    if pd.isna(text):
        return ""

    text_lower = text.lower()  # case-insensitive matching

    matches = []

    # search every keyword one by one
    for keyword in keywords:

        # WORD-BOUNDARY MATCH ONLY → prevents "Germany" false positives
        pattern = r"\b" + re.escape(keyword.lower()) + r"\b"

        # find all occurrences safely
        for match in re.finditer(pattern, text_lower):

            start = max(0, match.start() - 50)   # 50 chars before match
            end = min(len(text), match.end() + 50)  # 50 chars after match

            snippet = text[start:end].replace("\n", " ")  # clean formatting

            matches.append(snippet.strip())

    # remove duplicates while preserving order
    return " | ".join(dict.fromkeys(matches))

# ==================================================
# CREATE NEW COLUMN
# ==================================================

df["german_skills"] = df["description"].apply(extract_german_skills)

# ==================================================
# SAVE BACK TO SAME FILE
# ==================================================

df.to_excel(scraped_jobs_link, index=False)

print("German skills extraction completed")