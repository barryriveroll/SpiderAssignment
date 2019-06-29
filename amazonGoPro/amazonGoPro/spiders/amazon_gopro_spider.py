import scrapy
from scrapy.exceptions import DropItem

class QuotesSpider(scrapy.Spider):
    name = "amazon_gopro"
    start_urls = [
        'https://www.amazon.com/GoPro-Fusion-Waterproof-Digital-Spherical/dp/B0792MJLNM/ref=sr_1_3?crid=D3C7EDM435E7&keywords=gopro+fusion&qid=1550442454&s=electronics&sprefix=GoPro+Fu%2Celectronics%2C1332&sr=1-3',
    ]

    def parse(self, response):
        for review in response.css('div.aok-relative'):
            yield {
                'id': review.css('div.review::attr(id)').get(),
                'title': review.css('a.review-title span::text').get(),
                'date': review.css('span.review-date::text').get(),
                'rating': review.css('span.a-icon-alt::text').get(),
                'text': review.css('span.review-text-content span').get(),
            }

        all_reviews = response.css('div#reviews-medley-footer a.a-text-bold::attr(href)').get()
        if all_reviews is not None:
            all_reviews = response.urljoin(all_reviews)
            yield scrapy.Request(all_reviews, callback=self.parse)

        next_page = response.css('li.a-last a::attr(href)').get()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse)