# Importing relevant libraries
import asyncio
import csv
import json
import os
import re
from playwright.async_api import Playwright, async_playwright
from urllib.parse import urljoin

current_dir = os.path.dirname(os.path.realpath(__file__))
csv_links_path = os.path.join(current_dir, "sgcarmarttest.csv")  # -- to amend the csv filename accordingly
screenshot_folder = os.path.join(current_dir, "screenshots")
# create the screenshot folder if not present
os.makedirs(screenshot_folder, exist_ok=True)

links_filename = "sgcarmarttest.jsonl"   # -- to amend this filename accordingly
with open(links_filename) as f:
    links = [json.loads(line) for line in f]
# Appending "Done" key to each dict in the list of dicts
[dict.update({"Done": "No"}) for dict in links]

async def scrape(playwright: Playwright) -> None:
    browser = await playwright.chromium.launch(headless=True, timeout=0)
    context = await browser.new_context()
    page = await context.new_page()

    for link in links:
        if link["Done"] == "Yes":
            continue     
        try:
            await page.goto(link["url"], wait_until='networkidle')  # -- can also use 'domcontentload' or 'load'
            # Get the screenshot of the entire page
            await page.screenshot(path=os.path.join(screenshot_folder, f"{link['url']}_Full_Screenshot.png"), full_page=True)
            print(f"Screenshot of {link['url']} taken")

            # Update "Done" column in csv link file
            link["Done"] = "Yes"
            with open(csv_links_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=["Links", "Done"])
                writer.writeheader()
                writer.writerow(link)

        except (Exception, BaseException) as e:
            print(f"Error scraping {link['url']}: {e}")
