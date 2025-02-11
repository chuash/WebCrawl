import os
import csv
import asyncio
from selectolax.parser import HTMLParser
from dataclasses import dataclass
from urllib.parse import urljoin
import re
from ftfy import fix_text
from playwright.async_api import Playwright, async_playwright
import pandas as pd

current_dir = os.path.dirname(os.path.realpath(__file__))
csv_reviews_path = os.path.join(current_dir, "lambency_reviews.csv")
csv_links_path = os.path.join(current_dir, "lambency_links.csv")
screenshot_path = os.path.join(current_dir, "screenshots")
xlsx_reviews_path = os.path.join(current_dir, "lambency_reviews.xlsx")

@dataclass
class Response:
    body_html: HTMLParser
    next_page_exists: bool = False


async def scrape(playwright: Playwright) -> None:
    browser = await playwright.chromium.launch(headless=True, timeout=0)
    context = await browser.new_context()
    page = await context.new_page()

    # Read links from lambency_links.csv
    with open(csv_links_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        links = list(reader)

    page_number = 1
    count = 0

    for row_number, link in enumerate(links, start=1):
        if link["Done"] == "Yes":
            continue

        page_number = row_number

        try:
            await page.goto(link["Links"])
            await page.wait_for_selector("div[id^='comments']", state='visible', timeout=5000)
            print("Reviews found!")
            page_content = await page.content()
            html = HTMLParser(page_content)

            # Wait for the ad to close by itself (Only appears on the first time you visit the website)
            if page_number == 1:
                await asyncio.sleep(20)

            headers = ["Reviewer", "Reviewer Description", "Title", "Date", "Overall Score", "Technical Expertise", 
                       "Customer Service", "Value for money", "Outlet Experience", "Review Body", "Photos", "Page"]
            
            page_folder = os.path.join(screenshot_path, f"Page_{page_number}")
            os.makedirs(page_folder, exist_ok=True)
            with open(csv_reviews_path, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                if file.tell() == 0:
                    writer.writerow(headers)

                index = 0
                for review in html.css("div[id^='comments']"):
                    review_id = review.attributes.get('id', '')
                    reviewer_details = extract_info(html, "div#memberSummary", index)
                    review_title_and_date_and_ratings = extract_info(html, "div.commenttitle", index)
                    review_text_and_photo = extract_info(html, "div.commenttext", index)

                    reviewer_name = extract_reviewer_name(reviewer_details)
                    reviewer_desc = extract_reviewer_desc(reviewer_details)
                    review_title = extract_title(review_title_and_date_and_ratings)
                    review_date = extract_date(review_title_and_date_and_ratings)
                    review_score_overall = extract_review_score(review_id, html, reviewer_desc)
                    review_score_individual = extract_score_components(review_title_and_date_and_ratings)
                    review_number_of_photos = extract_number_of_photos(review_text_and_photo)
                    review_text = extract_review_content(review_number_of_photos, review_text_and_photo)
                    review_title = fix_text(review_title)
                    review_text = fix_text(review_text)

                    row = [
                        reviewer_name,
                        reviewer_desc,
                        review_title,
                        review_date,
                        float(review_score_overall) if review_score_overall else None,
                        float(review_score_individual.get("Technical Expertise")) if review_score_individual.get("Technical Expertise") else None,
                        float(review_score_individual.get("Customer Service")) if review_score_individual.get("Customer Service") else None,
                        float(review_score_individual.get("Value for money")) if review_score_individual.get("Value for money") else None,
                        float(review_score_individual.get("Outlet Experience")) if review_score_individual.get("Outlet Experience") else None,
                        review_text,
                        review_number_of_photos,
                        page_number
                    ]
                    writer.writerow(row)

                    # If there is a photo, extract the href and screenshot the link directly
                    if review_number_of_photos != 0:
                        for i in range(review_number_of_photos):
                            # Extract the href of the first img element in the comment text
                            photo_link = page.locator(f'//div[@id="{review_id}"]//div[@class="commenttext"]//table//tr//td[{i * 2 + 1}]//a//img')

                            # Get the href attribute of the link containing the image
                            href = await photo_link.locator('..').get_attribute('href')
                            
                            new_page = await context.new_page()
                            await new_page.goto(href)
                            await new_page.wait_for_load_state('networkidle')
                            await new_page.screenshot(path=os.path.join(page_folder, f"Review {index + 1} ({reviewer_name})_Photo_Screenshot_{i + 1}.png"))
                            await new_page.close()

                    index += 1

                # Get the screenshot of the entire page
                await page.screenshot(path=os.path.join(page_folder, f"Page_{page_number}_Full_Screenshot.png"), full_page=True)
                print("Screenshot of whole page taken")
            
            ## For testing
            # if index != 15:
            #    raise ValueError("Number of reviews should be 15!")

            # Update "Done" column in lambency_links.csv
            link["Done"] = "Yes"
            with open(csv_links_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=["Links", "Done"])
                writer.writeheader()
                writer.writerows(links)

            count += index
            print(f"Page {page_number} successfully scraped.")
            print(f"Total reviews: {count}")

        except Exception as e:
            print(f"Error scraping {link['Links']}: {e}")