import numpy as np
import pandas as pd
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import time

# Set up Chrome options
options = webdriver.ChromeOptions()
#options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = uc.Chrome(options=options)

driver.get("https://www.sec.gov/edgar/search/")

ticker_list = ['AAPL']
text = "10-Q (Quarterly report)"


def report_scraper(ticker_list, report_text):
    html_dic = {}
    for ticker in ticker_list:
        try:
            # Ensure the search input is available
            input_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="entity-short-form"]'))
            )
            input_button.clear()
            input_button.send_keys(ticker)
            print("Cleared the main page")

            # Click the search button
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="search"]'))
            )
            search_button.click()

            time.sleep(3)

            print("Searching...")

            # Clear the text search bar
            keywords_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="keywords"]'))
            )
            keywords_input.clear()

            # Inputting Ticker in ticker search bar
            full_form_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="entity-full-form"]'))
            )
            full_form_input.send_keys(ticker)

            # Clicking the keyword input to free the cursor for the next steps.
            keywords_input.click()
            print("Searche button clicked")

            time.sleep(3)

            # Interacting with the dropdown menu
            category_select = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="category-select"]'))
            )
            category_select.click()

            # Choosing All Reports options
            all_reports_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="category-type-grp"]/ul/li[3]'))
            )
            all_reports_option.click()

            print("Looking for reports...")

            # Clicking the search bar now
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="search"]'))
            )
            search_button.click()

            time.sleep(3)

            # Clicking on the specified report
            try:
                report_link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{report_text}')]"))
                )
                report_link.click()
            except Exception as e:
                print(f"No {report_text} found for {ticker}: {e}")
                continue

            time.sleep(3)

            # Opening the document in another tab
            open_file_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="open-file"]/button'))
            )
            open_file_button.click()

            print("Opening the HTML report...")
            time.sleep(3)

            # Switch to the new tab
            WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
            driver.switch_to.window(driver.window_handles[1])

            # Save HTML Content to the dictionary
            html_dic[ticker] = driver.page_source
            print("Report successfully saved to dictionary.")

            # Close the new tab and switch back to the original tab
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        except Exception as e:
            print(f"An error occurred for ticker {ticker}: {e}")

    return html_dic


print(report_scraper(ticker_list, text))
driver.quit()
