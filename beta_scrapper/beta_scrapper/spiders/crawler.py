import scrapy

from beta_scrapper.items import ScrapeURL
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from w3lib.url import url_query_cleaner


class CrawlingSpider(CrawlSpider):

    name = "betacrawler"
    # Setting the download delay at spider level instead of at global level. Crawler to wait x sec between
    # requests
    download_delay = 0  # set to 1 sec if necessary to further throttle
    allowed_domains = ["toscrape.com"]
    start_urls = ["https://books.toscrape.com/"]
    rules = (
        Rule(
            LinkExtractor(allow="catalogue", unique=True, strip=True),
            callback="parse_item",
            follow=True,
            #process_links="process_link",    #activate this if necessary
        ),
    )

    def parse_item(self, response):
        item = ScrapeURL()
        item["url"] = response.url  # response.meta["link_text"]
        return item

    def process_link(self, links):
        # remove query strings, if any, from urls
        if links:
            for link in links:
                link.url = url_query_cleaner(link.url)
                yield link
        else:
            pass


# process = CrawlerProcess(
#    settings={
#        "FEEDS": {
#            "items.json": {"format": "json"},
#        },
#    }
# )

# process.crawl(MySpider)
# process.start()

# Need to set the depth limit
