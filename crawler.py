import os
from time import sleep

import requests
from urllib.parse import urlparse

import undetected_chromedriver as uc

from selenium.webdriver.chromium.options import ChromiumOptions
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# NIX
# import shutil
# BROWSER_PATH = shutil.which("chromium")
# DRIVER_PATH = shutil.which("undetected-chromedriver")

TIMEOUT = 5
URL = "https://ci.android.com/builds/branches/aosp-llvm-toolchain/grid?legacy=1"


def main():
    options = ChromiumOptions()
    options.add_argument(
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    )
    # options.binary_location = BROWSER_PATH
    driver = uc.Chrome(
        headless=True,
        options=options,
        use_subprocess=False,
        version_main=135
        # driver_executable_path=DRIVER_PATH,
    )

    print("Stage 1")
    # Stage 1: Find build
    driver.get(URL)
    grid_page_app = WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.TAG_NAME, "grid-page-app"))).shadow_root
    # not very much i can do there, i guess? we need to wait for several shadow roots to be fully rendered
    sleep(TIMEOUT)
    build_grid = grid_page_app.find_element(By.CSS_SELECTOR, "build-grid").shadow_root
    href = build_grid.find_element(By.CSS_SELECTOR, "a[href*='/llvm_linux/latest']").get_attribute("href")
    build_id = href.split("/")[-3]
    print(f"Build ID: {build_id}")
    with open("build_id", "w") as f:
        f.write(build_id)

    print("Stage 2")
    # Stage 2: Get artifact
    driver.get(href)
    artifact_page_app = WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.TAG_NAME, "artifact-page-app"))).shadow_root
    sleep(TIMEOUT)
    artifact_list = artifact_page_app.find_element(By.CSS_SELECTOR, "artifact-list").shadow_root
    artifacts = artifact_list.find_elements(By.CSS_SELECTOR, "artifact-folder")
    for artifact in artifacts:
        try:
            href = artifact.shadow_root.find_element(By.CSS_SELECTOR, f"a[href*='clang-{build_id}']").get_attribute("href")
            break
        except NoSuchElementException:
            continue

    if href is None:
        print("Failed to find prebuilt clang!")
        exit(1)

    print("Stage 3")
    # Stage 3: Download artifact
    driver.get(href)
    artifact_viewer_app = WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.TAG_NAME, "artifact-viewer-app"))).shadow_root
    sleep(TIMEOUT)
    artifact_viewer = artifact_viewer_app.find_element(By.CSS_SELECTOR, "artifact-viewer").shadow_root
    href = artifact_viewer.find_element(By.CSS_SELECTOR, "a[href^='https://storage.googleapis.com'").get_attribute("href")

    print(f"We got the URL: {href}")

    save_artifact(href)
    driver.quit()

def save_artifact(url: str):
    print("Saving artifact...")
    response = requests.get(url, stream=True)
    response.raise_for_status()

    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)

    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Downloaded as: {filename}")


if __name__ == "__main__":
    main()
