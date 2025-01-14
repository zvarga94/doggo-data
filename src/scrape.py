import time
from pathlib import Path

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import hashlib

import logging

logger = logging.getLogger(__name__)


def download_images(container, path_out_dir):
    # Locate the parent container

    # Find all child div elements within the container
    all_divs = container.find_elements(By.XPATH, "./div")

    image_urls = []

    # Loop through each div and download images
    for div_index, div in enumerate(all_divs):
        try:
            images = div.find_elements(By.TAG_NAME, "img")
            for img_index, image in enumerate(images):
                try:
                    src = image.get_attribute("src")
                    image_urls.append(image_urls)
                    if src and src not in image_urls:  # If src is not None
                        response = requests.get(src)  # Download the image
                        if response.status_code == 200:
                            # Save the image with a unique name
                            path_img = path_out_dir / f"{div_index}_{img_index}.jpg"
                            with path_img.open("wb") as file:
                                file.write(response.content)
                            logger.info(f"Downloaded: {src}")
                except Exception as e:
                    logger.warning(f"Failed to download image in div[{div_index}]: {e}")
        except Exception as e:
            logger.warning(f"Failed to process div[{div_index}]: {e}")
    pass


def scrape_one_page(driver, href: str):
    uid = hashlib.md5(base_url.encode()).hexdigest()[0:8]

    driver.get(href)
    # time.sleep(3)

    xpaths = {
        "data": '//*[@id="bootstrap-panel"]/div[2]',  # data
        "description": '//*[@id="bootstrap-panel--2"]/div[2]',  # description
        "trait": '//*[@id="bootstrap-panel--3"]/div[2]',  # traits
        "behavior": '//*[@id="bootstrap-panel--4"]/div[2]',  # behaviour
        "table": '//*[@id="block-views-block-workflow-block-1"]/div/div/div/div',  # table
    }
    d = {k: driver.find_element(By.XPATH, v).text for k, v in xpaths.items()}
    d

    # Create a directory to save images
    path_out_dir = Path(f"slider_images/{uid}")

    path_out_dir.mkdir(parents=True, exist_ok=True)

    parent_container = driver.find_element(
        By.XPATH,
        '//*[@id="slick-media-24301-slide-full-width-colorbox-1-slider"]/div/div',
    )

    download_images(parent_container, path_out_dir)
    print()


if __name__ == "__main__":

    options = Options()
    options.add_argument("--headless")
    # options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)

    page_indices = range(0, 100)
    base_url = "https://www.tappancs.hu/gazdit-keresunk/archivum/orokbefogadott-tappancsos-kutyak?page="

    # per dog

    base_url = "https://www.tappancs.hu/gazdit-keresunk/archivum/orokbefogadott-tappancsos-kutyak/kali"

    scrape_one_page(driver, base_url)

    # generate uid from base url

    for page_index in page_indices:
        url = base_url + str(page_index)

        driver.get(url)

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
            driver.get(link)

            bla = '//*[@id="bootstrap-panel"]/div[2]'
            bla2 = driver.find_element(By.XPATH, bla)
            bla2.get_attribute("href")

            time.sleep(3)
