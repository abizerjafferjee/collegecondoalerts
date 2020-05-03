import pymongo
import pprint
import re
from datetime import datetime
from difflib import SequenceMatcher
from processors import places4studentsSchema

def clean_text(text):
    """
    remove characters excluding (0-9, A-Z, a-z, -.,_)
    """
    text = re.sub('[^A-Za-z0-9.,-_ ]+', '', text.lower())
    return text

def compare_strings(string_a, string_b):
    comparison_ratio = SequenceMatcher(None, string_a, string_b).ratio()
    if comparison_ratio > 0.85:
        return True
    return False

class Places4StudentsProcessor():

    def __init__(self):
        self.db = self.get_db()
        self.read_collection = self.db['webcrawler']
        self.write_collection = self.db['processed']
        self.processed_data = self.prepare_data()
        self.write_to_db()
    
    def get_db(self):
        client = pymongo.MongoClient('mongodb://localhost:27017/')
        db = client['collegecondoalerts']
        return db

    def write_to_db(self):
        # delete previous data in processed_data
        self.write_collection.remove({})
        for record in self.processed_data:
            self.write_collection.insert(record)

    def prepare_data(self):
        all_data = self.read_collection.find({})
        processed_data = []
        for record in all_data:
            self.current_record = record
            num_rental_options = len(self.current_record['rental_information'])
            if num_rental_options != 0:
                for i in range(num_rental_options):
                    processed_record = self.process_record(option=i)
                    processed_data.append(processed_record)
            else:
                processed_record = self.process_record()
                processed_data.append(processed_record)
        return processed_data
        
    def process_record(self, option=None):
        """
        returns processed dictionary with this info:
        - lease information
        - location
        - accomodation
        - listing information
        """
        use_rental_option = False # if rental_info empty
        if option:
            self.current_record['rental_information'] = self.current_record['rental_information'][option]
            use_rental_option = True
        
        _record = {}

        _record['url'] = self.current_record['url']
        _record['title'] = self.parse_title(use_rental_option)

        _record['lease information'] = {
            'landlord name': clean_text(self.current_record['landlord_name']),
            'landlord telephone': clean_text(self.current_record['landlord_telephone']),
            'rental rate': self.parse_rental_rate(use_rental_option),
            'occupancy date': self.parse_occupancy_date(use_rental_option)
        }

        _record['lease information']['tenant information required'] = self.parse_func([['tenant_information_required']],
                                                                                      places4studentsSchema.LEASE_REQUIREMENTS,
                                                                                      dict)

        _record['lease information']['lease condition'] = self.parse_func([['lease_conditions']],
                                                                          places4studentsSchema.LEASE_CONDITIONS,
                                                                          dict)

        _record['lease information']['lease type'] = self.parse_func([['lease_types']],
                                                                     places4studentsSchema.LEASE_TYPES,
                                                                     list)

        _record['location'] = {
            'address': clean_text(self.current_record['address']),
            'city': clean_text(self.current_record['city']),
            'province': clean_text(self.current_record['province']),
            'country': clean_text(self.current_record['country']),
            'postal_code': clean_text(self.current_record['postal_code']),
            'campus': clean_text(self.current_record['college_name'])
        }
        _record['location']['distance'],\
        _record['location']['duration by walking'],\
        _record['location']['duration by bicycling'],\
         _record['location']['duration by driving']\
        = self.parse_distance()

        _record['accomodation'] = {
            'occupied by landlord': self.parse_landlord_occupied(),
            'features': {
                'allow pets': self.parse_pets(),
                'allow smoking': self.parse_smoking()
            }
        }

        _record['accomodation']['number of rooms'] = self.parse_func([['type_of_accomodation']],
                                                                     places4studentsSchema.NUM_BEDROOMS,
                                                                     list)

        _record['accomodation']['accomodation type'] = self.parse_func([['type_of_accomodation']],
                                                                       places4studentsSchema.HOUSE_TYPES,
                                                                       list)

        if use_rental_option:
            _record['accomodation']['number of washrooms'] = self.parse_func(
                                                                [['rental_information', 'Bath']],
                                                                places4studentsSchema.NUM_WASHROOMS,
                                                                list)
        else:
            _record['accomodation']['number of washrooms'] = self.parse_func(
                                                                [['num_washrooms']],
                                                                places4studentsSchema.NUM_WASHROOMS,
                                                                list)

        for key, val in self.parse_features().items():
            _record['accomodation']['features'][key] = val

        _record['listing information'] = {
            'contains images': self.has_images(),
            'contains floor plans': self.has_floor_plans(),
            'image links': self.current_record['image_links'],
            'floor plans': self.current_record['floor_plans']
        }
        # get information from description and add it to features

        return _record
    
    def parse_features(self):
        """
        parse utilities and amenities together
        """
        utilities = self.current_record['utilities']
        if len(utilities) > 0:
            if isinstance(utilities[0], list):
                utilities = utilities[0]

        utilties = [clean_text(utility) for utility in utilities]

        amenities = self.current_record['amenities']
        if len(amenities) > 0:
            if isinstance(amenities[0], list):
                amenities = amenities[0]

        amenities = [clean_text(amenity) for amenity in amenities]
        features = amenities + utilities

        feature_list = {
            'electricity': ['electricity'],
            'water': ['water'],
            'garbage pickup': ['garbage pickup'],
            'gas': ['gas'],
            'heat': ['heat'],
            'includes parking': ['includes parking'],
            'free air conditioning': ['free air conditioning', 'air conditioning'],
            'refrigerator': ['refrigerator'],
            'bus route': ['bus route'],
            'common laundry': ['common laundry'],
            'stove': ['stove'],
            'parking': ['parking driveway', 'parking', 'parking garage'],
            'all inclusive': ['all inclusive'],
            'hardwood floors': ['hardwood floors'],
            'in unit washing machine': ['washing machine in unit', 'washing machine'],
            'in unit dryer': ['dryer in unit'],
            'microwave': ['microwave'],
            'internet': ['internet', 'high speed internet included', 'free internet'],
            'storage space': ['storage space', 'storage spaces'],
            'furnished': ['furnished'],
            'bike storage': ['bike storage in unit'],
            'dish washer': ['dishwasher'],
            'tv cable': ['tv cable included'],
            'carpeted floors': ['carpeted floors'],
            'outdoor area': ['outdoor area']
        }

        features_available = {}
        for label, all_strings in feature_list.items():
            for string in all_strings:
                for feature in features:
                    if compare_strings(string, feature):
                        features_available[label] = True
                        break
                if label in features_available:
                    break
            if label not in features_available:
                features_available[label] = False

        return features_available

    def has_images(self):
        images = self.current_record['image_links']
        if len(images) > 0:
            return True
        return False

    def has_floor_plans(self):
        floor_plans = self.current_record['floor_plans']
        if len(floor_plans) > 0:
            return True
        return False

    def parse_landlord_occupied(self):
        text = clean_text(self.current_record['occupied_by_landlord'])
        if 'no' in text:
            return False
        return True

    def parse_pets(self):
        find_strings = ['no pets']
        lease_condition_text = clean_text(self.current_record['lease_conditions'])
        lease_description_text = clean_text(self.current_record['listing_description'])
        for string in find_strings:
            if string in lease_condition_text:
                return False
            elif string in lease_description_text:
                return False
        return True

    def parse_smoking(self):
        find_strings = ['no smoking']
        lease_condition_text = clean_text(self.current_record['lease_conditions'])
        lease_description_text = clean_text(self.current_record['listing_description'])
        for string in find_strings:
            if string in lease_condition_text:
                return False
            elif string in lease_description_text:
                return False
        return True

    def parse_title(self, use_rental_option):
        if use_rental_option:
            title_text = clean_text(self.current_record['rental_information']['title'])
        else:
            title_text = clean_text(self.current_record['title'])
        return title_text
    
    def parse_occupancy_date(self, use_rental_option):
        if use_rental_option:
            date_text = clean_text(self.current_record['rental_information']['Occupancy Date'])
        else:
            date_text = clean_text(self.current_record['occupancy_date'])
        date_text = date_text.replace(',', '').replace(' 0', ' ').replace(' ', '-').strip()
        try:
            return str(datetime.strptime(date_text, '%B-%d-%Y').date())
        except:
            return date_text

    def parse_distance(self):
        distance = clean_text(self.current_record['distance']['distance']).split()
        duration_by_walking = clean_text(self.current_record['distance']['duration_by_walking']).split()
        duration_by_bicycling = clean_text(self.current_record['distance']['duration_by_bicycling']).split()
        duration_by_driving = clean_text(self.current_record['distance']['duration_by_driving']).split()
        _distance = {'magnitude': distance[0], 'measure': distance[1]} if distance else {}
        _duration_by_walking = {'magnitude': duration_by_walking[0], 'measure': duration_by_walking[1]} if duration_by_walking else {}
        _duration_by_bicycling = {'magnitude': duration_by_bicycling[0], 'measure': duration_by_bicycling[1]} if duration_by_bicycling else {}
        _duration_by_driving = {'magnitude': duration_by_driving[0], 'measure': duration_by_driving[1]} if duration_by_driving else {}
        return _distance, _duration_by_walking, _duration_by_bicycling, _duration_by_driving
    
    def parse_rental_rate(self, use_rental_option):
        if use_rental_option:
            return {
                'min rent': clean_text(self.current_record['rental_information']['Min Rent']),
                'max rent': clean_text(self.current_record['rental_information']['Max Rent']),
                'currency': 'cdn',
                'frequency': None,
            }
        else:
            rate_text = clean_text(self.current_record['rental_rate'])
            if rate_text != '':
                currencies = ['cdn']
                currency = ''
                for curr in currencies:
                    if curr in rate_text:
                        currency = curr
                
                frequencies = ['per month', 'per room / month']
                frequency = ''
                for freq in frequencies:
                    if freq in rate_text:
                        frequency = freq
                
                r = re.compile('^[0-9].+$')
                rates = rate_text.split()
                rates = list(filter(r.match, rates))
                min_rate, max_rate = None, None
                if len(rates) == 1:
                    min_rate = rates[0]
                    max_rate = rates[0]
                elif len(rates) == 2:
                    min_rate = rates[0]
                    max_rate = rates[1]

                return {
                    'min rent': min_rate,
                    'max rent': max_rate,
                    'currency': currency,
                    'frequency': frequency
                }
                return min_rate, max_rate, currency, frequency
            else:
                return {
                    'min rent': None,
                    'max rent': None,
                    'currency': None,
                    'frequency': None
                }
    
    def parse_func(self, fields, schema, output_type):
        """
        general parse function
        """
        if output_type == list:
            output = []
        elif output_type == dict:
            output = {}

        for field in fields:
            text = clean_text(self.get_text(field))

            for key, variables in schema.items():
                for variable in variables:

                    if output_type == list:
                        if variable in text:
                            output.append(key)
                            break

                    elif output_type == dict:
                        if variable in text:
                            output[key] = True
                            break
                        else:
                            output[key] = False

        return output

    def get_text(self, field):
        """
        get nested field
        """
        output = self.current_record
        for f in field:
            output = output[f]
        return output

if __name__ == "__main__":
    Places4StudentsProcessor()