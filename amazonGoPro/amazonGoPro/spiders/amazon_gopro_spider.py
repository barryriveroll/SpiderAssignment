import scrapy
import json
import os
dirname = os.path.dirname(__file__)

# Wipe existing file if it's there, or else create a new one. Prevents stacking multiple arrays of
# data when the spider is run multiple times.
new_json = open(os.path.join(dirname, '../../amazon_gopro.json'), 'w+')
id_list = []


class QuotesSpider(scrapy.Spider):
    name = "amazon_gopro"
    start_urls = [
        'https://www.amazon.com/GoPro-Fusion-Waterproof-Digital-Spherical/dp/B0792MJLNM/ref=sr_1_3?crid=D3C7EDM435E7&keywords=gopro+fusion&qid=1550442454&s=electronics&sprefix=GoPro+Fu%2Celectronics%2C1332&sr=1-3',
    ]

    def parse(self, response):

        for review in response.css('div.aok-relative'):

            # Store review ID as a variable to check if the review has already been scraped.
            # If the ID is not in the global array, the yield will run. Otherwise, print a
            # simple notification about the duplicate.
            new_id = review.css('div.review::attr(id)').get()
            if new_id not in id_list:
                id_list.append(new_id)
                yield {
                    'id': review.css('div.review::attr(id)').get(),
                    'title': review.css('a.review-title span::text').get(),
                    'date': review.css('span.review-date::text').get(),
                    'rating': review.css('span.a-icon-alt::text').get(),
                    'text': review.css('span.review-text-content span').get(),
                }
            else:
                print("DUPLICATE FOUND")

        # If there is an "all reviews" button, follow that URL and repeat the scraping.
        # This lets the spider work from the main item page, then continue on the "all reviews" page.
        all_reviews = response.css('div#reviews-medley-footer a.a-text-bold::attr(href)').get()
        if all_reviews is not None:
            all_reviews = response.urljoin(all_reviews)
            yield scrapy.Request(all_reviews, callback=self.parse)

        # The main item page doesn't have a "next page" target, but the "all reviews" pages do.
        # After the above "all reviews" callback runs the first time, the all_reviews variable will
        # be null and the following next_page variable will have a value.
        next_page = response.css('li.a-last a::attr(href)').get()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse)