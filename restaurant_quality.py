"""
Restaurant Quality Analysis for Forks & Fortunes

This module handles restaurant quality metrics including ratings, prices, 
and review counts from Google Places API data.
"""

import requests
import time
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RestaurantQuality:
    """Data class for restaurant quality information"""
    place_id: str
    name: str
    lat: float
    lng: float
    rating: Optional[float] = None
    price_level: Optional[int] = None
    user_ratings_total: Optional[int] = None
    types: Optional[List[str]] = None
    vicinity: Optional[str] = None
    quality_score: Optional[float] = None


class RestaurantQualityAnalyzer:
    """Analyzes restaurant quality using Google Places API"""
    
    def __init__(self):
        self.config = Config
        
    def get_restaurants_with_quality(self, lat: float, lng: float, 
                                   radius: int = 1000, max_pages: int = None) -> List[RestaurantQuality]:
        """Get restaurants with quality data near a specific point"""
        if max_pages is None:
            max_pages = self.config.MAX_API_PAGES
            
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            'location': f"{lat},{lng}",
            'radius': radius,
            'type': 'restaurant',
            'key': self.config.GOOGLE_API_KEY
        }
        
        restaurants = []
        
        try:
            response = requests.get(url, params=params, timeout=10).json()
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return []
        
        if response.get("status") != "OK":
            if response.get("status") == "OVER_QUERY_LIMIT":
                logger.warning("⚠️ Google API quota exceeded")
            elif response.get("status") == "REQUEST_DENIED":
                logger.error("❌ Google API request denied - check your API key")
            return []
        
        # Process first page
        restaurants.extend(self._parse_restaurants_from_response(response))
        
        # Process additional pages
        next_page_token = response.get('next_page_token')
        page_count = 1
        
        while next_page_token and page_count < max_pages:
            time.sleep(2)  # Required delay for next page token
            next_params = {"pagetoken": next_page_token, "key": self.config.GOOGLE_API_KEY}
            
            try:
                next_response = requests.get(url, params=next_params, timeout=10).json()
            except requests.RequestException as e:
                logger.error(f"API request failed for page {page_count + 1}: {e}")
                break
            
            restaurants.extend(self._parse_restaurants_from_response(next_response))
            next_page_token = next_response.get('next_page_token')
            page_count += 1
        
        return restaurants
    
    def _parse_restaurants_from_response(self, response: Dict) -> List[RestaurantQuality]:
        """Parse restaurant data from API response"""
        restaurants = []
        
        for place in response.get('results', []):
            restaurant = RestaurantQuality(
                place_id=place.get('place_id', ''),
                name=place.get('name', 'Unnamed'),
                lat=place['geometry']['location']['lat'],
                lng=place['geometry']['location']['lng'],
                rating=place.get('rating'),
                price_level=place.get('price_level'),
                user_ratings_total=place.get('user_ratings_total'),
                types=place.get('types', []),
                vicinity=place.get('vicinity', '')
            )
            
            # Calculate quality score
            restaurant.quality_score = self._calculate_quality_score(restaurant)
            restaurants.append(restaurant)
        
        return restaurants
    
    def _calculate_quality_score(self, restaurant: RestaurantQuality) -> Optional[float]:
        """Calculate a composite quality score for a restaurant"""
        if restaurant.rating is None:
            return None
        
        # Base score from rating (0-5 scale)
        score = restaurant.rating
        
        # Adjust for number of reviews (credibility factor)
        if restaurant.user_ratings_total:
            # Normalize review count impact (0-1 scale)
            review_factor = min(restaurant.user_ratings_total / 100, 1.0)
            # Weight the rating by credibility (more reviews = more credible)
            score = score * (0.7 + 0.3 * review_factor)
        
        # Adjust for price level (value consideration)
        if restaurant.price_level is not None:
            # Higher price doesn't necessarily mean better, but can indicate quality
            # Slight bonus for mid-range restaurants (price level 2-3)
            if restaurant.price_level in [2, 3]:
                score *= 1.05
            elif restaurant.price_level == 4:  # Very expensive
                score *= 1.02  # Small bonus for high-end
        
        return round(score, 2)
    
    def analyze_city_restaurant_quality(self, city_name: str, lat_c: float, lng_c: float, 
                                      search_radius_km: float = 3, search_step_km: float = 0.5) -> pd.DataFrame:
        """Analyze restaurant quality for an entire city"""
        # Calculate grid parameters
        delta_deg = search_step_km / 111  # Rough conversion km to degrees
        steps = int(search_radius_km / search_step_km)
        
        all_restaurants = []
        search_points = 0
        
        logger.info(f"Analyzing restaurant quality in {city_name}...")
        logger.info(f"Grid size: {steps * 2 + 1}x{steps * 2 + 1} points")
        
        # Grid sweep
        for dx in range(-steps, steps + 1):
            for dy in range(-steps, steps + 1):
                lat = lat_c + dy * delta_deg
                lng = lng_c + dx * delta_deg
                
                # Check if point is within radius
                dist = self._haversine_distance_km(lat_c, lng_c, lat, lng)
                if dist <= search_radius_km:
                    restaurants = self.get_restaurants_with_quality(lat, lng, radius=1000)
                    all_restaurants.extend(restaurants)
                    search_points += 1
        
        logger.info(f"Searched {search_points} points, found {len(all_restaurants)} restaurants")
        
        # Convert to DataFrame and deduplicate
        if not all_restaurants:
            return pd.DataFrame()
        
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
                'city': city_name
            }
            for r in all_restaurants
        ])
        
        # Deduplicate by place_id
        df = df.drop_duplicates(subset='place_id').reset_index(drop=True)
        
        logger.info(f"After deduplication: {len(df)} unique restaurants in {city_name}")
        return df
    
    @staticmethod
    def _haversine_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in km"""
        import math
        R = 6371  # Earth's radius in km
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lng2 - lng1)
        a = (math.sin(delta_phi / 2.0) ** 2 + 
             math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
        return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))
    
    def calculate_city_quality_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate quality metrics for a city's restaurants"""
        if df.empty:
            return {
                'total_restaurants': 0,
                'avg_rating': None,
                'avg_quality_score': None,
                'high_rated_count': 0,
                'low_rated_count': 0,
                'expensive_count': 0,
                'budget_count': 0,
                'well_reviewed_count': 0,
                'quality_categories': {}
            }
        
        # Filter out restaurants without ratings
        rated_df = df.dropna(subset=['rating'])
        
        metrics = {
            'total_restaurants': len(df),
            'avg_rating': rated_df['rating'].mean() if not rated_df.empty else None,
            'avg_quality_score': rated_df['quality_score'].mean() if not rated_df.empty else None,
            'high_rated_count': len(rated_df[rated_df['rating'] >= 4.0]),
            'low_rated_count': len(rated_df[rated_df['rating'] < 3.0]),
            'expensive_count': len(df[df['price_level'].isin([3, 4])]),
            'budget_count': len(df[df['price_level'].isin([1, 2])]),
            'well_reviewed_count': len(df[df['user_ratings_total'] >= 50]),
        }
        
        # Quality categories
        if not rated_df.empty:
            quality_ranges = [
                ('Excellent (4.5+)', len(rated_df[rated_df['rating'] >= 4.5])),
                ('Very Good (4.0-4.4)', len(rated_df[(rated_df['rating'] >= 4.0) & (rated_df['rating'] < 4.5)])),
                ('Good (3.5-3.9)', len(rated_df[(rated_df['rating'] >= 3.5) & (rated_df['rating'] < 4.0)])),
                ('Average (3.0-3.4)', len(rated_df[(rated_df['rating'] >= 3.0) & (rated_df['rating'] < 3.5)])),
                ('Below Average (<3.0)', len(rated_df[rated_df['rating'] < 3.0]))
            ]
            metrics['quality_categories'] = dict(quality_ranges)
        
        return metrics
    
    def save_quality_data(self, df: pd.DataFrame, city_name: str) -> str:
        """Save restaurant quality data to CSV"""
        filename = f"restaurant_quality_{city_name.replace(' ', '_').lower()}.csv"
        filepath = f"{self.config.RESULTS_DIR}/{filename}"
        df.to_csv(filepath, index=False)
        logger.info(f"💾 Saved quality data: {filepath}")
        return filepath


if __name__ == "__main__":
    # Test the quality analyzer
    Config.create_directories()
    analyzer = RestaurantQualityAnalyzer()
    
    # Test with a specific location (Palo Alto)
    test_city = "Palo Alto"
    test_lat, test_lng = 37.4419, -122.1430  # Palo Alto coordinates
    
    logger.info(f"Testing quality analysis for {test_city}")
    
    # Get sample data
    restaurants = analyzer.get_restaurants_with_quality(test_lat, test_lng, radius=2000)
    logger.info(f"Found {len(restaurants)} restaurants with quality data")
    
    if restaurants:
        # Show sample quality data
        for i, restaurant in enumerate(restaurants[:3]):
            logger.info(f"Sample {i+1}: {restaurant.name}")
            logger.info(f"  Rating: {restaurant.rating}/5")
            logger.info(f"  Price Level: {'$' * restaurant.price_level if restaurant.price_level else 'N/A'}")
            logger.info(f"  Reviews: {restaurant.user_ratings_total}")
            logger.info(f"  Quality Score: {restaurant.quality_score}")
            logger.info("")
