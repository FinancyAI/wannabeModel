import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def wait_for_clickable(driver, by, value, timeout=20):
    """Waits until an element is clickable."""
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )


def accept_cookies(driver):
    try:
        # Wait for the agree button to be clickable
        agree_button = wait_for_clickable(driver, By.NAME, 'agree')
        # Attempt to click use JavaScript to perform the click
        try:
            agree_button.click()
        except Exception as e:
            driver.execute_script("arguments[0].click();", agree_button)
    except Exception as e:
        print("Error clicking agree button:", e)


def select_press_releases(driver):
    try:
        # Ensure the element is present before clicking
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, 'tab-press-releases'))
        )
        element.click()
    except Exception as e:
        print("Error navigating to press releases tab:", e)


def get_urls(driver):
    urls = []
    try:
        elements = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "a.subtle-link.fin-size-small.titles.noUnderline.svelte-wdkn18"))
        )
        urls = [element.get_attribute('href') for element in elements[:5]]
    except TimeoutException:
        print("Timeout while trying to fetch press release URLs")
    return urls


def clean_date(date_text):
    """Extracts the date from a string."""
    date_pattern = re.compile(r'(\w{3}, )?(\w{3} \d{1,2}, \d{4})(, \d{1,2}:\d{2} (AM|PM) GMT)?')
    match = date_pattern.search(date_text)
    return match.group(2) if match else "Date format error"


def extract_news(driver, url):
    """Extracts news from a given URL."""
    driver.get(url)
    title, date, body = "No Data Available", "No Data Available", "No Data Available"
    try:
        title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1[@data-test-locator='headline']")))
        title = title_element.text
        date_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.caas-attr-meta")))
        date = clean_date(date_element.text)
        body_paragraphs = driver.find_elements(By.CSS_SELECTOR, "div.caas-body p")
        body = ' '.join([paragraph.text for paragraph in body_paragraphs])
    except TimeoutException as e:
        print("Error extracting data:", e)
    return title, date, body


def scrape_data(tickers, base_url, driver):
    """Main scraping function to collect the news data from the webpages."""
    data_list = []
    for ticker in tickers:
        driver.get(base_url + ticker + "/")
        if ticker == tickers[0]:  # Handle cookie agreement once
            accept_cookies(driver)
        select_press_releases(driver)
        urls = get_urls(driver)
        for url in urls:
            title, date, body = extract_news(driver, url)
            data_list.append({'Ticker': ticker, 'Title': title, 'Date': date, 'Body': body})
    return pd.DataFrame(data_list)


if __name__ == "__main__":
    # Get ticker inputs
    ticker_input = input("Please enter the ticker symbols separated by a comma (e.g., AAPL, NFLX, AMZN): ")
    tickers = [ticker.strip() for ticker in ticker_input.split(',')]

    base_url = "https://finance.yahoo.com/quote/"

    # Initialize the WebDriver
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

    try:
        # Call the scrape_data function
        all_data = scrape_data(tickers, base_url, driver)
        # Save the DataFrame to a CSV file
        all_data.to_csv("output.csv", index=False)
        print(f"Data has been saved to output.csv")
    finally:
        driver.quit()