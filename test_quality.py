"""
Test script for restaurant quality analysis
"""

import pandas as pd
import logging
from config import Config
from restaurant_quality import RestaurantQualityAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_quality_analysis():
    """Test the quality analysis functionality"""
    logger.info("🧪 Testing Restaurant Quality Analysis")
    logger.info("=" * 50)
    
    # Create directories
    Config.create_directories()
    
    # Initialize analyzer
    analyzer = RestaurantQualityAnalyzer()
    
    # Test with Palo Alto (good test location)
    test_city = "Palo Alto"
    test_lat, test_lng = 37.4419, -122.1430
    
    logger.info(f"Testing quality analysis for {test_city}")
    
    try:
        # Get restaurants with quality data
        restaurants = analyzer.get_restaurants_with_quality(
            test_lat, test_lng, radius=2000, max_pages=2
        )
        
        if not restaurants:
            logger.warning("No restaurants found - may be API quota issue")
            return
        
        logger.info(f"Found {len(restaurants)} restaurants with quality data")
        
        # Show sample quality data
        logger.info("\n📊 Sample Restaurant Quality Data:")
        logger.info("-" * 40)
        
        for i, restaurant in enumerate(restaurants[:5]):
            logger.info(f"\n{i+1}. {restaurant.name}")
            logger.info(f"   📍 Location: ({restaurant.lat:.4f}, {restaurant.lng:.4f})")
            logger.info(f"   ⭐ Rating: {restaurant.rating}/5" if restaurant.rating else "   ⭐ Rating: No rating")
            logger.info(f"   💰 Price Level: {'$' * restaurant.price_level if restaurant.price_level else 'Unknown'}")
            logger.info(f"   📝 Reviews: {restaurant.user_ratings_total}" if restaurant.user_ratings_total else "   📝 Reviews: No review count")
            logger.info(f"   🏆 Quality Score: {restaurant.quality_score}" if restaurant.quality_score else "   🏆 Quality Score: No score")
            logger.info(f"   🏷️ Types: {', '.join(restaurant.types[:3]) if restaurant.types else 'No types'}")
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame([
            {
                'place_id': r.place_id,
                'name': r.name,
                'lat': r.lat,
                'lng': r.lng,
                'rating': r.rating,
                'price_level': r.price_level,
                'user_ratings_total': r.user_ratings_total,
                'quality_score': r.quality_score,
                'types': '|'.join(r.types) if r.types else '',
                'vicinity': r.vicinity,
                'city': test_city
            }
            for r in restaurants
        ])
        
        # Calculate metrics
        metrics = analyzer.calculate_city_quality_metrics(df)
        
        logger.info(f"\n📈 {test_city} Quality Metrics:")
        logger.info("-" * 40)
        logger.info(f"Total restaurants: {metrics['total_restaurants']}")
        logger.info(f"Average rating: {metrics['avg_rating']:.2f}" if metrics['avg_rating'] else "Average rating: N/A")
        logger.info(f"Average quality score: {metrics['avg_quality_score']:.2f}" if metrics['avg_quality_score'] else "Average quality score: N/A")
        logger.info(f"High-rated (4.0+): {metrics['high_rated_count']}")
        logger.info(f"Low-rated (<3.0): {metrics['low_rated_count']}")
        logger.info(f"Expensive ($$$+): {metrics['expensive_count']}")
        logger.info(f"Budget ($ or $$): {metrics['budget_count']}")
        logger.info(f"Well-reviewed (50+ reviews): {metrics['well_reviewed_count']}")
        
        if metrics['quality_categories']:
            logger.info("\nQuality Distribution:")
            for category, count in metrics['quality_categories'].items():
                logger.info(f"  {category}: {count}")
        
        # Save test data
        test_file = analyzer.save_quality_data(df, f"{test_city}_test")
        logger.info(f"\n✅ Test completed successfully!")
        logger.info(f"📁 Test data saved: {test_file}")
        
        return df, metrics
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return None, None

def test_quality_scoring():
    """Test the quality scoring algorithm"""
    logger.info("\n🔬 Testing Quality Scoring Algorithm")
    logger.info("-" * 40)
    
    from restaurant_quality import RestaurantQuality
    
    analyzer = RestaurantQualityAnalyzer()
    
    # Test cases for quality scoring
    test_restaurants = [
        # High rating, many reviews
        RestaurantQuality("test1", "Excellent Restaurant", 37.4419, -122.1430, 
                         rating=4.8, price_level=3, user_ratings_total=500),
        
        # High rating, few reviews  
        RestaurantQuality("test2", "New Good Place", 37.4419, -122.1430,
                         rating=4.7, price_level=2, user_ratings_total=15),
        
        # Average rating, many reviews
        RestaurantQuality("test3", "Okay Restaurant", 37.4419, -122.1430,
                         rating=3.5, price_level=1, user_ratings_total=200),
        
        # No rating
        RestaurantQuality("test4", "Unknown Quality", 37.4419, -122.1430,
                         rating=None, price_level=2, user_ratings_total=10),
    ]
    
    for restaurant in test_restaurants:
        score = analyzer._calculate_quality_score(restaurant)
        logger.info(f"{restaurant.name}:")
        logger.info(f"  Rating: {restaurant.rating}, Reviews: {restaurant.user_ratings_total}, Price: {'$' * restaurant.price_level if restaurant.price_level else 'N/A'}")
        logger.info(f"  Quality Score: {score}")
        logger.info("")

if __name__ == "__main__":
    # Run tests
    test_quality_scoring()
    test_quality_analysis()
