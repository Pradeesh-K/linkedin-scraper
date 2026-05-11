import logging
from linkedin_jobs_scraper import LinkedinScraper
from linkedin_jobs_scraper.events import Events, EventData, EventMetrics
from linkedin_jobs_scraper.query import Query, QueryOptions, QueryFilters
from linkedin_jobs_scraper.filters import (
    TimeFilters,
    TypeFilters,
    OnSiteOrRemoteFilters
)

logging.basicConfig(level=logging.INFO)


def on_data(data: EventData):
    print(
        '[JOB]',
        data.title,
        '|', data.company,
        '|', data.place,
        '|', data.date_text,
        '|', data.link
    )


def on_error(error):
    print('[ERROR]', error)


def on_end():
    print('[END]')


scraper = LinkedinScraper(
    chrome_executable_path=r"D:\linkedin_automation\chromedriver.exe",
    chrome_binary_location=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    headless=True,
    max_workers=1,
    slow_mo=2,  # safer (you can reduce later)
)


scraper.on(Events.DATA, on_data)
scraper.on(Events.ERROR, on_error)
scraper.on(Events.END, on_end)


queries = [
    Query(
        query='Operations Manager',
        options=QueryOptions(
            locations=['Germany'],
            limit=10,
            filters=QueryFilters(
                time=TimeFilters.DAY,  # posted today
                type=[TypeFilters.FULL_TIME],
                on_site_or_remote=[OnSiteOrRemoteFilters.ON_SITE]
            )
        )
    )
]


try:
    scraper.run(queries)
except KeyboardInterrupt:
    print("Stopped by user")

# set LI_AT_COOKIE=AQEDAQkYRSsBbkr0AAABnVCB1EoAAAGddI5YSk4AyOZAtgx_jsUMeaDjj94lA9yyABMxmyebsj7QVkHC3AP2X6FP2K71gvDvwV-3b0VTk6XYCJ17kljBu84VAs--Zk71GsVZTV5n9ViiyPxjRVKEBK5W