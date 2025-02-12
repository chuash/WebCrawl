# Importing relevant libraries
import asyncio
import csv
import json
import os
import re
from playwright.async_api import Playwright, async_playwright
from urllib.parse import urljoin

current_dir = os.path.dirname(os.path.realpath(__file__))

# Declare the csv filepath that would capture urls that have been successfully screenshot
completed_links_filepath = os.path.join(current_dir, "sgcarmartlinks.csv")  # -- to amend the csv filename accordingly
# Declare the directory that would contain the url screenshots
screenshot_folderpath = os.path.join(current_dir, "screenshots")

# create the screenshot folder, if not present
os.makedirs(screenshot_folderpath, exist_ok=True)
# create the completed links csv file with headers, if not present
if not os.path.exists(completed_links_filepath):
    with open(completed_links_filepath, mode='a', newline='') as file:                            
        writer = csv.DictWriter(file, fieldnames=["URL", "Done"])
        writer.writeheader()

# specify the jsonl file that contains the crawled urls
links_filename = "sgcarmartlinks.jsonl"   # -- to amend this filename accordingly
# Loading the content in the jsonl file
with open(links_filename, mode='r') as f:
    links = [json.loads(line) for line in f]
# Appending "Done" key to each dict in the list of dicts
[dict.update({"Done": "No"}) for dict in links]

async def get_screenshot(context, link):
    
    # navigate to the relevant url and wait till page is fully loaded
    page = await context.new_page()
    await page.goto(link["URL"], wait_until='networkidle')  # -- can also use 'domcontentload' or 'load'
    
    # Save the screenshot of the entire page, then close the page
    await page.screenshot(path=os.path.join(screenshot_folder, f"{(link["URL"])}_Full_Screenshot.png"), full_page=True)
    page.close()
    
    # Update the Done status
    link["Done"] = "Yes"
    
    # Update the completed links csv file
    with open(completed_links_filepath, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["URL", "Done"])
        writer.writerow(link)

    print(f"Screenshot of {(link["URL"])} taken")
    
async def main(links):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, timeout=5)
        context = await browser.new_context()
        # create all tasks
        tasks = [asyncio.create_task(get_screenshot(context, link)) for link in links if link["Done"] == "No"]
        # wait for each task to complete
        for task in asyncio.as_completed(tasks):
            try:
                await task
            except (Exception, BaseException) as e:
                print(f"Failed with: {e}")
        
if __name__ == '__main__':
    asyncio.run(main(links))
