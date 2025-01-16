import time
from pathlib import Path

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import hashlib

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_images(container, path_out_dir):
    all_divs = container.find_elements(By.XPATH, "./div")

    image_urls = []

    for div_index, div in enumerate(all_divs):
        try:
            images = div.find_elements(By.TAG_NAME, "img")
            for img_index, image in enumerate(images):
                try:
                    src = image.get_attribute("src")
                    if src and src not in image_urls:
                        response = requests.get(src)
                        if response.status_code == 200:
                            path_img = path_out_dir / f"{div_index}_{img_index}.jpg"
                            with path_img.open("wb") as file:
                                file.write(response.content)
                            logger.info(f"Downloaded: {src}")
                            image_urls.append(src)
                except Exception as e:
                    logger.warning(f"Failed to download image in div[{div_index}]: {e}")
        except Exception as e:
            logger.warning(f"Failed to process div[{div_index}]: {e}")
    pass


def scrape_one_page(driver, href: str):
    logger.info(f"Scraping {href}")

    uid = hashlib.md5(base_url.encode()).hexdigest()[0:8]

    driver.get(href)
    time.sleep(3)

    xpaths = {
        "data": '//*[@id="bootstrap-panel"]/div[2]',
        "description": '//*[@id="bootstrap-panel--2"]/div[2]',
        "trait": '//*[@id="bootstrap-panel--3"]/div[2]',
        "behavior": '//*[@id="bootstrap-panel--4"]/div[2]',
        "table": '//*[@id="block-views-block-workflow-block-1"]/div/div/div/div',
    }
    d = {k: driver.find_element(By.XPATH, v).text for k, v in xpaths.items()}

    path_out_dir = Path(f"slider_images/{uid}")

    path_out_dir.mkdir(parents=True, exist_ok=True)

    parent_container = driver.find_element(
        By.XPATH,
        '//*[@id="slick-media-24301-slide-full-width-colorbox-1-slider"]/div/div',
    )

    download_images(parent_container, path_out_dir)
    return d


if __name__ == "__main__":

    options = Options()
    # options.add_argument("--headless")
    # options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)

    page_indices = range(0, 100)
    base_url = "https://www.tappancs.hu/gazdit-keresunk/archivum/orokbefogadott-tappancsos-kutyak?page="

    l_d = []

    for page_index in page_indices:
        logger.info(f"Scraping page {page_index}")

        url = base_url + str(page_index)

        driver.get(url)
        time.sleep(3)

        links = driver.find_elements(
            By.XPATH, '//*[@id="block-views-block-tappancs-dogs-block-5"]//a'
        )

        links_dog = [
            link.get_attribute("href")
            for link in links
            if "gazdit-keresunk" in link.get_attribute("href")
        ]
        links_dog = [link for link in links_dog if "page" not in link]
        links_dog = list(set(links_dog))

        for link in links_dog:
            try:
                l_d.append(scrape_one_page(driver, link))
            except Exception as e:
                logger.warning(f"Failed to scrape {link}: {e}")
            time.sleep(3)
