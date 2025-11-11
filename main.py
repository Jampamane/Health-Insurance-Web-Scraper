from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import os


class HealthInsuranceScraper:

    def __init__(
        self,
        zip_code: int,
        full_time: bool,
        pay_frequency: str,
        coverage: str,
        age: int,
        expense_category: str,
        headless: bool = False,
    ) -> None:

        self.data = []

        self.zip_code = zip_code
        self.full_time = full_time
        self.pay_frequency = pay_frequency
        self.coverage = coverage
        self.age = age
        self.expense_category = expense_category

        self.options = Options()
        self.headless = headless
        if self.headless is True:
            self.options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=self.options)
        time.sleep(1)
        self.driver.get("https://www.checkbook.org/compareyourbenefits")
        time.sleep(1)
        while "https://www.checkbook.org/newhig2/hig.cfm" in self.driver.current_url:
            self.driver.quit()
            self.driver = webdriver.Chrome(options=self.options)
            time.sleep(1)
            self.driver.get("https://www.checkbook.org/compareyourbenefits")
            time.sleep(1)

    @property
    def plan_names(self):
        return (data["plan"] for data in self.data)

    def fill_information(self) -> None:

        # Zip code
        self.driver.find_element(By.ID, "Q6HN").send_keys(str(self.zip_code))

        # Enrollment category (GS-Full Time or Retired)
        if self.full_time is True:
            self.driver.find_element(By.ID, "Q1").send_keys("G")
        else:
            self.driver.find_element(By.ID, "Q1").send_keys("R")

        # Pay Frequency
        self.driver.find_element(By.ID, "qPayFrequency").send_keys(
            self.pay_frequency[0]
        )

        # Who will be covered
        self.driver.find_element(By.ID, "Q2").send_keys(self.coverage)

        # Age of primary insured
        self.driver.find_element(By.ID, "Q4").send_keys(str(self.age))

        # Healthcare expense category
        self.driver.find_element(By.ID, "Q5").send_keys(self.expense_category[0])

        time.sleep(1)
        self.driver.find_element(
            By.XPATH, "/html/body/section/div[2]/div/form/div[15]/div/input"
        ).click()
        time.sleep(2)

        if "https://www.checkbook.org/newhig2/hig.cfm" in self.driver.current_url:
            while self.recreate_driver() is False:
                pass

    def scrape(self) -> None:
        links = self.driver.find_elements(By.TAG_NAME, "a")

        limit_bool = False

        # Loop through the links and click those that match the pattern
        for link in links:
            href = link.get_attribute("href")
            if href and "compare.cfm?planIds=" in href:
                plan_name = link.text.strip()
                print(plan_name)

                if plan_name in self.plan_names:
                    continue

                link.click()
                time.sleep(1)  # Allow some time for navigation if needed
                if (
                    "https://www.checkbook.org/newhig2/hig.cfm"
                    in self.driver.current_url
                ):
                    return False
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, "html.parser")
                table = soup.find("table")

                for row in table.find_all("tr"):
                    cells = row.find_all("td")
                    cell_texts = [cell.get_text(strip=True) for cell in cells]
                    if limit_bool is True:
                        limit = next(
                            (text for text in cell_texts if "Limit" not in text), None
                        )
                        limit_bool = False

                    # Check if "biweekly cost" and a dollar amount are in the row
                    if "Biweekly Premium Cost" in cell_texts and any(
                        "$" in text for text in cell_texts
                    ):
                        biweekly_amount = next(
                            (text for text in cell_texts if "$" in text), None
                        )
                        biweekly_amount = biweekly_amount.replace("$", "")
                    elif "Deductible" in cell_texts and any(
                        "$" in text for text in cell_texts
                    ):
                        deductible = next(
                            (text for text in cell_texts if "$" in text), None
                        )
                        deductible = deductible.replace("$", "")
                    elif "Speech Therapy" in cell_texts:
                        copay = next(
                            (
                                text
                                for text in cell_texts
                                if "Speech Therapy" not in text
                            ),
                            None,
                        )
                        limit_bool = True

                self.data.append(
                    {
                        "plan": plan_name,
                        "biweekly_cost": biweekly_amount,
                        "deductible": deductible,
                        "copay": copay,
                        "limit": limit,
                    }
                )
                print(self.data)
                self.driver.back()
                time.sleep(1)
                if (
                    "https://www.checkbook.org/newhig2/hig.cfm"
                    in self.driver.current_url
                ):
                    return False

        time.sleep(5)
        return True

    def output_files(self):
        os.makedirs("output", exist_ok=True)

        with open("output/output.json", "w") as file:
            json.dump(self.data, file, indent=4)

        df = pd.DataFrame(self.data)
        df.to_csv("output/output.csv", index=False)

    def recreate_driver(self):
        self.driver.quit()
        self.driver = webdriver.Chrome(options=self.options)
        time.sleep(1)
        self.driver.get("https://www.checkbook.org/compareyourbenefits")
        time.sleep(1)
        if "https://www.checkbook.org/newhig2/hig.cfm" in self.driver.current_url:
            return False
        self.fill_information()
        if "https://www.checkbook.org/newhig2/hig.cfm" in self.driver.current_url:
            return False
        return True


def main():
    scraper = HealthInsuranceScraper(
        zip_code=20755,
        full_time=True,
        pay_frequency="Biweekly",
        coverage="Family of Three",
        age=26,
        expense_category="Average",
        headless=False,
    )
    scraper.fill_information()
    while scraper.scrape() is False:
        while scraper.recreate_driver() is False:
            pass
    scraper.output_files()


if __name__ == "__main__":
    main()
