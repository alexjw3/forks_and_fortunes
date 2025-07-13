import pandas as pd

# Load and inspect the Zillow file
try:
    zillow_df = pd.read_csv("Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv")
    print("Zillow CSV columns:")
    print(list(zillow_df.columns))
    print(f"\nShape: {zillow_df.shape}")
    print("\nFirst few columns:")
    print(zillow_df.columns[:10])
    print("\nLast few columns:")
    print(zillow_df.columns[-10:])
    
    # Look for date-like columns
    date_cols = [col for col in zillow_df.columns if '-' in col]
    print(f"\nColumns with dashes (potential dates): {date_cols[:5]}...")
    
    # Look for numeric columns
    numeric_cols = [col for col in zillow_df.columns if str(col).replace('-', '').replace('_', '').isdigit()]
    print(f"\nNumeric-looking columns: {numeric_cols[:5]}...")
    
    print("\nFirst row sample:")
    print(zillow_df.head(1))
    
except Exception as e:
    print(f"Error: {e}")
