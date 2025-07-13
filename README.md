# 🍴💰 Forks & Fortunes

A comprehensive analysis of restaurant density vs. wealth in Bay Area cities, now enhanced with restaurant quality metrics using Google Places API.

## Overview

This project analyzes the relationship between affluence and restaurant availability/quality across Bay Area communities, combining:

- **Restaurant Data**: Count, quality ratings, price levels, and review data from Google Places API
- **Wealth Data**: Property values from Zillow ZHVI (Zillow Home Value Index)
- **Demographics**: Population and income data from US Census Bureau

## Features

### 🎯 Core Analysis
- **Restaurant Density**: Restaurants per capita and per billion dollars of property value
- **Quality Metrics**: Average ratings, high-rated restaurant percentages, price distributions
- **Wealth Correlation**: Relationship between property values and restaurant quality/quantity
- **Interactive Maps**: Color-coded by restaurant quality with detailed popups

### 🗺️ Visualizations
- **Quality Maps**: Interactive maps with color-coded restaurant markers based on ratings
- **Ranking Charts**: Cities ranked by property value and restaurant metrics
- **Scatter Plots**: Property value vs restaurant count with population weighting
- **Quality Analysis**: Distribution of excellent vs average restaurants by area

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd forks-and-fortunes
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API keys** in `config.py`:
   - **Census API Key**: Get from [census.gov/developers](https://www.census.gov/developers/)
   - **Google Places API Key**: Get from [Google Cloud Console](https://console.cloud.google.com/)

4. **Add Zillow Data**: Download ZHVI data and place in the project directory

## Usage

### Command Line Options

```bash
# Full analysis of all Bay Area cities (16 cities)
python main.py

# Quick test with 3 cities (Atherton, Menlo Park, Palo Alto)
python main.py --mode test

# Analyze specific wealth tiers
python main.py --mode tier --tier ultra_wealthy
python main.py --mode tier --tier high_wealth
python main.py --mode tier --tier upper_middle

# Quick single-city test (generates test map)
python main.py --quick-test

# List all available cities and tiers
python main.py --list-cities

# Get help
python main.py --help
```

### Wealth Tiers

Cities are organized into wealth tiers for focused analysis:

- **Ultra Wealthy**: Atherton, Portola Valley, Hillsborough, Los Altos
- **High Wealth**: Palo Alto, Menlo Park, Mountain View  
- **Upper Middle**: Redwood City, San Carlos, Belmont, Foster City, San Mateo
- **Mid Tier**: Burlingame, Millbrae, San Bruno, South San Francisco
- **Urban**: San Francisco, Daly City

## Data Sources

1. **Restaurant Data**: Google Places API
   - Restaurant locations, ratings, price levels
   - Review counts and quality scores
   - Comprehensive grid-based city coverage

2. **Property Values**: Zillow ZHVI
   - Monthly home value estimates by ZIP code
   - California focus with Bay Area filtering

3. **Demographics**: US Census Bureau ACS 5-Year
   - Population, median income, housing units
   - ZIP code level granularity

## Output Files

### 📁 Results Directory
- `merged_analysis.csv`: Complete dataset with all metrics
- `restaurant_quality_results.csv`: Detailed restaurant quality data
- `insights_report.md`: Comprehensive analysis insights
- `*.png`: Ranking charts and scatter plots

### 🗺️ Maps Directory
- `{city}_quality_map.html`: Interactive quality maps for each city
- Color-coded restaurant markers by rating
- Detailed popups with quality metrics

### 📊 Key Metrics

For each city, the analysis provides:

- **Restaurant Count & Density**: Total restaurants, per capita, per billion $ property value
- **Quality Metrics**: Average rating, quality score, high-rated percentage (4.0+)
- **Price Analysis**: Expensive restaurant percentage, price distribution
- **Wealth Indicators**: Median home value, income, population

## Quality Scoring

The system uses a composite quality score that combines:
- **Base Rating** (1-5 stars from Google)
- **Review Credibility** (more reviews = more reliable)
- **Price Adjustments** (value consideration)

## Progressive Analysis

The system is designed for incremental analysis:
- **Resume Capability**: Skips cities already analyzed
- **API Efficiency**: Respects rate limits with intelligent batching
- **Flexible Modes**: Test small sets before full analysis

## Example Insights

- **Quality Paradox**: Some wealthy areas have fewer restaurants but higher average quality
- **Underserved Enclaves**: High-value areas with surprisingly low restaurant density
- **Urban vs Suburban**: Different patterns of restaurant quantity vs quality
- **Price Premiums**: Concentration of expensive restaurants in certain areas

## Technical Details

- **Grid-based Search**: Comprehensive coverage using overlapping search grids
- **Rate Limit Handling**: Built-in delays and retry logic for API calls
- **Data Persistence**: Saves intermediate results to avoid re-analysis
- **Quality Validation**: Multiple data validation and cleaning steps

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is for educational and research purposes.
