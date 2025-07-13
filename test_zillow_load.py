"""
Simple test for Zillow data loading
"""

from config import Config
from data_collector import DataCollector
import logging

logging.basicConfig(level=logging.INFO)

def test_zillow_loading():
    """Test just the Zillow data loading"""
    print("🧪 Testing Zillow Data Loading")
    print("=" * 40)
    
    # Create directories
    Config.create_directories()
    
    # Initialize collector
    collector = DataCollector()
    
    # Test Zillow loading
    print(f"Loading Zillow file: {Config.ZILLOW_FILE}")
    zillow_df = collector.load_zillow_data(Config.ZILLOW_FILE)
    
    if not zillow_df.empty:
        print(f"✅ Successfully loaded {len(zillow_df)} records")
        print("\nColumns in loaded data:")
        print(list(zillow_df.columns))
        print("\nFirst few rows:")
        print(zillow_df.head())
        print(f"\nZHVI range: ${zillow_df['zhvi_latest'].min():,.0f} - ${zillow_df['zhvi_latest'].max():,.0f}")
    else:
        print("❌ Failed to load Zillow data")

if __name__ == "__main__":
    test_zillow_loading()
