from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import pandas as pd
import json
import time

def main():
    # Setup Selenium WebDriver
    # chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Run headless (without GUI)
    # chrome_service = ChromeService("path/to/chromedriver")  # Specify path to your chromedriver

    # driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    driver = webdriver.Chrome()

    try:
        # Navigate to a webpage
        driver.get("https://www.checkbook.org/compareyourbenefits")
        
        # Optional: Wait for dynamic content to load
        time.sleep(2)  # Adjust depending on the page's load time

        # Locate the input field by its name, ID, or another attribute
        # Example using ID
        driver.find_element(By.ID, "Q6HN").send_keys("20755")  # Replace with actual ID
        driver.find_element(By.ID, "Q1").send_keys("G")# Replace with actual ID
        driver.find_element(By.ID, "qPayFrequency").send_keys("B")# Replace with actual ID
        driver.find_element(By.ID, "Q2").send_keys("Family of Three")# Replace with actual ID
        driver.find_element(By.ID, "Q4").send_keys("25")# Replace with actual ID
        driver.find_element(By.ID, "Q5").send_keys("A")# Replace with actual ID
        time.sleep(1)
        driver.find_element(By.CLASS_NAME, "btn").click()# Replace with actual ID



        # Optionally submit the form if needed
        # input_field.send_keys(Keys.ENTER)

        # Pause to observe (if not headless)
        time.sleep(5)

        links = driver.find_elements(By.TAG_NAME, "a")

        limit_bool = False
        data = []

        # Loop through the links and click those that match the pattern
        for link in links:
            href = link.get_attribute("href")
            if href and "compare.cfm?planIds=" in href:
                plan_name = link.text.strip()
                print(plan_name)
                link.click()
                time.sleep(1)  # Allow some time for navigation if needed
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, "html.parser")
                table = soup.find("table")

                for row in table.find_all("tr"):
                    cells = row.find_all("td")
                    cell_texts = [cell.get_text(strip=True) for cell in cells]
                    if limit_bool is True:
                        limit = next((text for text in cell_texts if "Limit" not in text), None)
                        limit_bool = False
                    
                    # Check if "biweekly cost" and a dollar amount are in the row
                    if "Biweekly Premium Cost" in cell_texts and any("$" in text for text in cell_texts):
                        biweekly_amount = next((text for text in cell_texts if "$" in text), None)
                        biweekly_amount = biweekly_amount.replace("$", "")
                    elif "Deductible" in cell_texts and any("$" in text for text in cell_texts):
                        deductible = next((text for text in cell_texts if "$" in text), None)
                        deductible = deductible.replace("$", "")
                    elif "Speech Therapy" in cell_texts:
                        copay = next((text for text in cell_texts if "Speech Therapy" not in text), None)
                        limit_bool = True

                data.append({"plan": plan_name,"biweekly_cost": biweekly_amount, "deductible": deductible, "copay": copay, "limit": limit})
                driver.back()  # Go back to the previous page after clicking
                time.sleep(1)  # Allow time for the page to reload


        time.sleep(5)

        # Convert JSON to DataFrame
        output_file = "output.json"

        with open(output_file, "w") as file:
            json.dump(data, file, indent=4)

        
        # Extract page source
        # page_source = driver.page_source

        # Parse with BeautifulSoup
        # soup = BeautifulSoup(page_source, "html.parser")

        # Example: Extract all links
        # links = soup.find_all("a")
        # for link in links:
        #     print(link.get("href"))

    finally:
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    main()