import re
import scrapy

from beta_scrapper.items import ScrapeURL
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from w3lib.url import url_query_cleaner

# This is the list of URL extensions that will be ignored by link extractor, to edit accordingly.
# For this use case, remove jpg and jpeg
ignored_extensions = ['7z', '7zip', 'bz2', 'rar', 'tar', 'tar.gz', 'xz', 'zip', 'mng', 'pct',
                      'bmp', 'gif', 'png', 'pst', 'psp', 'tif', 'tiff', 'ai',
                      'drw', 'dxf', 'eps', 'ps', 'svg', 'cdr', 'ico', 'mp3', 'wma', 'ogg', 'wav', 
                      'ra', 'aac', 'mid', 'au', 'aiff', '3gp', 'asf', 'asx', 'avi', 'mov', 'mp4', 
                      'mpg', 'qt', 'rm', 'swf', 'wmv', 'm4a', 'm4v', 'flv', 'webm', 'xls', 'xlsx',
                      'ppt', 'pptx', 'pps', 'doc', 'docx', 'odt', 'ods', 'odg', 'odp', 'css', 'pdf', 
                      'exe', 'bin', 'rss', 'dmg', 'iso', 'apk']


class CrawlingSpider(CrawlSpider):

    def __init__(self, delay=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setting the download delay at spider level instead of at global level. Crawler to wait delay sec between requests
        self.download_delay = int(delay)  # set to >0 sec if necessary to further throttle

    name = "CCCSspider"
    allowed_domains = ["sgcarmart.com", "i.i-sgcm.com"]  # "toscrape.com"
    start_urls = ["https://www.sgcarmart.com/directory/merchant_reviews.php?MID=11296"]  # https://books.toscrape.com/

    rules = (
            Rule(
                LinkExtractor(allow=[r"directory/merchant_reviews\.php\?.*?MID=11296.*?",
                                     r"directory/reviewphotos/11296"],
                              deny_extensions=ignored_extensions,
                              unique=True, strip=True),
                callback="parse_item",
                follow=True,
                # process_links="process_link",    #activate this if necessary
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
