import time
import random
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ==================================================
# CONFIG
# ==================================================

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROMEDRIVER_PATH = r"D:\linkedin_automation\chromedriver.exe"

SEARCH_URL = (
    "https://www.linkedin.com/jobs/search/"
    "?keywords=Operations%20Manager"
    "&location=Germany"
    "&f_TPR=r43200"
    "&f_WT=1"
    "&f_JT=F"
)

MAX_JOBS = 50

start = time.time()  # start timer


# ==================================================
# CHROME OPTIONS
# ==================================================

options = Options()

options.binary_location = CHROME_PATH

options.add_argument("--headless=new")  # run browser in headless mode
options.add_argument("--window-size=1920,1080")

# reduce selenium detection
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")


# ==================================================
# DRIVER SETUP
# ==================================================

driver = webdriver.Chrome(
    service=Service(CHROMEDRIVER_PATH),
    options=options
)

wait = WebDriverWait(driver, 10)  # reduced wait

# hide webdriver flag from LinkedIn
driver.execute_script("""
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
})
""")


# ==================================================
# OPEN SEARCH PAGE
# ==================================================

driver.get(SEARCH_URL)

time.sleep(random.uniform(1.5, 3))  # initial human delay


# ==================================================
# DISMISS LOGIN POPUP
# ==================================================

try:
    dismiss_btn = wait.until(
        EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            "button.contextual-sign-in-modal__modal-dismiss"
        ))
    )

    time.sleep(random.uniform(0.5, 1))

    driver.execute_script(
        "arguments[0].click();",
        dismiss_btn
    )  # click popup dismiss button

    print("Dismissed login popup")

    time.sleep(random.uniform(1, 2))

except:
    print("No popup found")


# ==================================================
# WAIT FOR JOB COUNT + LIST
# ==================================================

wait.until(EC.presence_of_element_located((
    By.CSS_SELECTOR,
    "span.results-context-header__job-count"
)))

job_count = driver.find_element(
    By.CSS_SELECTOR,
    "span.results-context-header__job-count"
).text.strip()

print(f"\nTotal jobs found: {job_count}")

wait.until(EC.presence_of_element_located((
    By.CSS_SELECTOR,
    "ul.jobs-search__results-list"
)))

time.sleep(random.uniform(1, 2))


# ==================================================
# INITIAL HUMAN SCROLL
# ==================================================

for _ in range(random.randint(2, 3)):

    driver.execute_script(
        f"window.scrollBy(0, {random.randint(400, 800)});"
    )  # scroll down naturally

    time.sleep(random.uniform(1, 2.5))


# ==================================================
# SCRAPE JOBS
# ==================================================

results = []
# create excel file immediately to save results one by one
filename = f"job_scrape_{datetime.now().strftime('%d_%m_%H_%M')}.xlsx"

# empty dataframe with headers
pd.DataFrame(
    columns=["company", "url", "description"]
).to_excel(filename, index=False)

for idx in range(MAX_JOBS):

    try:

        # re-fetch jobs every loop to avoid stale elements
        jobs = driver.find_elements(
            By.CSS_SELECTOR,
            "ul.jobs-search__results-list > li"
        )

        job = jobs[idx]

        # scroll current card into view
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            job
        )

        time.sleep(random.uniform(0.8, 1.8))

        card = job.find_element(
            By.CSS_SELECTOR,
            "div.base-search-card"
        )

        # ---------------- TITLE ----------------

        try:
            title = card.find_element(
                By.CSS_SELECTOR,
                "h3.base-search-card__title"
            ).text.strip()

        except:
            title = "N/A"

        # ---------------- COMPANY ----------------

        try:
            company = card.find_element(
                By.CSS_SELECTOR,
                "h4.base-search-card__subtitle"
            ).text.strip()

        except:
            company = "N/A"

        # ---------------- JOB LINK ----------------

        raw_link = card.find_element(
            By.CSS_SELECTOR,
            "a.base-card__full-link"
        ).get_attribute("href")

        link = raw_link.split("?")[0]  # remove tracking params

        print(f"\n[{idx+1}] {title}")
        print(f"Company: {company}")
        print(f"URL: {link}")

        # ---------------- POSTING TIME ----------------

        try:
            time_posted = card.find_element(
                By.CSS_SELECTOR,
                "time.job-search-card__listdate--new"
            ).text.strip()  # e.g. "2 hours ago"

        except:
            time_posted = "N/A"

        # ==================================================
        # OPEN JOB PAGE
        # ==================================================

        driver.get(link)

        time.sleep(random.uniform(1, 2))

        desc_el = wait.until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                "div.show-more-less-html__markup"
            ))
        )

        # get raw HTML description
        html = desc_el.get_attribute("innerHTML")

        soup = BeautifulSoup(html, "html.parser")

        # extract only paragraphs + bullet points
        texts = [
            tag.get_text(" ", strip=True)
            for tag in soup.find_all(["p", "li"])
        ]

        # remove duplicates while preserving order
        full_description = "\n".join(
            dict.fromkeys(filter(None, texts))
        )

        # print("\nFULL DESCRIPTION:\n")
        # print(full_description)

        
        # save result in memory
        job_data = {
            "company": company,
            "title": title,
            "url": link,
            "description": full_description
        }

        results.append(job_data)

        # append immediately to excel after every successful scrape
        pd.DataFrame([job_data]).to_excel(
            filename,
            mode="a",
            header=False,  # don't rewrite headers
            index=False,
            engine="openpyxl"
        )

        print(f"Saved {company} - {title} job information to excel")

        # ==================================================
        # RETURN TO SEARCH PAGE
        # ==================================================

        driver.back()

        time.sleep(random.uniform(0.8, 2))

        wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR,
            "ul.jobs-search__results-list"
        )))

        # small random scroll after return
        driver.execute_script(
            f"window.scrollBy(0, {random.randint(250, 600)});"
        )

        time.sleep(random.uniform(0.8, 1.8))

    except Exception as e:

        print(f"\nERROR ON JOB {idx+1}: {e}")

        # recovery reload
        try:
            driver.get(SEARCH_URL)

            time.sleep(random.uniform(2, 4))

        except:
            pass


# ==================================================
# SHOW SCRAPE TIME
# ==================================================

print(f"\nTOTAL TIME: {round(time.time() - start, 2)} seconds")


# ==================================================
# CLOSE DRIVER
# ==================================================

driver.quit()  # close browser