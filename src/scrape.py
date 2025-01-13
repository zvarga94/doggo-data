import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

if __name__ == "__main__":

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)

    page_indices = range(0, 100)
    base_url = "https://www.tappancs.hu/gazdit-keresunk/archivum/orokbefogadott-tappancsos-kutyak?page="

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

            time.sleep(3)
