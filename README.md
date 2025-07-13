# Forks & Fortunes

An analysis of the relationship between wealth and restaurant availability in the Bay Area.

## Overview

This project explores how property values in Bay Area cities correlate with the number and quality of their restaurants. It uses data from the US Census, Zillow, and the Google Places API to generate insights, rankings, and interactive maps.

## Features

-   **Data Integration**: Combines demographic, property value, and restaurant data.
-   **Quality Scoring**: Uses a custom algorithm to score restaurants based on ratings, reviews, and price.
-   **Wealth Tier Analysis**: Groups cities into wealth tiers for comparative analysis.
-   **Visualization**: Generates charts and interactive maps to display the findings.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd forks-and-fortunes
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up API Keys**:
    -   Get a **Google Places API Key** from the [Google Cloud Console](https://console.cloud.google.com/).
    -   Get a **US Census API Key** from the [Census Bureau](https://www.census.gov/developers/).
    -   Add your keys to the `config.py` file.

4.  **Add Zillow Data**:
    -   Download the Zillow Home Value Index (ZHVI) data for ZIP codes from the [Zillow research page](https://www.zillow.com/research/data/).
    -   Place the CSV file in the project's root directory and update the `ZILLOW_FILE` path in `config.py`.

## Usage

You can run the analysis from the command line with several options:

-   **Full analysis** (all 18 cities):
    ```bash
    python main.py
    ```

-   **Test mode** (3 cities for a quick run):
    ```bash
    python main.py --mode test
    ```

-   **Analyze a specific wealth tier**:
    ```bash
    python main.py --mode tier --tier ultra_wealthy
    ```

-   **List available cities and tiers**:
    ```bash
    python main.py --list-cities
    ```

## Output

The analysis generates several output files in the `results/` and `maps/` directories:

-   `results/merged_analysis.csv`: The complete dataset with all metrics.
-   `results/insights_report.md`: A summary of the key findings.
-   `results/*.png`: Ranking charts and scatter plots.
-   `maps/*.html`: Interactive maps for each city, color-coded by restaurant quality.
