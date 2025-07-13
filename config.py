"""
Configuration file for Forks & Fortunes analysis
boring constants
"""

import os

class Config:
    """Configuration class containing all settings and constants
    Because hardcoding values throughout the codebase is for amateurs
    """
    
    CENSUS_API_KEY = 'nice_try_but_you_need_your_own_key'
    GOOGLE_API_KEY = "nice_try_but_youre_a_loser"
    
    # File paths
    DATA_DIR = "./data"
    MAPS_DIR = "./maps"
    RESULTS_DIR = "./results"
    ZILLOW_FILE = "Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
    
    # Analysis parameters
    RESTAURANT_SEARCH_RADIUS_KM = 10
    SEARCH_STEP_KM = 0.75
    # GOOGLE_API_DELAY = 1.2  # seconds between API calls sike
    MAX_API_PAGES = 10
    
    # Bay Area ZIP codes
    BAY_AREA_ZIPS = [
        # San Jose (951xx)
        '95110', '95112', '95113', '95116', '95117', '95118', '95119', '95120', '95121', '95122',
        '95123', '95124', '95125', '95126', '95127', '95128', '95129', '95130', '95131', '95132',
        '95133', '95134', '95135', '95136', '95138', '95139', '95148',
        # Santa Clara, Sunnyvale
        '95050', '95051', '95054', '94085', '94086', '94087', '94089',
        # Mountain View, Los Altos
        '94040', '94041', '94043', '94022', '94024',
        # Palo Alto & Stanford
        '94301', '94303', '94304', '94305',
        # Menlo Park, Atherton, Redwood City
        '94025', '94027', '94028', '94063', '94061', '94062', '94065',
        # Belmont, San Carlos, Foster City
        '94070', '94404', '94002',
        # San Mateo, Burlingame, Hillsborough
        '94401', '94402', '94403', '94010',
        # Millbrae, San Bruno, South SF, Daly City
        '94030', '94066', '94080', '94014', '94015',
        # San Francisco (941xx)
        '94102', '94103', '94104', '94105', '94107', '94108', '94109', '94110',
        '94111', '94112', '94114', '94115', '94116', '94117', '94118', '94121',
        '94122', '94123', '94124', '94127', '94129', '94130', '94131', '94132',
        '94133', '94134', '94158',
        # Oakland (946xx)
        '94601', '94602', '94603', '94605', '94606', '94607', '94608', '94609',
        '94610', '94611', '94612', '94618', '94619', '94621',
        # Berkeley (947xx)
        '94702', '94703', '94704', '94705', '94706', '94707', '94708', '94709', '94710',
        # East Bay
        '94536', '94538', '94539', '94541', '94542', '94544', '94545', '94546',
        '94552', '94555', '94560', '94577', '94578', '94579', '94580', '94586', '94587',
        # Marin County (949xx)
        '94901', '94903', '94904', '94920', '94925', '94930', '94939', '94941',
        '94945', '94947', '94949', '94960', '94965'
    ]
    
    # Cities to analyze - organized by wealth tier
    CITIES_TO_ANALYZE = [
        # Ultra-wealthy Peninsula cities
        "Atherton", "Portola Valley", "Hillsborough", "Los Altos",
        
        # High-wealth Peninsula cities  
        "Palo Alto", "Menlo Park", "Mountain View",
        
        # Upper-middle Peninsula cities
        "Redwood City", "San Carlos", "Belmont", "Foster City", "San Mateo",
        
        # Mid-tier Peninsula cities
        "Burlingame", "Millbrae", "San Bruno", "South San Francisco",
        
        # Urban comparison
        "San Francisco", "Daly City"
    ]
    
    # Test subset for quick testing
    TEST_CITIES = ["Atherton", "Menlo Park", "Palo Alto"]
    
    # Wealth tier groupings for analysis
    WEALTH_TIERS = {
        "ultra_wealthy": ["Atherton", "Portola Valley", "Hillsborough", "Los Altos"],
        "high_wealth": ["Palo Alto", "Menlo Park", "Mountain View"],
        "upper_middle": ["Redwood City", "San Carlos", "Belmont", "Foster City", "San Mateo"],
        "mid_tier": ["Burlingame", "Millbrae", "San Bruno", "South San Francisco"],
        "urban": ["San Francisco", "Daly City"]
    }
    
    # Census variables mapping
    CENSUS_VARIABLES = {
        'B25077_001E': 'median_home_value',
        'B25001_001E': 'housing_units',
        'B19013_001E': 'median_income',
        'B01003_001E': 'population'
    }
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories"""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        os.makedirs(cls.MAPS_DIR, exist_ok=True)
        os.makedirs(cls.RESULTS_DIR, exist_ok=True)
