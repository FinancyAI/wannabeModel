import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


def create_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    driver = webdriver.Chrome(options=options)
    return driver


def wait_for_element(driver, by, value, timeout=20):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )


def wait_for_clickable(driver, by, value, timeout=20):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )


def extract_management_discussion(html_content):
    pattern = re.compile(
        r'(Item\s*2\.\s*Management’s\s*Discussion\s*and\s*Analysis\s*of\s*Financial\s*Condition\s*and\s*Results\s*of\s*Operations.*?)'
        r'(Item\s*\d+|\Z)',
        re.DOTALL | re.IGNORECASE
    )

    match = pattern.search(html_content)
    if match:
        return match.group(1)
    else:
        return "Section not found."


def report_scraper(driver, cik, report_text):
    html_dic = {}

    try:
        driver.get("https://www.sec.gov/edgar/search/")
        WebDriverWait(driver, 20).until(EC.url_contains("sec.gov"))
        print(f"{cik}: Navigated to SEC EDGAR search page. Current URL: {driver.current_url}")

        input_button = wait_for_element(driver, By.XPATH, '//*[@id="entity-short-form"]')
        input_button.clear()
        input_button.send_keys(cik)
        print(f"{cik}: Cleared the main page and entered CIK")

        search_button = wait_for_clickable(driver, By.XPATH, '//*[@id="search"]')
        search_button.click()
        print(f"{cik}: Clicked the search button")
        time.sleep(3)

        keywords_input = wait_for_element(driver, By.XPATH, '//*[@id="keywords"]')
        keywords_input.clear()
        print(f"{cik}: Text Search Cleared")

        full_form_input = wait_for_element(driver, By.XPATH, '//*[@id="entity-full-form"]')
        full_form_input.send_keys(cik)
        print(f"{cik}: Send CIK keys to search bar")

        keywords_input = wait_for_clickable(driver, By.XPATH, '//*[@id="keywords"]')
        keywords_input.click()
        print(f"{cik}: Keywords input clicked")
        time.sleep(3)

        try:
            category_select = wait_for_clickable(driver, By.XPATH, '//*[@id="category-select"]')
            driver.execute_script("arguments[0].click();", category_select)
            print(f"{cik}: Clicked on report options")
        except Exception as e:
            print(f"{cik}: Failed to click on report options: {e}")

        all_reports_option = wait_for_clickable(driver, By.XPATH, '//*[@id="category-type-grp"]/ul/li[3]')
        driver.execute_script("arguments[0].click();", all_reports_option)
        print(f"{cik}: Selected All Reports option")

        search_button = wait_for_clickable(driver, By.XPATH, '//*[@id="search"]')
        driver.execute_script("arguments[0].click();", search_button)
        print(f"{cik}: Clicked search button for reports")
        time.sleep(3)

        try:
            report_link = wait_for_clickable(driver, By.XPATH, f"//a[contains(text(), '{report_text}')]")
            driver.execute_script("arguments[0].click();", report_link)
            print(f"{cik}: Clicked on the specified report link")
        except Exception as e:
            print(f"No {report_text} found for {cik}: {e}")
            return

        time.sleep(3)

        try:
            open_file_button = wait_for_clickable(driver, By.XPATH, '//*[@id="open-file"]/button')
            driver.execute_script("arguments[0].click();", open_file_button)
            print(f"{cik}: Opening the HTML report...")
        except Exception as e:
            print(f"Failed to find or click the open file button: {e}")
            return

        time.sleep(3)

        WebDriverWait(driver, 20).until(EC.number_of_windows_to_be(2))
        driver.switch_to.window(driver.window_handles[1])
        print(f"{cik}: Switched to the new tab")

        # Get the HTML content
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        all_text = soup.get_text(separator='\n')
        print(all_text)

        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    except Exception as e:
        print(f"An error occurred for cik {cik}: {e}")

    return


driver = create_driver()
report_scraper(driver, "0000320193", "10-Q (Quarterly report)")
