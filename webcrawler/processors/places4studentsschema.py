NUM_BEDROOMS = {
                '1 bedroom': ['1 bedroom'],
                '2 bedrooms': ['2 bedrooms'],
                '3 bedrooms': ['3 bedrooms', '2 or more bedrooms'],
                'greater than 3 bedrooms': ['3 or more bedrooms', '5 bedrooms',
                                            '5 or more bedrooms', 'or more bedrooms']
                }


NUM_WASHROOMS = {
                '1 (or 1.5) washroom': ['1', '1.5'],
                '2 (or 2.5) washrooms': ['1.5'],
                '3 washrooms': ['3'],
                'greater than 3 washrooms': ['3.5', '4', '5', '6']
                }

HOUSE_TYPES = {
                'house': ['house'],
                'townhouse': ['townhouse'],
                'duplex': ['duplex'],
                'apartment': ['apartment'],
                'condo': ['condo'],
                'student residence': ['student residence']
              }

LEASE_TYPES = {
                '4 months': ['4 months'],
                '12 months': ['12 months'],
                '24 months or more': ['24 months or more'],
                'month to month': ['month to month'],
                'any': ['any']
              }

LEASE_CONDITIONS = {
    'first and last month deposit': ['first month and last month deposit', 'first and last month deposit'],
    'one occupant per room': ['1 occupant per room']
}

LEASE_REQUIREMENTS = {
    'guarantor required': ['guarantor', 'guarantors'],
    'reference required': ['reference'],
    'credit check required': ['credit check']
}