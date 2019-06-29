import pymongo
from scrapy.conf import settings


class AmazongoproPipeline(object):
    def __init__(self):
        # Initialize MongoDB connection. These settings come from the settings.py file.
        connection = pymongo.MongoClient(
            settings['MONGODB_SERVER'],
            settings['MONGODB_PORT']
        )
        db = connection[settings['MONGODB_DB']]
        self.collection = db[settings['MONGODB_REVIEWS_COLLECTION']]

    def process_item(self, item, spider):
        valid = True

        if valid:
            # Add reviews to DB. 'upsert=True' allows MongoDB to see if the entry already exists based
            # on the given query. If it does exist, it works like a regular update. If it doesn't exist,
            # it works like an insert and will create the new document.
            self.collection.update({'review_id': item['review_id']}, item, upsert=True)

        return item
