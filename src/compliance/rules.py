"""
Legal Metrology compliance requirements.

This module contains the declarations that the analyzer
currently checks.

IMPORTANT:
These are automated first-pass checks only. A detected
declaration does not establish legal compliance.
"""

MANDATORY_DECLARATIONS = {
    "manufacturer_packer_importer": {
        "label": "Name & address of manufacturer/packer/importer",
        "description": "Manufacturer, packer or importer name and address",
    },
    "net_quantity": {
        "label": "Net quantity (weight/volume/number)",
        "description": "Declared net quantity of the commodity",
    },
    "manufacture_date": {
        "label": "Month & year of manufacture/packing",
        "description": "Month and year of manufacture or packing",
    },
    "mrp": {
        "label": "Retail Sale Price (MRP), inclusive of taxes",
        "description": "Maximum Retail Price",
    },
    "consumer_care": {
        "label": "Consumer care details (contact for complaints)",
        "description": "Consumer complaint/contact details",
    },
}

CONDITIONAL_DECLARATIONS = {
    "country_of_origin": {
        "label": "Country of origin (mandatory only for imported goods)",
        "description": "Country of origin for imported goods",
    },
}

MANUAL_REVIEW_DECLARATIONS = {
    "generic_name": {
        "label": "Generic/common name of the commodity",
        "description": "Generic or common name of the packaged commodity",
    },
}
