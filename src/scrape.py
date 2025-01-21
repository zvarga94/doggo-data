import hashlib
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional

import requests
from requests import Session
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_images(
    container,
    output_dir: Path,
    session: Session,
) -> List[str]:
    """
    Download all <img> elements found within each <div> of the container.
    """

    all_divs = container.find_elements(By.XPATH, "./div")
    downloaded_urls = set()

    for div_index, div in enumerate(all_divs):
        try:
            images = div.find_elements(By.TAG_NAME, "img")
            for img_index, image in enumerate(images):
                src = image.get_attribute("src")
                if src and src not in downloaded_urls:

                    try:
                        response = session.get(src, timeout=10)

                        if response.status_code == 200:
                            image_path = output_dir / f"{div_index}_{img_index}.jpg"

                            with image_path.open("wb") as file:
                                file.write(response.content)

                            logger.info(f"Downloaded: {src}")
                            time.sleep(1)
                            downloaded_urls.add(src)
                        else:
                            logger.warning(
                                f"Image URL responded with status {response.status_code}: {src}"
                            )
                    except Exception as e:
                        logger.warning(f"Failed to download image {src}: {e}")
        except Exception as e:
            logger.warning(f"Failed to process div[{div_index}]: {e}")

    return list(downloaded_urls)


def scrape_one_page(
    driver: webdriver.Chrome,
    page_url: str,
    session: Session,
    path_out: Path,
) -> Dict:
    """
    Scrape text fields and images from a single dog's page.
    """
    logger.info(f"Scraping {page_url}")
    uid = hashlib.md5(page_url.encode()).hexdigest()[:8]

    driver.get(page_url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="bootstrap-panel"]'))
        )
    except Exception as e:
        logger.warning(f"Timeout or problem waiting for main panel on {page_url}: {e}")

    xpaths = {
        "data": '//*[@id="bootstrap-panel"]/div[2]',
        "description": '//*[@id="bootstrap-panel--2"]/div[2]',
        "trait": '//*[@id="bootstrap-panel--3"]/div[2]',
        "behavior": '//*[@id="bootstrap-panel--4"]/div[2]',
        "table": '//*[@id="block-views-block-workflow-block-1"]/div/div/div/div',
    }

    page_data = {}
    for key, xp in xpaths.items():
        try:
            element = driver.find_element(By.XPATH, xp)
            page_data[key] = element.text
        except Exception as e:
            logger.warning(f"Could not find element for '{key}': {e}")
            page_data[key] = None

    path_out_img = path_out / uid
    path_out_img.mkdir(parents=True, exist_ok=True)

    try:
        parent_container = driver.find_element(
            By.XPATH,
            '//*[starts-with(@id, "slick-media-") and contains(@id, "slide-full-width-colorbox-1")]',
        )
        downloaded = download_images(parent_container, path_out_img, session)
        page_data["downloaded_urls"] = downloaded
    except Exception as e:
        logger.warning(f"Could not find or process parent_container on {page_url}: {e}")
        page_data["downloaded_urls"] = []

    page_data["uid"] = uid
    page_data["page_url"] = page_url

    return page_data


def find_last_page(driver: webdriver.Chrome, base_url: str) -> Optional[int]:
    """
    Find the last page number in the pagination to know how many archive pages exist.
    """

    driver.get(base_url)

    xpath = '//*[@id="block-views-block-tappancs-dogs-block-5"]/div/div/nav/ul/li[11]/a'
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
    except Exception as e:
        logger.warning(f"Timeout or problem waiting for main panel: {e}")

    try:
        last_page_link = driver.find_element(By.XPATH, xpath)
        last_page_url = last_page_link.get_attribute("href")
        last_page_number = int(last_page_url.split("=")[-1])
        logger.info(f"Discovered last page index: {last_page_number}")
        return last_page_number
    except Exception as e:
        logger.warning(f"Could not find last page number: {e}")
        return


def scrape_pages(
    driver: webdriver.Chrome,
    base_url: str,
    path_out: Path,
    scraped_pages: Optional[List[str]] = None,
    session: Session = None,
) -> List[Dict]:
    """
    Scrape multiple archive pages, each containing links to individual dog pages.
    """

    if session is None:
        session = requests.Session()

    if scraped_pages is None:
        scraped_pages = []

    all_dogs_data = []

    last_page = find_last_page(driver, base_url)
    if last_page is None:
        logger.warning("No last page discovered. Defaulting to only page 0.")
        last_page = 1

    for page_index in range(0, last_page + 1):
        url = f"{base_url}{page_index}"
        logger.info(f"Scraping archive page {page_index}: {url}")
        try:
            driver.get(url)

            xpath_links = '//*[@id="block-views-block-tappancs-dogs-block-5"]//a'
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, xpath_links))
                )
            except Exception as e:
                logger.warning(
                    f"Timeout or problem waiting for link container on page {page_index}: {e}"
                )

            links = driver.find_elements(By.XPATH, xpath_links)
            dog_links = [
                link.get_attribute("href")
                for link in links
                if "gazdit-keresunk" in link.get_attribute("href")
            ]
            dog_links = [link for link in dog_links if "page" not in link]
            dog_links = list(set(dog_links))

            logger.info(f"Found {len(dog_links)} dog links on page {page_index}")

            for link in dog_links:
                if link in scraped_pages:
                    logger.info(f"Skipping already scraped link: {link}")
                    continue

                try:
                    data = scrape_one_page(driver, link, session, path_out)
                    all_dogs_data.append(data)
                except Exception as e:
                    logger.warning(f"Failed to scrape {link}: {e}")
                finally:
                    time.sleep(3)
        except Exception as e:
            logger.warning(f"Failed to load archive page {url}: {e}")

    return all_dogs_data


def main():
    """
    Main entry point to scrape the Tappancs website for adoptable dogs
    (archived) and save results to JSON.
    """
    options = Options()
    # options.add_argument("--headless")
    # options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)
    session = requests.Session()

    try:
        base_url = "https://www.tappancs.hu/gazdit-keresunk/archivum/orokbefogadott-tappancsos-kutyak?page="

        path_out = Path("scraped_data")
        path_out.mkdir(parents=True, exist_ok=True)
        output_json_path = path_out / "dogs_data_raw.json"

        if output_json_path.exists():
            with output_json_path.open("r", encoding="utf-8") as f:
                old_data = json.load(f)
            scraped_pages = [d["page_url"] for d in old_data]
            logger.info(f"Loaded {len(old_data)} existing dog pages.")
        else:
            old_data = []
            scraped_pages = []

        new_data = scrape_pages(
            driver=driver,
            base_url=base_url,
            path_out=path_out,
            scraped_pages=scraped_pages,
            session=session,
        )
        logger.info(f"Scraped {len(new_data)} new dog pages in total.")

        # Merge new data with old data and save to JSON
        merged_data = old_data + new_data
        with output_json_path.open("w", encoding="utf-8") as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=4)
        logger.info(f"Saved merged dog data to {output_json_path.resolve()}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
