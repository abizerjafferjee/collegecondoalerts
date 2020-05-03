# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import os
import sys
import pymongo
from scrapy.utils.project import get_project_settings
from scrapy.exceptions import DropItem
dirpath = os.path.dirname(__file__)
sys.path.append(os.path.join('..', dirpath))
from processors import places4students

settings = get_project_settings()

class WebcrawlerPipeline(object):
    def process_item(self, item, spider):
        return item

class MongoDBPipeline(object):
    def __init__(self):
        connection = pymongo.MongoClient(
            settings['MONGODB_SERVER'],
            settings['MONGODB_PORT']
        )
        db = connection[settings['MONGODB_DB']]
        self.collection = db[settings['MONGODB_COLLECTION']]

    def process_item(self, item, spider):
        """
        write items to this collection
        """
        valid = True
        # for data in item:
        #     if not data:
        #         valid = False
        #         raise DropItem("Missing {}!".format(data))
        if valid:
            self.collection.insert(dict(item))
            print("listing added")
        return item
    
    def open_spider(self, spider):
        """
        delete all the data in this collection
        """
        self.collection.remove({})

    def close_spider(self, spider):
        """
        trigger another process that processes
        the new data in this collection
        """
        places4students.Places4StudentsProcessor()