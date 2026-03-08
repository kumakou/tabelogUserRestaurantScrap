import time
from typing import Optional

import requests
from requests import RequestException, Response

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    )
}


def fetch_response(
    url: str,
    timeout: float = 20.0,
    retries: int = 2,
    backoff_seconds: float = 1.0,
    sleep_after: float = 0.0,
) -> Optional[Response]:
    """
    Fetch URL with simple retry/backoff policy.
    Returns None when all attempts fail or non-200 response persists.
    """
    max_attempts = max(1, retries + 1)
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        except RequestException as exc:
            print(f"[warn] request failed ({attempt}/{max_attempts}): {url} ({exc})")
            if attempt < max_attempts:
                time.sleep(backoff_seconds * attempt)
            continue

        if response.status_code == requests.codes.ok:
            if sleep_after > 0:
                time.sleep(sleep_after)
            return response

        print(
            f"[warn] unexpected status ({attempt}/{max_attempts}): "
            f"{response.status_code} {url}"
        )
        if attempt < max_attempts:
            time.sleep(backoff_seconds * attempt)

    return None
