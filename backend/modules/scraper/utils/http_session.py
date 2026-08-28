import random

from curl_cffi import requests

# TLS/user-agent fingerprint profiles curl_cffi can impersonate. Picking one at random
# per session makes concurrent scraper sessions look like distinct browsers.
IMPERSONATE_PROFILES = [
    'chrome116', 'chrome119', 'chrome120', 'chrome123', 'chrome124',
    'chrome131', 'chrome133a', 'chrome136',
    'edge101',
    'safari153', 'safari155', 'safari170', 'safari180', 'safari184',
    'firefox133', 'firefox135',
]

COMMON_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}


def new_session(proxy_url: str | None = None) -> requests.Session:
    """Build a fresh HTTP session: a random impersonate profile (TLS/browser fingerprint)
    plus the shared baseline headers. Pass proxy_url to route the session through a proxy;
    omit it for a plain direct-connection session."""
    impersonate_profile = random.choice(IMPERSONATE_PROFILES)

    session = requests.Session(impersonate=impersonate_profile)
    session.headers.update(COMMON_HEADERS)
    if proxy_url:
        session.proxies = {'http': proxy_url, 'https': proxy_url}
    return session
