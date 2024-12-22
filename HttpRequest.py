import json
import logging
import time
import traceback
from collections import defaultdict


def _handle_http_error(url, status_code, reason, data):
    """Handles HTTP errors (non-2xx statuses) and logging."""
    logging.error(f"HTTP Error {status_code} ({reason}) on {url}")
    logging.debug(f"Response body: {data.decode('utf-8', errors='replace')}")


def _handle_error(message, exc=None):
    """Handles logging error and prints stack trace."""
    logging.error(message)
    if exc:
        logging.debug(traceback.format_exc())


def _parse_json(data):
    """Safely attempts to parse JSON data."""
    try:
        return json.loads(data.decode("utf-8"))
    except json.JSONDecodeError as err:
        _handle_error(f"JSON decoding failed for data: {data}", exc=err)
        return None


class HttpRequest:
    def __init__(self, conn, headers, retries=10, delay=2, max_redirects=10):
        self.conn = conn
        self.headers = headers
        self.retries = retries
        self.delay = delay
        self.max_redirects = max_redirects

        # Инициализируем cookies из заголовка headers, если они есть
        self.cookies = defaultdict(str)
        if 'cookie' in self.headers:
            self._extract_cookies_from_header(self.headers['cookie'])

    def _extract_cookies_from_header(self, cookie_header):
        """Parses cookies from the Cookie header."""
        for cookie in cookie_header.split(';'):
            key_value = cookie.split('=')
            if len(key_value) == 2:
                self.cookies[key_value[0].strip()] = key_value[1].strip()

    def _get_cookies_header(self):
        """Return cookies formatted for the 'Cookie' header."""
        if not self.cookies:
            return ''
        return '; '.join(f"{key}={value}" for key, value in self.cookies.items())

    def _wait_retry(self, attempt):
        """Handles waiting between retries with exponential backoff."""
        logging.info(f"Retrying... Attempt {attempt + 1} of {self.retries}. Waiting {self.delay}s.")
        time.sleep(self.delay)
        self.delay *= 2  # Exponential backoff

    def _handle_redirect(self, res):
        """Processes redirects and updates cookies."""
        set_cookie_header = res.getheader('Set-Cookie')
        if set_cookie_header:
            for cookie in set_cookie_header.split(';'):
                key_value = cookie.split('=')
                if len(key_value) == 2:
                    # Обновляем существующие cookies, если ключ уже есть
                    self.cookies[key_value[0].strip()] = key_value[1].strip()

    def _make_request(self, url):
        """Makes the HTTP request, adding cookies to headers."""
        self.headers['Cookie'] = self._get_cookies_header()
        self.conn.request("GET", url, '', self.headers)
        res = self.conn.getresponse()
        data = res.read()
        return res.status, res.reason, data, res

    def make_request(self, url):
        """Handles retries, redirects, and error processing while making HTTP requests."""
        redirects = 0
        while redirects < self.max_redirects:
            for attempt in range(self.retries):
                try:
                    status_code, reason, data, res = self._make_request(url)
                    logging.info(f"Attempt {attempt + 1}: status {status_code} for URL: {url}")

                    if 200 <= status_code < 300:
                        return _parse_json(data)

                    if status_code in {301, 302, 303, 307, 308}:
                        location = res.getheader("Location")
                        if not location:
                            _handle_error(f"Redirect but no Location provided for URL: {url}")
                            return None
                        self._handle_redirect(res)
                        url = location
                        redirects += 1
                        break

                    if status_code == 504:
                        logging.warning(f"Gateway Timeout for URL: {url}")
                        self._wait_retry(attempt)
                        continue

                    _handle_http_error(url, status_code, reason, data)
                    break

                except Exception as e:
                    _handle_error(f"Request attempt {attempt + 1} failed: {e}", exc=e)

                if attempt < self.retries - 1:
                    self._wait_retry(attempt)

            logging.error(f"All {self.retries} attempts failed for URL: {url}")
            return None

        logging.error(f"Too many redirects for URL: {url}")
        return None