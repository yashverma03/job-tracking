from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper
from modules.scraper.types import ScraperJobData
from modules.scraper.utils.rate_limiter import wait_between_requests
from modules.scraper.utils.text_cleaner import clean_text

HOST = 'eeho.fa.us2.oraclecloud.com'
LIST_URL = f'https://{HOST}/hcmRestApi/resources/latest/recruitingCEJobRequisitions'
DETAIL_URL_TEMPLATE = f'https://{HOST}/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails/{{job_id}}'
JOB_URL_TEMPLATE = 'https://careers.oracle.com/en/sites/jobsearch/job/{job_id}'
COMPANY_NAME = 'Oracle'
PAGE_SIZE = 14

LIST_EXPAND = (
    'requisitionList.workLocation,requisitionList.otherWorkLocations,'
    'requisitionList.secondaryLocations,flexFieldsFacet.values,requisitionList.requisitionFlexFields'
)
FINDER_TEMPLATE = (
    'findReqs;siteNumber=CX_45001,'
    'facetsList=LOCATIONS;WORK_LOCATIONS;WORKPLACE_TYPES;TITLES;CATEGORIES;ORGANIZATIONS;POSTING_DATES;FLEX_FIELDS,'
    'limit={limit},offset={offset},lastSelectedFacet=POSTING_DATES,'
    'selectedFlexFieldsFacets="AttributeChar4|Employee||AttributeChar29|Individual Contributor||AttributeChar6|3 to 5+ years",'
    'selectedLocationsFacet=300000000106947,selectedPostingDatesFacet=2,sortBy=POSTING_DATES_DESC'
)

# Job-specific detail fields to concatenate into the stored description - excludes the
# generic company/EEO boilerplate fields (e.g. CorporateDescriptionStr) that repeat
# identically across every posting.
DESCRIPTION_FIELDS = ('ExternalDescriptionStr', 'ExternalResponsibilitiesStr', 'ExternalQualificationsStr')
# Location fields to concatenate, in priority order. The list-item fields (secondary/
# other/work locations) are lists of dicts with a `Name` key; the primary location is a
# plain string.
LOCATION_LIST_FIELDS = ('secondaryLocations', 'otherWorkLocations', 'workLocation')


@register_scraper
class OracleScraper(ApiScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.ORACLE

    @property
    def page_size(self) -> int:
        return PAGE_SIZE

    @property
    def list_url(self) -> str:
        return LIST_URL

    @property
    def detail_url(self) -> str:
        # Unused: `_fetch_detail_fields` is overridden below since the detail URL is
        # templated on each listing's own job id, not a fixed endpoint.
        return DETAIL_URL_TEMPLATE

    def build_list_params(self, start: int) -> dict:
        return {
            'onlyData': 'true',
            'expand': LIST_EXPAND,
            'finder': FINDER_TEMPLATE.format(limit=self.page_size, offset=start),
        }

    def parse_list_items(self, response_json: dict) -> list[dict]:
        items = response_json.get('items') or []
        return items[0].get('requisitionList', []) if items else []

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        job_id = item.get('Id')
        if not job_id:
            self._record_error(None, f'missing job id: {item}')
            return None

        return ScraperJobData(
            url=clean_job_url(JOB_URL_TEMPLATE.format(job_id=job_id)),
            official_id=str(job_id),
            title=clean_text(item.get('Title')),
            company_name=COMPANY_NAME,
            location=clean_text(_build_location_text(item)),
            extra={'job_id': job_id},
        )

    def build_detail_params(self, listing: ScraperJobData) -> dict:
        return {}

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        wait_between_requests()
        response = self._request(
            DETAIL_URL_TEMPLATE.format(job_id=listing.extra['job_id']), params={'onlyData': 'true', 'expand': 'all'}
        )
        response.raise_for_status()
        return self.parse_detail_fields(response.json())

    def parse_detail_fields(self, response_json: dict) -> dict:
        description = '\n\n'.join(text for text in (response_json.get(field) for field in DESCRIPTION_FIELDS) if text)

        return {
            'description': clean_text(description),
            'location': clean_text(_build_location_text(response_json)),
        }


def _build_location_text(fields: dict) -> str | None:
    names = []
    primary_location = fields.get('PrimaryLocation')
    if primary_location:
        names.append(primary_location)

    for field_name in LOCATION_LIST_FIELDS:
        for location in fields.get(field_name) or []:
            name = location.get('Name')
            if name and name not in names:
                names.append(name)

    return ', '.join(names) if names else None
