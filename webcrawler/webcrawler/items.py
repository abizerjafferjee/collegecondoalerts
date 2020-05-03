# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class WebcrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class Places4StudentsListingItem(scrapy.Item):
    college_name = scrapy.Field()
    website = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    address = scrapy.Field()
    city = scrapy.Field()
    province = scrapy.Field()
    country = scrapy.Field()
    postal_code = scrapy.Field()
    type_of_accomodation = scrapy.Field()
    rental_rate = scrapy.Field()
    occupancy_date = scrapy.Field()
    lease_types = scrapy.Field()
    lease_conditions = scrapy.Field()
    tenant_information_required = scrapy.Field()
    num_washrooms = scrapy.Field()
    rental_information = scrapy.Field()
    occupied_by_landlord = scrapy.Field()
    landlord_name = scrapy.Field()
    landlord_telephone = scrapy.Field()
    floor_plans = scrapy.Field()
    distance = scrapy.Field()
    listing_description = scrapy.Field()
    utilities = scrapy.Field()
    amenities = scrapy.Field()
    image_links = scrapy.Field()