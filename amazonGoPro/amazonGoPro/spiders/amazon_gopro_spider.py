import scrapy
import json
import os
import pymongo
from scrapy.conf import settings

class QuotesSpider(scrapy.Spider):
    name = "amazon_gopro"
    user_agent = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'
    start_urls = [
        'https://www.amazon.com/GoPro-Fusion-Waterproof-Digital-Spherical/dp/B0792MJLNM/ref=sr_1_3?crid=D3C7EDM435E7&keywords=gopro+fusion&qid=1550442454&s=electronics&sprefix=GoPro+Fu%2Celectronics%2C1332&sr=1-3',
    ]

    # Initial start URL is used to pull in the source which is split at the second forward slash
    # and the product ID which comes from index 3 of the same split.
    uri_split = start_urls[0].split('/')[2:]
    source = uri_split[0]
    product_id = uri_split[3]
    id_list = []

    def __init__(self):
        # Initialize MongoDB, settings from settings.py
        # Only the products collection is used here and the reviews collection is used in pipelines.py
        connection = pymongo.MongoClient(
            settings['MONGODB_SERVER'],
            settings['MONGODB_PORT']
        )
        db = connection[settings['MONGODB_DB']]
        self.collection = db[settings['MONGODB_PRODUCTS_COLLECTION']]

    def parse(self, response):
        for review in response.css('div.aok-relative'):
            yield {
                'review_id': review.css('div.review::attr(id)').get(),
                'product_id': self.product_id,
                'title': review.css('a.review-title span::text').get(),
                'date': review.css('span.review-date::text').get(),
                'rating': review.css('span.a-icon-alt::text').get(),
                'text': review.css('span.review-text-content span').get(),
            }

        # If there is an "all reviews" button, follow that URL and repeat the scraping.
        # This lets the spider work from the main item page, then continue on the "all reviews" page.
        all_reviews = response.css('div#reviews-medley-footer a.a-text-bold::attr(href)').get()
        if all_reviews is not None:
            
            # Check to see if a strikeout MSRP exists. If it does, that will be used in the object for the database.
            # If it doesn't, which means there is no sale price, the MSRP is grabbed from a different element.
            msrp = response.css('span.priceBlockStrikePriceString::text').get()
            if msrp is None:
                msrp = response.css('span#priceblock_ourprice::text').get()

            review_count = response.css('span#acrCustomerReviewText::text').get().split(' ', 1)
            review_count = review_count[0]

            # Product data added to database in this location because this if conditional is only ever met once,
            # when the start URL is first scraped since the all_reviews variable is null after the first page.
            product_data = {
                'name': response.css('span#productTitle::text').get(),
                'brand': response.css('a#bylineInfo::text').get(),
                'source': self.source,
                'msrp': msrp,
                'sale_price': response.css('span#priceblock_pospromoprice::text').get(),
                'description': response.css('div#productDescription p::text').get(),
                'rating_avg': response.css('i.a-icon-star span.a-icon-alt::text').get(),
                'total_reviews': review_count,
            }

            # When adding the product data to the database, upsert allows the update method to act like an
            # insert/create if the document does not exist.
            self.collection.update({'name': product_data['name']}, product_data, upsert=True)
            all_reviews = response.urljoin(all_reviews)
            yield scrapy.Request(all_reviews, callback=self.parse)

        # The main item page doesn't have a "next page" target, but the "all reviews" pages do.
        # After the above "all reviews" callback runs the first time, the all_reviews variable will
        # be null and the following next_page variable will have a value.
        next_page = response.css('li.a-last a::attr(href)').get()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse)