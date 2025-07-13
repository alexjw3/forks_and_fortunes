"""
Data collection utilities for Forks & Fortunes analysis
"""

import pandas as pd
from census import Census
from geopy.geocoders import Nominatim
from tqdm import tqdm
import logging
from typing import Tuple, Optional

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCollector:
    """Handles all data collection from various APIs and sources"""
    
    def __init__(self):
        self.config = Config
        self.census = Census(self.config.CENSUS_API_KEY)
        self.geolocator = Nominatim(user_agent="forks-fortunes-analysis")
        
    def collect_census_data(self) -> pd.DataFrame:
        """Collect Census ACS data for Bay Area ZIP codes"""
        logger.info("📊 Collecting Census data...")
        
        zip_data = []
        failed_zips = []
        
        for zip_code in tqdm(self.config.BAY_AREA_ZIPS, desc="ZIP codes"):
            try:
                res = self.census.acs5.get(
                    list(self.config.CENSUS_VARIABLES.keys()),
                    {'for': f'zip code tabulation area:{zip_code}'}
                )
                if res:
                    entry = res[0]
                    entry['zip'] = zip_code
                    zip_data.append(entry)
            except Exception as e:
                failed_zips.append(zip_code)
                logger.warning(f"Failed to get data for ZIP {zip_code}: {e}")
                continue
        
        # Convert to DataFrame
        df = pd.DataFrame(zip_data)
        df.rename(columns=self.config.CENSUS_VARIABLES, inplace=True)
        
        # Convert numeric fields
        for col in self.config.CENSUS_VARIABLES.values():
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df[['zip'] + list(self.config.CENSUS_VARIABLES.values())]
        
        logger.info(f"✅ Collected data for {len(df)} ZIP codes")
        if failed_zips:
            logger.warning(f"⚠️ Failed for {len(failed_zips)} ZIP codes: {failed_zips[:5]}...")
        
        return df
    
    def load_zillow_data(self, filepath: str) -> pd.DataFrame:
        """Load and process Zillow ZHVI data"""
        logger.info("🏠 Loading Zillow ZHVI data...")
        
        try:
            zillow_df = pd.read_csv(filepath)
            
            # Debug: print column information
            logger.info(f"Zillow CSV columns: {list(zillow_df.columns)}")
            logger.info(f"Zillow CSV shape: {zillow_df.shape}")
            
            # Filter for California
            zillow_df = zillow_df[zillow_df['State'] == 'CA'].copy()
            
            # Get most recent month's ZHVI - look for date patterns
            # Standard Zillow format is YYYY-MM
            date_columns = [col for col in zillow_df.columns if '-' in col and len(col) == 7 and col[:4].isdigit()]
            
            # If no standard format, look for any date-like columns
            if not date_columns:
                date_columns = [col for col in zillow_df.columns if '-' in col and len(col) >= 6]
            
            # If still none, look for numeric columns that could be dates
            if not date_columns:
                date_columns = [col for col in zillow_df.columns 
                              if str(col).replace('-', '').replace('_', '').replace('.', '').isdigit() 
                              and len(str(col)) >= 6]
            
            logger.info(f"Found date columns: {date_columns[:5] if len(date_columns) > 5 else date_columns}")
            
            if date_columns:
                # Sort to get the latest month
                latest_month = sorted(date_columns)[-1]
                logger.info(f"Selected latest month column: {latest_month}")
                
                # Create zhvi_latest column
                zillow_df['zhvi_latest'] = pd.to_numeric(zillow_df[latest_month], errors='coerce')
                logger.info(f"Using ZHVI data from {latest_month}")
                
                # Check if we got valid data
                valid_count = zillow_df['zhvi_latest'].notna().sum()
                logger.info(f"Valid ZHVI values: {valid_count} out of {len(zillow_df)}")
                
            else:
                logger.error("No date columns found - checking all available columns")
                all_cols = list(zillow_df.columns)
                logger.info(f"All available columns: {all_cols}")
                
                # As a fallback, look for any column that might contain home values
                potential_value_cols = [col for col in all_cols if any(term in col.lower() for term in ['zhvi', 'value', 'price'])]
                if potential_value_cols:
                    logger.info(f"Found potential value columns: {potential_value_cols}")
                    # Use the last one as latest
                    latest_col = potential_value_cols[-1]
                    zillow_df['zhvi_latest'] = pd.to_numeric(zillow_df[latest_col], errors='coerce')
                    logger.info(f"Using fallback column: {latest_col}")
            
            # Clean up - only include zhvi_latest if it was successfully created
            if 'zhvi_latest' in zillow_df.columns:
                zillow_df = zillow_df[['RegionName', 'City', 'zhvi_latest']].copy()
                zillow_df.rename(columns={'RegionName': 'zip'}, inplace=True)
                zillow_df['zip'] = zillow_df['zip'].astype(str).str.zfill(5)
                
                # Filter for Bay Area ZIPs
                zillow_df = zillow_df[zillow_df['zip'].isin(self.config.BAY_AREA_ZIPS)].copy()
                zillow_df = zillow_df.sort_values('zhvi_latest', ascending=False)
            else:
                logger.error("No date columns found in Zillow data - check file format")
                return pd.DataFrame()
            
            logger.info(f"✅ Loaded Zillow data for {len(zillow_df)} Bay Area ZIP codes")
            return zillow_df
            
        except FileNotFoundError:
            logger.error(f"❌ Zillow file not found: {filepath}")
            logger.info("Please download the Zillow ZHVI data and update the file path in Config.ZILLOW_FILE")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"❌ Error loading Zillow data: {e}")
            return pd.DataFrame()
    
    def get_city_center(self, city_name: str, state_code: str = 'CA') -> Tuple[Optional[float], Optional[float]]:
        """Get city center coordinates"""
        try:
            location = self.geolocator.geocode(f"{city_name}, {state_code}")
            if not location:
                raise ValueError(f"Could not find center for {city_name}")
            return location.latitude, location.longitude
        except Exception as e:
            logger.error(f"Error getting coordinates for {city_name}: {e}")
            return None, None
    
    def save_census_data(self, df: pd.DataFrame, filename: str = "census_zip_data.csv") -> str:
        """Save census data to CSV"""
        filepath = f"{self.config.DATA_DIR}/{filename}"
        df.to_csv(filepath, index=False)
        logger.info(f"💾 Saved census data to {filepath}")
        return filepath
    
    def load_existing_census_data(self, filename: str = "census_zip_data.csv") -> Optional[pd.DataFrame]:
        """Load existing census data if available"""
        filepath = f"{self.config.DATA_DIR}/{filename}"
        try:
            df = pd.read_csv(filepath)
            logger.info(f"📖 Loaded existing census data from {filepath}")
            return df
        except FileNotFoundError:
            logger.info(f"No existing census data found at {filepath}")
            return None
        except Exception as e:
            logger.error(f"Error loading census data: {e}")
            return None


if __name__ == "__main__":
    # Test the data collector
    Config.create_directories()
    collector = DataCollector()
    
    # Test census data collection
    census_df = collector.collect_census_data()
    print(f"\nCensus data shape: {census_df.shape}")
    print(census_df.head())
    
    # Test Zillow data loading
    zillow_df = collector.load_zillow_data(Config.ZILLOW_FILE)
    if not zillow_df.empty:
        print(f"\nZillow data shape: {zillow_df.shape}")
        print(zillow_df.head())
