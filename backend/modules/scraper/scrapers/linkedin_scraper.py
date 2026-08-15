import re

import requests
from bs4 import BeautifulSoup

from common.utils.env import get_env_int
from modules.jobs.services import job_service, job_unique_key_service
from modules.scraper.base.base_scraper import BaseScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.utils.rate_limiter import wait_between_requests
from modules.scraper.utils.scraper_logger import get_scraper_logger
from modules.scraper.utils.user_agent_rotator import get_random_user_agent

LISTING_URL = 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search'
DETAIL_URL_TEMPLATE = 'https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}'
PAGE_SIZE = 10
REQUEST_TIMEOUT_SECONDS = 15
MAX_JOBS_PER_RUN_ENV_KEY = 'SCRAPER_MAX_JOBS_PER_RUN'

DEFAULT_SEARCH_FILTERS = {
    'keywords': 'software',
    'location': 'India',
    'f_TPR': 'r86400',
    'f_E': '2,3,4',
    'f_JT': 'F',
}

JOB_ID_PATTERN = re.compile(r'-(\d+)(?:\?|$)')


class LinkedInScraper(BaseScraper):
    @property
    def name(self) -> str:
        return ScraperName.LINKEDIN.value

    def __init__(self):
        self._logger = get_scraper_logger(self.name)
        self._session = requests.Session()
        self._max_jobs_per_run = get_env_int(MAX_JOBS_PER_RUN_ENV_KEY)
        self._total_count = 0
        self._total_unique_count = 0

    def run(self) -> dict:
        self._total_count = 0
        self._total_unique_count = 0
        start = 0

        while self._total_count < self._max_jobs_per_run:
            self._logger.info('fetching listing page start=%s', start)
            html = self._fetch_listing_page(start)
            page_listings = self._parse_listing_html(html)

            if not page_listings:
                break

            for listing in page_listings:
                if self._total_count >= self._max_jobs_per_run:
                    break

                self._total_count += 1
                self._process_listing(listing)

            start += PAGE_SIZE
            wait_between_requests()

        self._logger.info(
            'run complete, checked=%s inserted=%s', self._total_count, self._total_unique_count
        )

        return {
            'total_count': self._total_count,
            'total_unique_count': self._total_unique_count,
        }

    def _process_listing(self, listing: dict) -> None:
        url = listing['url']

        if job_unique_key_service.is_duplicate(url, None):
            self._logger.info('duplicate skipped: %s', url)
            return

        self._logger.info('fetching details for %s', url)
        description = self._fetch_job_details(url)

        try:
            job_service.create_scraped_job(
                title=listing['title'],
                company_name=listing['company_name'],
                location=listing['location'],
                description=description,
                url=url,
            )
        except Exception as exc:  # noqa: BLE001 - one job's failure must not abort the run
            self._logger.warning('job insert failed for %s: %s', url, exc)
            return

        self._total_unique_count += 1
        self._logger.info('job inserted: %s', url)

    def _fetch_listing_page(self, start: int) -> str:
        params = {**DEFAULT_SEARCH_FILTERS, 'start': start}
        response = self._session.get(
            LISTING_URL,
            params=params,
            headers={'User-Agent': get_random_user_agent()},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.text

    def _parse_listing_html(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, 'html.parser')
        listings = []

        for card in soup.find_all('li'):
            link = card.find('a', class_='base-card__full-link')
            if link is None or not link.get('href'):
                continue

            url = link['href'].split('?')[0].strip()
            title_el = card.find('h3', class_='base-search-card__title')
            company_el = card.find('h4', class_='base-search-card__subtitle')
            location_el = card.find('span', class_='job-search-card__location')

            listings.append(
                {
                    'url': url,
                    'title': title_el.get_text(strip=True) if title_el else None,
                    'company_name': company_el.get_text(strip=True) if company_el else None,
                    'location': location_el.get_text(strip=True) if location_el else None,
                }
            )

        return listings

    def _fetch_job_details(self, url: str) -> str | None:
        wait_between_requests()

        job_id_match = JOB_ID_PATTERN.search(url)
        if not job_id_match:
            self._logger.warning('could not extract job id from url: %s', url)
            return None

        detail_url = DETAIL_URL_TEMPLATE.format(job_id=job_id_match.group(1))
        response = self._session.get(
            detail_url,
            headers={'User-Agent': get_random_user_agent()},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return self._parse_detail_html(response.text)

    def _parse_detail_html(self, html: str) -> str | None:
        soup = BeautifulSoup(html, 'html.parser')
        description_el = soup.find('div', class_='show-more-less-html__markup')
        if description_el is None:
            return None
        return description_el.get_text(separator='\n', strip=True)
