"""
Analysis and visualization utilities for Forks & Fortunes
Because who doesn't love turning data into pretty charts and pretending it's "insights"
Boutta smoke and rip this shit out
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import logging
from typing import List, Dict, Optional

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


class AnalysisUtils:
    """Utilities for data analysis and visualization
     the place where numbers go to get dressed up for presentations
    """
    
    def __init__(self):
        self.config = Config
    
    @staticmethod
    def format_currency(x) -> str:
        """Format number as currency
        Because apparently humans can't read raw numbers without dollar signs
        """
        return f"${x:,.0f}" if pd.notnull(x) else "N/A"
    
    @staticmethod
    def format_large_number(x, suffix='') -> str:
        """Format large numbers with appropriate suffixes
        For when your data is too big for normal human comprehension
        """
        if pd.isnull(x):
            return "N/A"
        if x >= 1e9:
            return f"{x/1e9:.2f}B{suffix}"  # Look ma, I'm a billionaire (in data points)
        elif x >= 1e6:
            return f"{x/1e6:.1f}M{suffix}"  # Million-dollar dreams
        elif x >= 1e3:
            return f"{x/1e3:.0f}K{suffix}"  # Thousand-yard stare
        else:
            return f"{x:.0f}{suffix}"       # Just a regular peasant number
    
    @staticmethod
    def format_percentage(x) -> str:
        """Format number as percentage
        Because 0.157 is just confusing but 15.7% makes everyone an expert
        """
        return f"{x:.1f}%" if pd.notnull(x) else "N/A"
    
    def create_ranking_plot(self, df: pd.DataFrame, x_col: str, y_col: str, 
                           title: str, x_label: str, top_n: int = 15, 
                           save_path: Optional[str] = None) -> None:
        """Create a horizontal bar plot for rankings
        Because vertical bars are for amateur hour
        """
        plot_df = df.nlargest(top_n, x_col).copy()
        
        plt.figure(figsize=(14, 10))
        bars = plt.barh(plot_df[y_col], plot_df[x_col], 
                       color='skyblue', edgecolor='navy', alpha=0.7)
        
        # Add value labels on bars (because people love numbers on their numbers)
        for i, bar in enumerate(bars):
            width = bar.get_width()
            plt.text(width, bar.get_y() + bar.get_height()/2, 
                    f'{width:,.0f}', ha='left', va='center', fontweight='bold')
        
        # Format x-axis as currency if it's a value column (money makes everything prettier)
        if 'value' in x_col.lower() or 'zhvi' in x_col.lower():
            plt.gca().xaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
        
        plt.gca().invert_yaxis()  # Because we're rebels like that
        plt.title(title, fontsize=16, fontweight='bold', pad=20)
        plt.xlabel(x_label, fontsize=12)
        plt.ylabel('', fontsize=12)  # Empty y-label because we're minimalists
        plt.grid(axis='x', alpha=0.3)  # Subtle grid for that professional look
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"📊 Saved plot: {save_path}")
        
        plt.show()  # Ta-da! 🎉
    
    def create_scatter_plot(self, df: pd.DataFrame, x_col: str, y_col: str, 
                           title: str, x_label: str, y_label: str,
                           color_col: Optional[str] = None, size_col: Optional[str] = None,
                           save_path: Optional[str] = None) -> None:
        """Create a scatter plot with optional color and size mapping"""
        plt.figure(figsize=(12, 8))
        
        scatter_kwargs = {'alpha': 0.7}
        
        if color_col and color_col in df.columns:
            scatter_kwargs['c'] = df[color_col]
            scatter_kwargs['cmap'] = 'viridis'
        
        if size_col and size_col in df.columns:
            # Normalize sizes to reasonable range
            sizes = df[size_col].fillna(0)
            scatter_kwargs['s'] = (sizes - sizes.min()) / (sizes.max() - sizes.min()) * 200 + 20
        
        scatter = plt.scatter(df[x_col], df[y_col], **scatter_kwargs)
        
        # Add colorbar if color mapping is used
        if color_col and color_col in df.columns:
            cbar = plt.colorbar(scatter)
            cbar.set_label(color_col.replace('_', ' ').title())
        
        # Add city labels for interesting points
        if 'City' in df.columns:
            for idx, row in df.iterrows():
                if pd.notnull(row[x_col]) and pd.notnull(row[y_col]):
                    plt.annotate(row['City'], (row[x_col], row[y_col]), 
                               xytext=(5, 5), textcoords='offset points', 
                               fontsize=8, alpha=0.7)
        
        plt.xlabel(x_label, fontsize=12)
        plt.ylabel(y_label, fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"📊 Saved scatter plot: {save_path}")
        
        plt.show()
    
    def create_summary_table(self, df: pd.DataFrame, sort_col: str, 
                           columns_to_show: List[str], title: str,
                           ascending: bool = True, top_n: Optional[int] = None) -> pd.DataFrame:
        """Create a formatted summary table"""
        display_df = df.sort_values(sort_col, ascending=ascending).copy()
        
        if top_n:
            display_df = display_df.head(top_n)
        
        # Apply formatting to specific columns
        format_cols = {}
        for col in columns_to_show:
            if col in display_df.columns:
                if 'zhvi' in col.lower() or 'value' in col.lower() or 'income' in col.lower():
                    format_cols[col] = self.format_currency
                elif 'population' in col.lower() or 'housing' in col.lower():
                    format_cols[col] = lambda x: f"{x:,.0f}" if pd.notnull(x) else "N/A"
                elif 'per_' in col.lower() and 'billion' in col.lower():
                    format_cols[col] = lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A"
        
        # Apply formatting
        for col, formatter in format_cols.items():
            if col in display_df.columns:
                display_df[f"{col}_fmt"] = display_df[col].apply(formatter)
        
        display_cols = [col for col in columns_to_show if col in display_df.columns]
        result_df = display_df[display_cols]
        
        logger.info(f"\n📋 {title}")
        logger.info("=" * 80)
        print(result_df.to_string(index=False))
        
        return result_df
    
    def merge_datasets(self, zillow_df: pd.DataFrame, census_df: pd.DataFrame, 
                      restaurant_df: pd.DataFrame) -> pd.DataFrame:
        """Merge all datasets for comprehensive analysis"""
        logger.info("🔗 Merging datasets...")
        
        # Start with restaurant data as base (it has city names)
        merged = restaurant_df.copy()
        
        # Add city-to-ZIP mapping for joining with other datasets
        city_zip_mapping = {
            'San Francisco': '94102',  # Use representative ZIP for each city
            'Palo Alto': '94301',
            'Menlo Park': '94025',
            'Atherton': '94027',
            'Redwood City': '94061',
            'San Carlos': '94070',
            'Belmont': '94002',
            'Foster City': '94404',
            'San Mateo': '94401',
            'Burlingame': '94010',
            'Hillsborough': '94010',
            'Millbrae': '94030',
            'San Bruno': '94066',
            'South San Francisco': '94080',
            'Daly City': '94014',
            'Mountain View': '94041',
            'Los Altos': '94022',
            'Portola Valley': '94028'
        }
        
        # Add ZIP codes to restaurant data
        merged['zip_code'] = merged['City'].map(city_zip_mapping)
        
        # Merge with Zillow data (already processed by data_collector)
        if not zillow_df.empty:
            # The zillow_df from data_collector already has 'zhvi_latest' and proper column names
            if 'zip' in zillow_df.columns and 'zhvi_latest' in zillow_df.columns:
                zillow_subset = zillow_df[['zip', 'zhvi_latest']].copy()
                zillow_subset['zip_code'] = zillow_subset['zip'].astype(str)
                
                merged = merged.merge(zillow_subset[['zip_code', 'zhvi_latest']], 
                                    on='zip_code', how='left')
            elif 'RegionName' in zillow_df.columns:
                # Handle raw Zillow data if needed (fallback)
                value_cols = [col for col in zillow_df.columns if col.startswith('20')]
                if value_cols:
                    zillow_df_copy = zillow_df.copy()
                    zillow_df_copy['zhvi_latest'] = zillow_df_copy[value_cols].iloc[:, -1]
                    zillow_subset = zillow_df_copy[['RegionName', 'zhvi_latest']].copy()
                    zillow_subset['zip_code'] = zillow_subset['RegionName'].astype(str)
                    
                    merged = merged.merge(zillow_subset[['zip_code', 'zhvi_latest']], 
                                        on='zip_code', how='left')
        
        # Merge with Census data
        if not census_df.empty:
            # Check which zip column name is used
            if 'zip' in census_df.columns:
                census_cols = ['zip']
                zip_col = 'zip'
            elif 'zip_code' in census_df.columns:
                census_cols = ['zip_code']
                zip_col = 'zip_code'
            else:
                logger.warning("No zip column found in census data")
                zip_col = None
            
            if zip_col:
                # Add available columns
                if 'median_home_value' in census_df.columns:
                    census_cols.append('median_home_value')
                if 'median_income' in census_df.columns:
                    census_cols.append('median_income')
                if 'population' in census_df.columns:
                    census_cols.append('population')
                if 'housing_units' in census_df.columns:
                    census_cols.append('housing_units')
                    
                census_subset = census_df[census_cols].copy()
                
                # Rename zip column to match our standard
                if zip_col == 'zip':
                    census_subset['zip_code'] = census_subset['zip'].astype(str)
                    census_subset = census_subset.drop('zip', axis=1)
                
                merged = merged.merge(census_subset, on='zip_code', how='left')
        
        # Create derived metrics for quality analysis
        if 'zhvi_latest' in merged.columns and 'restaurant_count' in merged.columns:
            # Restaurants per billion dollars of property value
            merged['restaurants_per_billion_val'] = (
                merged['restaurant_count'] / (merged['zhvi_latest'] / 1_000_000_000)
            ).round(2)
            
            # Restaurants per thousand people
            if 'population' in merged.columns:
                merged['restaurants_per_1k_pop'] = (
                    merged['restaurant_count'] / (merged['population'] / 1000)
                ).round(2)
        
        # Add quality-based derived metrics
        if 'avg_rating' in merged.columns:
            # Quality tiers
            merged['quality_tier'] = pd.cut(
                merged['avg_rating'], 
                bins=[0, 3.5, 4.0, 4.5, 5.0], 
                labels=['Low', 'Good', 'Very Good', 'Excellent']
            )
        
        if 'high_rated_count' in merged.columns and 'restaurant_count' in merged.columns:
            # Percentage of high-rated restaurants
            merged['high_rated_percentage'] = (
                merged['high_rated_count'] / merged['restaurant_count'] * 100
            ).round(1)
        
        if 'expensive_count' in merged.columns and 'restaurant_count' in merged.columns:
            # Percentage of expensive restaurants
            merged['expensive_percentage'] = (
                merged['expensive_count'] / merged['restaurant_count'] * 100
            ).round(1)
        
        logger.info(f"✅ Merged dataset contains {len(merged)} cities with quality metrics")
        return merged
    
    def generate_insights_report(self, df: pd.DataFrame, save_path: Optional[str] = None) -> str:
        """Generate a comprehensive insights report"""
        report_lines = []
        report_lines.append("# 🍴💰 Forks & Fortunes Analysis Report")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        # Basic statistics
        report_lines.append("## 📊 Dataset Overview")
        report_lines.append(f"- Total cities analyzed: {len(df)}")
        report_lines.append(f"- Cities with restaurant data: {df['restaurant_count'].notna().sum()}")
        report_lines.append(f"- Average restaurants per city: {df['restaurant_count'].mean():.1f}")
        report_lines.append("")
        
        # Wealth insights
        if 'zhvi_latest' in df.columns:
            report_lines.append("## 🏠 Property Value Insights")
            top_expensive = df.nlargest(5, 'zhvi_latest')[['City', 'zhvi_latest']]
            report_lines.append("### Top 5 Most Expensive Cities (by ZHVI):")
            for _, row in top_expensive.iterrows():
                report_lines.append(f"- {row['City']}: {self.format_currency(row['zhvi_latest'])}")
            report_lines.append("")
        
        # Restaurant density insights
        if 'restaurants_per_billion_val' in df.columns:
            report_lines.append("## 🍽️ Restaurant Density Insights")
            underserved = df.nsmallest(5, 'restaurants_per_billion_val')[['City', 'restaurants_per_billion_val', 'restaurant_count']]
            report_lines.append("### Top 5 Under-served Wealthy Areas (fewest restaurants per billion $ property value):")
            for _, row in underserved.iterrows():
                if pd.notna(row['restaurants_per_billion_val']):
                    report_lines.append(f"- {row['City']}: {row['restaurants_per_billion_val']:.2f} restaurants/billion$ ({int(row['restaurant_count'])} total)")
            report_lines.append("")
        
        # Correlation insights
        if all(col in df.columns for col in ['zhvi_latest', 'restaurant_count']):
            corr = df[['zhvi_latest', 'restaurant_count']].corr().iloc[0, 1]
            report_lines.append("## 🔍 Key Correlations")
            report_lines.append(f"- Property value vs Restaurant count correlation: {corr:.3f}")
            if corr > 0.3:
                report_lines.append("  → Positive correlation: Wealthier areas tend to have more restaurants")
            elif corr < -0.3:
                report_lines.append("  → Negative correlation: Wealthier areas tend to have fewer restaurants")
            else:
                report_lines.append("  → Weak correlation: Property value weakly related to restaurant count")
            report_lines.append("")
        
        report = "\n".join(report_lines)
        
        if save_path:
            with open(save_path, 'w') as f:
                f.write(report)
            logger.info(f"📄 Saved insights report: {save_path}")
        
        return report


if __name__ == "__main__":
    utils = AnalysisUtils()
    
    test_data = pd.DataFrame({
        'City': ['Palo Alto', 'Atherton', 'San Francisco', 'Mountain View'],
        'zhvi_latest': [2500000, 4000000, 1200000, 1800000],
        'restaurant_count': [150, 80, 500, 120],
        'population': [65000, 7000, 850000, 80000]
    })
    
    print("Testing analysis utils with sample data:")
    print(test_data)
    
    # Test formatting functions
    print(f"\nFormatting tests:")
    print(f"Currency: {utils.format_currency(2500000)}")
    print(f"Large number: {utils.format_large_number(2500000)}")
    print(f"Percentage: {utils.format_percentage(0.157)}")
