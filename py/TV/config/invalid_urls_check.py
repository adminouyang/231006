import concurrent.futures
import subprocess

import requests
import logging
import warnings
import ping3
from urllib.parse import urlsplit


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s', handlers=[logging.FileHandler("py/TV/config/error_urls_log", "w", encoding="utf-8"), logging.StreamHandler()])
def ping_url(url: str):
    hostname = urlsplit(url).hostname
    pinger = ping3.ping(hostname)
    if not pinger:
        if hostname not in invalid_hosts:
            invalid_hosts.add(hostname)
        logging.error(f"ping error code {url}")


if __name__ == "__main__":
    with open("py/TV/config/failed_urls.txt", 'r', encoding='utf-8') as f:
        future_to_url = {}
        invalid_hosts = set()
        warnings.filterwarnings('ignore')
        with concurrent.futures.ThreadPoolExecutor(max_workers = 512) as executor:
            for url in f:
                    try:
                        if url.startswith('http://') or url.startswith('https://'):
                            # future = executor.submit(requests.get, url, headers={}, timeout=15, verify=False)
                            future = executor.submit(ping_url, url)
                            future_to_url[future] = url
                    except subprocess.TimeoutExpired as e:
                        logging.error(f"check invalid_urls {url} code {e}")

                    except requests.exceptions.RequestException as e:
                        logging.error(f"check invalid_urls {url} code {e}")

                    except Exception as e:
                        logging.error(f"check invalid_urls {url} code {e}")

            try:
                for future in concurrent.futures.as_completed(future_to_url):
                    try:
                        url = future_to_url[future]
                        response = future.result(600)
                        if response.status_code != 200 and response.status_code != 403:
                            hostname = urlsplit(url).hostname
                            if hostname not in invalid_hosts:
                                invalid_hosts.add(hostname)
                            logging.error(f"Invalid status code {url} code {response.status_code}")

                    except Exception as e:
                        logging.info(f"url: {url} Processing took too long {e}")
            except Exception as e:
                logging.info(f"url: {url} Processing took too long {e}")

            with open("py/TV/config/error_urls_host_log", "w", encoding="utf-8") as error_urlsf:
                for invalid_host in invalid_hosts:
                    error_urlsf.write(f"{invalid_host}\n")
