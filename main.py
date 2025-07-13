"""
Main execution script for Forks & Fortunes analysis

This script orchestrates the complete analysis pipeline (because someone has to be the conductor):
1. Data collection (Census, Zillow, Restaurant data) - the boring but necessary part
2. Data merging and processing - where the magic happens (and things break)
3. Analysis and visualization - pretty charts to impress your friends
4. Report generation - words to go with the pretty charts
"""

import os
import sys
import argparse
import pandas as pd
import logging
from datetime import datetime

from config import Config
from data_collector import DataCollector
from restaurant_analyzer import RestaurantAnalyzer
from analysis_utils import AnalysisUtils

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('forks_fortunes.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def main(mode='full', wealth_tier=None):
    """Main execution function - where the magic (and chaos) happens"""
    logger.info("Starting Forks & Fortunes Analysis")
    logger.info("=" * 60)
    
    # Create directories (because we're organized like that)
    Config.create_directories()
    
    # Initialize components (assembling the dream team)
    data_collector = DataCollector()
    restaurant_analyzer = RestaurantAnalyzer()
    analysis_utils = AnalysisUtils()
    
    # Determine cities to analyze based on mode (choose your own adventure)
    if mode == 'test':
        cities_to_analyze = Config.TEST_CITIES
        logger.info(f"Running in TEST mode with {len(cities_to_analyze)} cities (because patience is overrated)")
    elif mode == 'tier' and wealth_tier:
        cities_to_analyze = Config.WEALTH_TIERS.get(wealth_tier, Config.CITIES_TO_ANALYZE)
        logger.info(f"Analyzing {wealth_tier} tier: {len(cities_to_analyze)} cities (fancy!)")
    else:
        cities_to_analyze = Config.CITIES_TO_ANALYZE
        logger.info(f"Running FULL analysis with {len(cities_to_analyze)} cities (buckle up buttercup)")
    
    logger.info(f"Cities to analyze: {', '.join(cities_to_analyze)}")
    
    try:
        # Step 1: Census Data Collection
        logger.info("\nSTEP 1: Census Data Collection")
        logger.info("-" * 40)
        
        # Try to load existing census data first
        census_df = data_collector.load_existing_census_data()
        if census_df is None:
            logger.info("No existing census data found. Collecting from API...")
            census_df = data_collector.collect_census_data()
            data_collector.save_census_data(census_df)
        else:
            logger.info(f"Using existing census data with {len(census_df)} ZIP codes")
        
        # Step 2: Zillow Data Loading
        logger.info("\nSTEP 2: Zillow Data Loading")
        logger.info("-" * 40)
        
        zillow_df = data_collector.load_zillow_data(Config.ZILLOW_FILE)
        if zillow_df.empty:
            logger.error("Could not load Zillow data. Please check the file path.")
            return
        
        # Step 3: Restaurant Data Analysis with Quality Metrics
        logger.info("\n🍽️⭐ STEP 3: Restaurant Data Analysis with Quality Metrics")
        logger.info("-" * 40)
        
        # Check if we should use existing quality restaurant data or analyze selected cities
        existing_quality_file = f"{Config.RESULTS_DIR}/restaurant_quality_results.csv"
        
        # Load existing data and check if we need to analyze additional cities
        existing_restaurant_df = None
        cities_already_analyzed = []
        
        if os.path.exists(existing_quality_file):
            logger.info("Found existing restaurant quality data. Loading...")
            existing_restaurant_df = pd.read_csv(existing_quality_file)
            cities_already_analyzed = existing_restaurant_df['City'].unique().tolist()
            logger.info(f"Already have data for {len(cities_already_analyzed)} cities: {cities_already_analyzed}")
        
        # Determine which cities still need analysis
        cities_to_analyze_new = [city for city in cities_to_analyze if city not in cities_already_analyzed]
        
        if cities_to_analyze_new:
            logger.info(f"Need to analyze {len(cities_to_analyze_new)} new cities: {cities_to_analyze_new}")
            logger.warning("⚠️ This will take a while due to API rate limits...")
            
            # Analyze the new cities
            new_restaurant_df = restaurant_analyzer.analyze_cities_with_quality(cities_to_analyze_new)
            
            # Combine with existing data if available
            if existing_restaurant_df is not None:
                restaurant_df = pd.concat([existing_restaurant_df, new_restaurant_df], ignore_index=True)
                logger.info(f"Combined existing data with new analysis: {len(restaurant_df)} total cities")
            else:
                restaurant_df = new_restaurant_df
            
            # Save the updated dataset
            restaurant_analyzer.save_restaurant_results(restaurant_df, "restaurant_quality_results.csv")
            
        elif existing_restaurant_df is not None:
            # Filter existing data to only include cities we want to analyze
            restaurant_df = existing_restaurant_df[existing_restaurant_df['City'].isin(cities_to_analyze)].copy()
            logger.info(f"Using existing data for {len(restaurant_df)} cities (filtered to selected cities)")
            
        else:
            logger.error("No existing data and no cities to analyze!")
            return
        
        # Step 4: Data Merging and Analysis
        logger.info("\n🔗 STEP 4: Data Merging and Analysis")
        logger.info("-" * 40)
        
        # Merge all datasets
        merged_df = analysis_utils.merge_datasets(zillow_df, census_df, restaurant_df)
        
        # Save merged dataset
        merged_file = f"{Config.RESULTS_DIR}/merged_analysis.csv"
        merged_df.to_csv(merged_file, index=False)
        logger.info(f"Saved merged dataset: {merged_file}")
        
        # Step 5: Visualizations
        logger.info("\nSTEP 5: Creating Visualizations")
        logger.info("-" * 40)
        
        # Filter for cities with complete data
        complete_data = merged_df.dropna(subset=['restaurant_count', 'zhvi_latest'])
        
        if len(complete_data) > 0:
            # Property value ranking
            if not complete_data.empty:
                analysis_utils.create_ranking_plot(
                    complete_data, 'zhvi_latest', 'City',
                    'Bay Area Cities by Property Value (ZHVI)',
                    'Median Home Value ($)',
                    top_n=min(15, len(complete_data)),
                    save_path=f"{Config.RESULTS_DIR}/property_value_ranking.png"
                )
            
            # Restaurant count ranking
            if not complete_data.empty:
                analysis_utils.create_ranking_plot(
                    complete_data, 'restaurant_count', 'City',
                    'Bay Area Cities by Restaurant Count',
                    'Number of Restaurants',
                    top_n=min(15, len(complete_data)),
                    save_path=f"{Config.RESULTS_DIR}/restaurant_count_ranking.png"
                )
            
            # Scatter plot: Property value vs Restaurant count
            if len(complete_data) > 1:
                analysis_utils.create_scatter_plot(
                    complete_data, 'zhvi_latest', 'restaurant_count',
                    'Property Value vs Restaurant Count',
                    'Median Home Value ($)', 'Number of Restaurants',
                    color_col='population',
                    save_path=f"{Config.RESULTS_DIR}/value_vs_restaurants_scatter.png"
                )
            
            # Under-served areas analysis
            if 'restaurants_per_billion_val' in complete_data.columns:
                underserved = analysis_utils.create_summary_table(
                    complete_data, 'restaurants_per_billion_val',
                    ['City', 'zhvi_latest', 'restaurant_count', 'restaurants_per_billion_val'],
                    'Under-served Wealthy Areas (Fewest Restaurants per $B Property Value)',
                    ascending=True, top_n=10
                )
        
        logger.info("\nSTEP 6: Generating Insights Report")
        logger.info("-" * 40)
        
        report = analysis_utils.generate_insights_report(
            merged_df, 
            save_path=f"{Config.RESULTS_DIR}/insights_report.md"
        )
        
        logger.info("\nANALYSIS COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"Results saved in: {Config.RESULTS_DIR}/")
        logger.info(f"Maps saved in: {Config.MAPS_DIR}/")
        logger.info(f"Visualizations: {Config.RESULTS_DIR}/*.png")
        logger.info(f"Full report: {Config.RESULTS_DIR}/insights_report.md")
        
        if not merged_df.empty:
            logger.info(f"\nQuick Preview ({len(merged_df)} cities analyzed):")
            preview_cols = ['City', 'zhvi_latest', 'restaurant_count']
            available_cols = [col for col in preview_cols if col in merged_df.columns]
            if available_cols:
                print(merged_df[available_cols].head(10).to_string(index=False))
        
    except KeyboardInterrupt:
        logger.info("\nAnalysis interrupted by user")
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        logger.exception("Full error traceback:")
    finally:
        logger.info(f"\nAnalysis completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def run_quick_test():
    """Run a quick test with minimal data"""
    logger.info("Running quick test mode...")
    
    Config.create_directories()
    data_collector = DataCollector()
    restaurant_analyzer = RestaurantAnalyzer()
    
    # Test single city
    test_city = "Atherton"
    logger.info(f"Testing restaurant analysis for {test_city}")
    
    restaurants, center = restaurant_analyzer.get_restaurants_within_radius(test_city)
    logger.info(f"Found {len(restaurants)} restaurants")
    
    if restaurants and center[0] is not None:
        map_obj = restaurant_analyzer.create_restaurant_map(test_city, restaurants, center)
        if map_obj:
            test_file = f"{Config.MAPS_DIR}/test_map.html"
            map_obj.save(test_file)
            logger.info(f"Test map saved: {test_file}")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Forks & Fortunes: Analyze restaurant density vs wealth in Bay Area cities',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Full analysis of all cities
  python main.py --mode test               # Quick test with 3 cities
  python main.py --mode tier --tier ultra_wealthy    # Analyze only ultra-wealthy cities
  python main.py --mode tier --tier high_wealth      # Analyze only high-wealth cities
  python main.py --quick-test              # Single city map test
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['full', 'test', 'tier'], 
        default='full',
        help='Analysis mode: full (all cities), test (3 cities), or tier (specific wealth tier)'
    )
    
    parser.add_argument(
        '--tier',
        choices=['ultra_wealthy', 'high_wealth', 'upper_middle', 'mid_tier', 'urban'],
        help='Wealth tier to analyze (only used with --mode tier)'
    )
    
    parser.add_argument(
        '--quick-test',
        action='store_true',
        help='Run quick single-city test (generates test map)'
    )
    
    parser.add_argument(
        '--list-cities',
        action='store_true',
        help='List all available cities and tiers'
    )
    
    return parser.parse_args()


def list_cities():
    """List all available cities organized by wealth tier"""
    print("\nAvailable Cities by Wealth Tier:")
    print("=" * 50)
    
    for tier_name, cities in Config.WEALTH_TIERS.items():
        print(f"\n{tier_name.replace('_', ' ').title()} ({len(cities)} cities):")
        for city in cities:
            print(f"  - {city}")
    
    print(f"\nTotal cities available: {len(Config.CITIES_TO_ANALYZE)}")
    print(f"Test cities: {', '.join(Config.TEST_CITIES)}")


if __name__ == "__main__":
    args = parse_arguments()
    
    if args.quick_test:
        run_quick_test()
    elif args.list_cities:
        list_cities()
    elif args.mode == 'tier' and not args.tier:
        print("Error: --tier argument required when using --mode tier")
        print("Available tiers: ultra_wealthy, high_wealth, upper_middle, mid_tier, urban")
        sys.exit(1)
    else:
        main(mode=args.mode, wealth_tier=args.tier)
