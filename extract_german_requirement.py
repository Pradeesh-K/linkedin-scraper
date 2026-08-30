import pandas as pd, re
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import time

load_dotenv()
start = time.time()  # start timer

file = "Marketing Specialist_job_scrape_30_08_22_29.xlsx"
df = pd.read_excel(file)


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# ==================================================
# KEYWORDS
# ==================================================

keywords = [
    "german","deutsch","german language","german speaking","german speaker",
    "german skills","german proficiency","german fluency","fluent german",
    "native german","business german","c1","c2","b2","cefr",
    "deutschkenntnisse","deutsch kenntnisse","sehr gute deutschkenntnisse",
    "gute deutschkenntnisse","verhandlungssicher deutsch","deutsch in wort und schrift",
    "must speak german","german required","german is required","knowledge of german",
    "written and spoken german","spoken german","excellent german","professional german",
    "english and german","german and english","both german and english"
]

# ==================================================
# EXTRACT SNIPPETS
# ==================================================

def extract(text):
    if not isinstance(text, str): return ""
    text_l = text.lower()
    out = []

    for k in keywords:
        for m in re.finditer(rf"\b{re.escape(k)}\b", text_l):
            s = max(0, m.start()-50)
            e = min(len(text), m.end()+50)
            out.append(text[s:e].replace("\n"," ").strip())

    return " | ".join(dict.fromkeys(out))


df["german_skills"] = df["description"].apply(extract)

# # ==================================================
# # LLM CLASSIFIER
# # ==================================================

# def needs_german(text):
#     if not isinstance(text, str) or not text.strip():
#         return False

#     prompt = f"This is a snippet from a Job Description. Is German mandatory for this job ? Optional, is a plus etc means non mandatory. Return only True or False:\n{text}"
#     return llm.invoke([HumanMessage(content=prompt)]).content.strip().lower() == "true"

# df["german_needed"] = df["german_skills"].apply(needs_german)

## Job language
def job_lang(text):
    if not isinstance(text, str) or not text.strip():
        return "unknown"

    t = text.lower()

    g = sum(w in t for w in ["deutsch","german","kenntnisse","wir "," und "," die ", "sie"])
    e = sum(w in t for w in ["experience","responsibilities","we "," and "," the "," role", "you"])

    return "german" if g > e else "english" if e > g else "mixed"


df["job_post_language"] = df["description"].apply(job_lang)

# ==================================================
# SAVE
# ==================================================

df.insert(0, "serial_number", range(1, len(df) + 1))
df.to_excel(file, index=False)

print(f"\nJobs classified in {round(time.time() - start, 2)} seconds")