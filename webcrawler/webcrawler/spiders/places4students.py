"""
TODO:
- Add logger
- Why are all listings not being extracted? They were before
- Add scheduler
- Run on docker or server
"""

# -*- coding: utf-8 -*-
import os
import json
from time import sleep

import scrapy
from scrapy.selector import Selector

import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from ..items import Places4StudentsListingItem
from scrapy.utils.project import get_project_settings

settings = get_project_settings()
basepath = os.path.dirname(__file__)

class Places4studentsSpider(scrapy.Spider):
    name = 'places4students'
    # college urls
    start_urls = ['https://www.places4students.com/Places/PropertyListings?SchoolID=VBThwOQPAX4=']
    college_names = {
        'VBThwOQPAX4': 'university of waterloo'
    }
    file_name = 'test.json'

    def parse(self, response):
        """
        main function to scrape a college's property listings
        """
        if settings['ENV'] == 'dev':
            driver = webdriver.Chrome(
                os.path.abspath(os.path.join(basepath, '../../chromedriver'))
            )
        
        elif settings['ENV'] == 'prod':
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')

            driver = webdriver.Chrome(settings['CHROME_DRIVER'], chrome_options=chrome_options)
            
        college_id = self.get_college_id(response.url)
        college_name = self.college_names[college_id]

        driver.get(response.url)
        property_links = self.get_property_listings_per_college(driver)

        for link in property_links:
            property_listing = self.get_data_from_property_listing(driver, link)
            property_listing['college_name'] = college_name
            property_listing['website'] = 'www.places4students.com'

            yield property_listing
            
        driver.close()

    def get_college_id(self, url):
        """
        return the id of the college from url
        """
        _url = url.replace('%3d', '=').split('=')
        if _url[-1] == '':
            return _url[-2]
        return _url[-1]

    def get_property_listings_per_college(self, driver):
        """
        return dictionary of property links for each page for a school
        """
        # accept page terms & conditions
        sleep(1)
        button = driver.find_element_by_xpath('//*[@id="MainContent_btnAgere"]').click()
        sleep(10)

        property_links = []

        # process first page
        property_links += self.get_page_property_listings(driver)
        # loop through remaining pages
        next_pages = self.get_next_pages(driver)
        num_pages = len(next_pages)//2
        current_page = 0
        while current_page < num_pages:
            page_button = next_pages[current_page].click()
            sleep(10)
            property_links += self.get_page_property_listings(driver)
            next_pages = self.get_next_pages(driver)
            current_page += 1

        return property_links

    def get_page_property_listings(self, driver):
        """
        return list of property listing urls from a page
        """
        listings = driver.find_elements_by_xpath('//*[@class="listing-title"]/a')
        links = [listing.get_attribute("href") for listing in listings]
        return links

    def get_next_pages(self, driver):
        """
        return next pages elements
        """
        return driver.find_elements_by_xpath('//*[@class="PagerStyle"]/td/table/tbody/tr/td/a')
        
    def driver_get(self, driver, xpath, attribute, **kwargs):
        """
        get the attribute at given xpath
        """
        try:
            if attribute == 'text':
                element = driver.find_element_by_xpath(xpath)
                text = element.text
                if 'child_xpath' in kwargs:
                    child_text = driver.find_element_by_xpath(xpath+kwargs['child_xpath']).text
                    return text.replace(child_text, '')
                elif 'parent_xpath' in kwargs:
                    parent_text = element.find_element(By.XPATH, kwargs['parent_xpath']).text
                    return parent_text.replace(text, '')

                return text
        except Exception as e:
            # print(str(e))
            return ''

    def get_from_column_lists(self, driver, xpaths):
        """
        return list of utilities or amenities from property listing
        """
        _list = []
        for xpath in xpaths:
            elements = driver.find_elements_by_xpath(xpath)
            for element in elements:
                try:
                    _list.append(element.find_element_by_class_name('p4stext').text)
                except Exception as e:
                    pass
                
        return _list

    def get_image_links(self, driver, xpath):
        """
        return list of image urls in property listing
        """
        elements = driver.find_elements_by_xpath(xpath)
        img_list = [element.get_attribute('src') for element in elements]
        return img_list

    def get_rental_information(self, driver, xpath):
        """
        get rental information block
        """
        accordion_extract = []
        # if driver.find_element_by_xpath(xpath):
        number = 1
        go = True
        while go:
            try:
                xpath_template = f'//*[@id="MainContent_rptApartment_divAccordianItem_{str(number)}"]'
                driver.find_element_by_xpath(xpath_template+'/h3').click()
                data = {}
                data['title'] = driver.find_element_by_xpath(xpath_template+'/h3').text
                div_block = driver.find_elements_by_xpath(xpath_template+'/div/div')
                div_num = 1
                for div in div_block:
                    div_title = driver.find_element_by_xpath(xpath_template+f'/div/div[{div_num}]/span').text
                    div_body = driver.find_element_by_xpath(xpath_template+f'/div/div[{div_num}]')\
                                                            .text.replace(div_title, '')
                    data[div_title] = div_body
                    div_num += 1
                accordion_extract.append(data)
                number += 1
            except Exception as e:
                go = False

        return accordion_extract

    def get_unit_floor_plan(self, driver):
        """
        get floor plan links
        """
        floor_plans = {}
        number = 0
        go = True
        while go:
            try:
                xpath_template = f'//*[@id="MainContent_grdUnitFloorPlan_lnkUnitFloorPlan_{number}"]'
                plan_name =driver.find_element_by_xpath(xpath_template).text 
                plan_link = driver.find_element_by_xpath(xpath_template).get_attribute("href")
                floor_plans[plan_name] = plan_link
                number += 1
            except Exception as e:
                go = False

        return floor_plans

    def get_distance_to_campus(self, driver):
        """
        get distance to campus block
        """
        try:
            block_titles = blocks = driver.find_elements_by_xpath('//*[@id="MainContent_tblDistDuration"]/table/tbody[1]/tr/td/i')
            blocks = driver.find_elements_by_xpath('//*[@id="MainContent_tblDistDuration"]/table/tbody[2]/tr/td')
            data = {}
            for i, title in enumerate(block_titles):
                title_text = title.get_attribute('title').lower().replace(' ', '_')
                data[title_text] = blocks[i].text
            return data
        except Exception as e:
            return {}

    def get_data_from_property_listing(self, driver, listing_url):
        """
        extract information from property listing html
        """
        sleep(5)
        listing_url = listing_url.replace('%3d', '=')
        driver.get(listing_url)

        item = Places4StudentsListingItem()

        item['url'] = listing_url
        item['title'] = self.driver_get(driver, '//*[@id="MainContent_detailsTitle"]', 'text')
        item['address'] = self.driver_get(driver, '//*[@id="MainContent_Label3"]', 'text', parent_xpath='..')
        item['city'] = self.driver_get(driver, '//*[@id="MainContent_trCity"]', 'text', child_xpath='/span')
        item['province'] = self.driver_get(driver, '//*[@id="MainContent_trProvince"]', 'text', child_xpath='/span')
        item['country'] = self.driver_get(driver, '//*[@id="MainContent_trCountry"]', 'text', child_xpath='/span')
        item['postal_code'] = self.driver_get(driver, '//*[@id="MainContent_trZip"]', 'text', child_xpath='/span')
        item['type_of_accomodation'] = self.driver_get(driver, '//*[@id="MainContent_Label21"]', 'text', parent_xpath='..')
        item['rental_rate'] = self.driver_get(driver, '//*[@id="MainContent_trRental"]', 'text', child_xpath='/span')
        item['occupancy_date'] = self.driver_get(driver, '//*[@id="MainContent_Label25"]', 'text', parent_xpath='..')
        item['lease_types'] = self.driver_get(driver, '//*[@id="MainContent_trLeaseType"]', 'text', child_xpath='/span')
        item['lease_conditions'] = self.driver_get(driver, '//*[@id="MainContent_trLeaseCondition"]', 'text', child_xpath='/span')
        item['tenant_information_required'] = self.driver_get(driver, '//*[@id="MainContent_trRequired"]', 'text', child_xpath='/span')
        item['num_washrooms'] = self.driver_get(driver, '//*[@id="MainContent_litWashTitle"]', 'text', parent_xpath='..')
        item['rental_information'] = self.get_rental_information(driver, '//*[@id="MainContent_elApartment"]')
        item['occupied_by_landlord'] = self.driver_get(driver, '//*[@id="MainContent_trLandLordOccupied"]', 'text', child_xpath='/span')
        item['landlord_name'] = self.driver_get(driver, '//*[@id="MainContent_lbLandlordName"]', 'text', parent_xpath='..')
        item['landlord_telephone'] = self.driver_get(driver, '//*[@id="MainContent_lbLandlordTel1"]', 'text', parent_xpath='..')
        item['floor_plans'] = self.get_unit_floor_plan(driver)
        item['distance'] = self.get_distance_to_campus(driver)
        item['listing_description'] = self.driver_get(driver, '//*[@id="MainContent_elDesc"]/div/div[1]', 'text')
        item['utilities'] = self.get_from_column_lists(driver, ['//*[@id="MainContent_ulUtiliesLeft"]/li',
                                            '//*[@id="MainContent_ulUtiliesRight"]/li']),
        item['amenities'] = self.get_from_column_lists(driver, ['//*[@id="MainContent_ulAmenitiesLeft"]/li',
                                            '//*[@id="MainContent_ulAmenitiesRight"]/li']),
        item['image_links'] = self.get_image_links(driver, '//*[@id="mycarousel_listingCarousel"]/li/img')

        return item