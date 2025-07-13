"""
Restaurant data collection and analysis for Forks & Fortunes
"""

import math
import requests
import time
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
from tqdm import tqdm
import logging
from typing import List, Tuple, Optional

from config import Config
from data_collector import DataCollector
from restaurant_quality import RestaurantQualityAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RestaurantAnalyzer:
    """Handles restaurant data collection and analysis"""
    
    def __init__(self):
        self.config = Config
        self.data_collector = DataCollector()
        self.quality_analyzer = RestaurantQualityAnalyzer()
        
    @staticmethod
    def haversine_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in km"""
        R = 6371  # Earth's radius in km
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lng2 - lng1)
        a = (math.sin(delta_phi / 2.0) ** 2 + 
             math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
        return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))
    
    def get_restaurants_near_point(self, lat: float, lng: float, 
                                 radius: int = 1000, max_pages: int = None) -> List[Tuple[float, float, str]]:
        """Get restaurants near a specific point using Google Places API"""
        if max_pages is None:
            max_pages = self.config.MAX_API_PAGES
            
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            'location': f"{lat},{lng}",
            'radius': radius,
            'type': 'restaurant',
            'key': self.config.GOOGLE_API_KEY
        }
        
        restaurant_points = []
        
        try:
            response = requests.get(url, params=params, timeout=10).json()
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return []
        
        # print(response.get("status"))
        # print(response.get("results", []))
        
        if response.get("status") != "OK":
            if response.get("status") == "OVER_QUERY_LIMIT":
                logger.warning("⚠️ Google API quota exceeded")
            elif response.get("status") == "REQUEST_DENIED":
                logger.error("❌ Google API request denied - check your API key")
            # else:
            #     logger.warning(f"API status: {response.get('status')}")
            return []
        
        # Process first page
        restaurant_points.extend([
            (r['geometry']['location']['lat'], 
             r['geometry']['location']['lng'], 
             r.get('name', 'Unnamed'))
            for r in response.get('results', [])
        ])
        
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
            
            restaurant_points.extend([
                (r['geometry']['location']['lat'], 
                 r['geometry']['location']['lng'], 
                 r.get('name', 'Unnamed'))
                for r in next_response.get('results', [])
            ])
            
            next_page_token = next_response.get('next_page_token')
            page_count += 1
        
        return restaurant_points
    
    def get_restaurants_within_radius(self, city_name: str) -> Tuple[List[Tuple[float, float, str]], Tuple[Optional[float], Optional[float]]]:
        """Get all restaurants within radius of city center using grid sweep"""
        lat_c, lng_c = self.data_collector.get_city_center(city_name)
        
        if lat_c is None or lng_c is None:
            logger.error(f"❌ Could not get coordinates for {city_name}")
            return [], (None, None)
        
        # Calculate grid parameters
        delta_deg = self.config.SEARCH_STEP_KM / 111  # Rough conversion km to degrees
        steps = int(self.config.RESTAURANT_SEARCH_RADIUS_KM / self.config.SEARCH_STEP_KM)
        
        all_restaurants = []
        search_points = 0
        
        logger.info(f"Searching {city_name} with {steps * 2 + 1}x{steps * 2 + 1} grid...")
        
        # Grid sweep
        for dx in range(-steps, steps + 1):
            for dy in range(-steps, steps + 1):
                lat = lat_c + dy * delta_deg
                lng = lng_c + dx * delta_deg
                
                # Check if point is within radius
                dist = self.haversine_distance_km(lat_c, lng_c, lat, lng)
                if dist <= self.config.RESTAURANT_SEARCH_RADIUS_KM:
                    points = self.get_restaurants_near_point(lat, lng, radius=1000)
                    all_restaurants.extend(points)
                    search_points += 1
                    
                    # Rate limiting
                    # time.sleep(self.config.GOOGLE_API_DELAY)
        
        # Deduplicate based on coordinates (with small tolerance for GPS variance)
        unique_restaurants = []
        seen_coords = set()
        
        for lat, lng, name in all_restaurants:
            # Round to 5 decimal places for deduplication
            coord_key = (round(lat, 5), round(lng, 5))
            if coord_key not in seen_coords:
                seen_coords.add(coord_key)
                unique_restaurants.append((lat, lng, name))
        
        logger.info(f"🔍 {city_name}: Searched {search_points} points, found {len(unique_restaurants)} unique restaurants")
        return unique_restaurants, (lat_c, lng_c)
    
    def create_restaurant_map(self, city_name: str, restaurants: List[Tuple[float, float, str]], 
                            center: Tuple[Optional[float], Optional[float]]) -> Optional[folium.Map]:
        """Create an interactive map showing restaurants"""
        if center[0] is None or center[1] is None:
            logger.error(f"Cannot create map for {city_name} - no center coordinates")
            return None
            
        # Create map
        m = folium.Map(location=center, zoom_start=13, tiles='CartoDB positron')
        
        # Add restaurants as clustered markers
        marker_cluster = MarkerCluster().add_to(m)
        for lat, lng, name in restaurants:
            folium.Marker(
                location=[lat, lng],
                popup=folium.Popup(name, max_width=200),
                tooltip=name,
                icon=folium.Icon(color='red', icon='cutlery', prefix='fa')
            ).add_to(marker_cluster)
        
        # Add search radius circle
        folium.Circle(
            location=center,
            radius=self.config.RESTAURANT_SEARCH_RADIUS_KM * 1000,  # Convert to meters
            color="blue",
            fill=True,
            fill_opacity=0.1,
            popup=f"{self.config.RESTAURANT_SEARCH_RADIUS_KM}km search radius",
            tooltip=f"Search area: {self.config.RESTAURANT_SEARCH_RADIUS_KM}km radius"
        ).add_to(m)
        
        # Add city center marker
        folium.Marker(
            location=center,
            popup=f"{city_name} Center",
            tooltip=f"{city_name} Center",
            icon=folium.Icon(color='blue', icon='star')
        ).add_to(m)
        
        return m
    
    def analyze_multiple_cities(self, cities: List[str] = None) -> pd.DataFrame:
        """Analyze restaurant counts for multiple cities"""
        if cities is None:
            cities = self.config.CITIES_TO_ANALYZE
        
        results = []
        
        for city in tqdm(cities, desc="Analyzing cities"):
            logger.info(f"\n🔍 Analyzing {city}...")
            try:
                restaurants, center = self.get_restaurants_within_radius(city)
                
                # Create and save map
                map_obj = self.create_restaurant_map(city, restaurants, center)
                map_filename = None
                if map_obj:
                    map_filename = f"{self.config.MAPS_DIR}/{city.replace(' ', '_').lower()}_restaurants_map.html"
                    map_obj.save(map_filename)
                    logger.info(f"💾 Saved map: {map_filename}")
                
                results.append({
                    'City': city,
                    'restaurant_count': len(restaurants),
                    'center_lat': center[0],
                    'center_lng': center[1],
                    'map_file': map_filename,
                    'status': 'success'
                })
                
            except Exception as e:
                logger.error(f"⚠️ Error analyzing {city}: {e}")
                results.append({
                    'City': city,
                    'restaurant_count': None,
                    'center_lat': None,
                    'center_lng': None,
                    'map_file': None,
                    'status': f'error: {str(e)}'
                })
        
        return pd.DataFrame(results)
    
    def analyze_cities_with_quality(self, cities: List[str] = None) -> pd.DataFrame:
        """Analyze restaurant counts AND quality metrics for multiple cities"""
        if cities is None:
            cities = self.config.CITIES_TO_ANALYZE
        
        results = []
        
        for city in tqdm(cities, desc="Analyzing cities with quality"):
            logger.info(f"\n🍴⭐ Analyzing {city} with quality metrics...")
            try:
                # Get city center coordinates
                lat_c, lng_c = self.data_collector.get_city_center(city)
                
                if lat_c is None or lng_c is None:
                    logger.error(f"❌ Could not get coordinates for {city}")
                    results.append({
                        'City': city,
                        'restaurant_count': None,
                        'avg_rating': None,
                        'avg_quality_score': None,
                        'high_rated_count': None,
                        'expensive_count': None,
                        'well_reviewed_count': None,
                        'center_lat': None,
                        'center_lng': None,
                        'status': 'error: no coordinates'
                    })
                    continue
                
                # Analyze restaurant quality for this city
                quality_df = self.quality_analyzer.analyze_city_restaurant_quality(
                    city, lat_c, lng_c, 
                    search_radius_km=self.config.RESTAURANT_SEARCH_RADIUS_KM,
                    search_step_km=self.config.SEARCH_STEP_KM
                )
                
                if quality_df.empty:
                    logger.warning(f"⚠️ No restaurant data found for {city}")
                    results.append({
                        'City': city,
                        'restaurant_count': 0,
                        'avg_rating': None,
                        'avg_quality_score': None,
                        'high_rated_count': 0,
                        'expensive_count': 0,
                        'well_reviewed_count': 0,
                        'center_lat': lat_c,
                        'center_lng': lng_c,
                        'status': 'success - no restaurants'
                    })
                    continue
                
                # Calculate quality metrics
                quality_metrics = self.quality_analyzer.calculate_city_quality_metrics(quality_df)
                
                # Save detailed quality data
                quality_file = self.quality_analyzer.save_quality_data(quality_df, city)
                
                # Create enhanced map with quality information
                quality_map = self.create_quality_map(city, quality_df, (lat_c, lng_c))
                quality_map_filename = None
                if quality_map:
                    quality_map_filename = f"{self.config.MAPS_DIR}/{city.replace(' ', '_').lower()}_quality_map.html"
                    quality_map.save(quality_map_filename)
                    logger.info(f"💾 Saved quality map: {quality_map_filename}")
                
                results.append({
                    'City': city,
                    'restaurant_count': quality_metrics['total_restaurants'],
                    'avg_rating': quality_metrics['avg_rating'],
                    'avg_quality_score': quality_metrics['avg_quality_score'],
                    'high_rated_count': quality_metrics['high_rated_count'],
                    'low_rated_count': quality_metrics['low_rated_count'],
                    'expensive_count': quality_metrics['expensive_count'],
                    'budget_count': quality_metrics['budget_count'],
                    'well_reviewed_count': quality_metrics['well_reviewed_count'],
                    'center_lat': lat_c,
                    'center_lng': lng_c,
                    'quality_map_file': quality_map_filename,
                    'quality_data_file': quality_file,
                    'status': 'success'
                })
                
                # Log quality summary
                logger.info(f"📊 {city} Quality Summary:")
                logger.info(f"   Total restaurants: {quality_metrics['total_restaurants']}")
                logger.info(f"   Average rating: {quality_metrics['avg_rating']:.2f}" if quality_metrics['avg_rating'] else "   Average rating: N/A")
                logger.info(f"   High-rated (4.0+): {quality_metrics['high_rated_count']}")
                logger.info(f"   Expensive ($$$+): {quality_metrics['expensive_count']}")
                
            except Exception as e:
                logger.error(f"⚠️ Error analyzing {city}: {e}")
                results.append({
                    'City': city,
                    'restaurant_count': None,
                    'avg_rating': None,
                    'avg_quality_score': None,
                    'high_rated_count': None,
                    'expensive_count': None,
                    'well_reviewed_count': None,
                    'center_lat': None,
                    'center_lng': None,
                    'status': f'error: {str(e)}'
                })
        
        return pd.DataFrame(results)
    
    def create_quality_map(self, city_name: str, quality_df: pd.DataFrame, 
                          center: Tuple[float, float]) -> Optional[folium.Map]:
        """Create an enhanced map showing restaurants with quality indicators"""
        if quality_df.empty:
            return None
            
        # Create map
        m = folium.Map(location=center, zoom_start=13, tiles='CartoDB positron')
        
        # Add restaurants with quality-based markers
        for _, restaurant in quality_df.iterrows():
            # Determine marker color based on rating
            if pd.isna(restaurant['rating']):
                color = 'gray'
                rating_text = 'No rating'
            elif restaurant['rating'] >= 4.5:
                color = 'green'
                rating_text = f"⭐ {restaurant['rating']}/5"
            elif restaurant['rating'] >= 4.0:
                color = 'lightgreen'
                rating_text = f"⭐ {restaurant['rating']}/5"
            elif restaurant['rating'] >= 3.5:
                color = 'orange'
                rating_text = f"⭐ {restaurant['rating']}/5"
            else:
                color = 'red'
                rating_text = f"⭐ {restaurant['rating']}/5"
            
            # Price level indicator
            price_text = 'Price: '
            if pd.isna(restaurant['price_level']):
                price_text += 'Unknown'
            else:
                price_text += '$' * int(restaurant['price_level'])
            
            # Create popup content
            popup_content = f"""
            <b>{restaurant['name']}</b><br>
            {rating_text}<br>
            {price_text}<br>
            Reviews: {restaurant['user_ratings_total'] if pd.notna(restaurant['user_ratings_total']) else 'N/A'}<br>
            Quality Score: {restaurant['quality_score'] if pd.notna(restaurant['quality_score']) else 'N/A'}
            """
            
            folium.Marker(
                location=[restaurant['lat'], restaurant['lng']],
                popup=folium.Popup(popup_content, max_width=250),
                tooltip=f"{restaurant['name']} - {rating_text}",
                icon=folium.Icon(color=color, icon='cutlery', prefix='fa')
            ).add_to(m)
        
        # Add search radius circle
        folium.Circle(
            location=center,
            radius=self.config.RESTAURANT_SEARCH_RADIUS_KM * 1000,
            color="blue",
            fill=True,
            fill_opacity=0.1,
            popup=f"{self.config.RESTAURANT_SEARCH_RADIUS_KM}km search radius",
        ).add_to(m)
        
        # Add city center marker
        folium.Marker(
            location=center,
            popup=f"{city_name} Center",
            tooltip=f"{city_name} Center",
            icon=folium.Icon(color='blue', icon='star')
        ).add_to(m)
        
        # Add legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 150px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Restaurant Quality</b></p>
        <p><i class="fa fa-cutlery" style="color:green"></i> Excellent (4.5+)</p>
        <p><i class="fa fa-cutlery" style="color:lightgreen"></i> Very Good (4.0+)</p>
        <p><i class="fa fa-cutlery" style="color:orange"></i> Good (3.5+)</p>
        <p><i class="fa fa-cutlery" style="color:red"></i> Below 3.5</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        return m
    
    def save_restaurant_results(self, df: pd.DataFrame, filename: str = "restaurant_results.csv") -> str:
        """Save restaurant analysis results"""
        filepath = f"{self.config.RESULTS_DIR}/{filename}"
        df.to_csv(filepath, index=False)
        logger.info(f"💾 Saved restaurant results to {filepath}")
        return filepath


if __name__ == "__main__":
    # Test the restaurant analyzer
    Config.create_directories()
    analyzer = RestaurantAnalyzer()
    
    # Test with a single city
    test_city = "Atherton"
    logger.info(f"Testing restaurant analysis for {test_city}")
    
    restaurants, center = analyzer.get_restaurants_within_radius(test_city)
    logger.info(f"Found {len(restaurants)} restaurants in {test_city}")
    
    if restaurants:
        # Create test map
        map_obj = analyzer.create_restaurant_map(test_city, restaurants, center)
        if map_obj:
            test_map_file = f"{Config.MAPS_DIR}/test_{test_city.lower()}_map.html"
            map_obj.save(test_map_file)
            logger.info(f"Saved test map: {test_map_file}")
