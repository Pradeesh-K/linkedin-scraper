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

role = "Sales Specialist"

SEARCH_URL = (
    "https://www.linkedin.com/jobs/search/"
    f"?keywords={role.replace(' ', '%20')}"
    "&location=Germany"
    "&f_TPR=r43200"
    "&f_WT=1"
    "&f_JT=F"
)



MAX_JOBS = None

start = time.time()


# ==================================================
# CHROME OPTIONS
# ==================================================

options = Options()

options.binary_location = CHROME_PATH

options.add_argument("--headless=new")
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
    options=options
)

wait = WebDriverWait(driver, 10)

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

time.sleep(random.uniform(0.8, 1.5))


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

    time.sleep(random.uniform(0.2, 0.5))

    driver.execute_script(
        "arguments[0].click();",
        dismiss_btn
    )

    print("Dismissed login popup")

    time.sleep(random.uniform(0.5, 1))

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

time.sleep(random.uniform(0.3, 0.8))


# ==================================================
# INITIAL HUMAN SCROLL
# ==================================================

for _ in range(random.randint(1, 2)):

    driver.execute_script(
        f"window.scrollBy(0, {random.randint(400, 800)});"
    )

    time.sleep(random.uniform(0.4, 1.2))


# ==================================================
# SCRAPE JOBS
# ==================================================

results = []

filename = f"{role}_job_scrape_{datetime.now().strftime('%d_%m_%H_%M')}.xlsx"
log_file = f"{role}_{datetime.now().strftime('%d_%m_%H_%M')}_errors.txt"

with open(log_file, "w", encoding="utf-8") as f:
    f.write(f"Error log started: {datetime.now()}\n")
    f.write("=" * 80 + "\n")

# create Excel file immediately with headers
pd.DataFrame(
    columns=["company", "title", "time_posted", "url", "description"]
).to_excel(filename, index=False)

def save_results():
    try:
        pd.DataFrame(results).to_excel(filename, index=False)
    except Exception as e:
        print(f"Excel save failed: {type(e).__name__}")

try:
    for idx in range(len(driver.find_elements(By.CSS_SELECTOR,"ul.jobs-search__results-list > li"))):

        try:

            # --------------------------------------------------
            # RE-FETCH JOBS EVERY LOOP TO AVOID STALE ELEMENTS
            # --------------------------------------------------

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

            time.sleep(random.uniform(0.3, 0.8))


            # ==================================================
            # JOB CARD
            # ==================================================

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

            link = raw_link.split("?")[0]


            print(f"\n[{idx+1}] {title}")
            print(f"Company: {company}")
            print(f"URL: {link}")


            # ---------------- POSTING TIME ----------------

            try:
                time_posted = card.find_element(
                    By.CSS_SELECTOR,
                    "time.job-search-card__listdate--new"
                ).text.strip()

            except:
                time_posted = "N/A"


            # ==================================================
            # OPEN JOB PAGE
            # ==================================================

            driver.get(link)

            time.sleep(random.uniform(0.5, 1))


            desc_el = wait.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "div.show-more-less-html__markup"
                ))
            )
            # ==================================================
            # EXTRACT DESCRIPTION
            # ==================================================

            # get raw HTML description
            html = desc_el.get_attribute("innerHTML")

            soup = BeautifulSoup(html, "html.parser")

            # LinkedIn puts the complete description inside this span.
            # Extract the entire text, including nested <li> elements.
            description_box = soup.find(
                "span",
                attrs={"data-testid": "expandable-text-box"}
            )

            if description_box:
                full_description = description_box.get_text(
                    "\n",
                    strip=True
                )
            else:
                # fallback if LinkedIn changes the HTML structure
                full_description = soup.get_text(
                    "\n",
                    strip=True
                )
            # ==================================================
            # STORE RESULT
            # ==================================================
            job_data = {
                "company": company,
                "title": title,
                "time_posted": time_posted,
                "url": link,
                "description": full_description
            }
            results.append(job_data)
            f"Checkpoint saved: {idx + 1} jobs"
            save_results()

            # ==================================================
            # RETURN TO SEARCH PAGE
            # ==================================================

            driver.back()

            time.sleep(random.uniform(0.5, 1.2))


            wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR,
                "ul.jobs-search__results-list"
            )))


            # small random scroll after return
            driver.execute_script(
                f"window.scrollBy(0, {random.randint(250, 600)});"
            )

            time.sleep(random.uniform(0.3, 0.8))

        except Exception as e:

            print(f"\nERROR ON JOB {idx+1}: Skipped")

            # Logging Errors
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(
                    f"\nJOB {idx+1} FAILED\n"
                    f"Title: {title if 'title' in locals() else 'Unknown'}\n"
                    f"Company: {company if 'company' in locals() else 'Unknown'}\n"
                    f"URL: {link if 'link' in locals() else 'Unknown'}\n"
                    f"Error Type: {type(e).__name__}\n"
                    f"Error: {str(e)}\n"
                    f"{'-' * 80}\n"
                )

            # ==================================================
            # RECOVERY RELOAD
            # ==================================================
            try:
                driver.get(SEARCH_URL)
                time.sleep(random.uniform(1, 2.1))
                wait.until(EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "ul.jobs-search__results-list"
                )))

            except:
                pass

    # ==================================================
    # FINAL SAVE
    # ==================================================
    save_results()
    print(f"\nFinal results saved to: {filename}")
    # ==================================================
    # SHOW SCRAPE TIME
    # ==================================================
    print(
        f"\nTOTAL TIME: {round(time.time() - start, 2)} seconds")


except KeyboardInterrupt:
    print("\nStopped by user — saving results...")
    save_results()

finally:
    # ==================================================
    # CLOSE DRIVER
    # ==================================================
    save_results()
    driver.quit()