import requests
import os
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta
from dotenv import load_dotenv
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Load environment variables
load_dotenv()

def create_price_chart(symbol, time_period, asset_type):
    """Create price charts for stocks and crypto using CoinGecko and Alpha Vantage APIs"""
    try:
        # Calculate date range
        days_map = {"1d": 1, "7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(time_period, 30)

        if asset_type == "crypto":
            return _create_crypto_chart(symbol, time_period, days)
        
        elif asset_type == "stock":
            return _create_stock_chart(symbol, time_period, days)

        return {'success': False, 'error': 'Invalid asset type'}

    except Exception as e:
        return {'success': False, 'error': f'Error creating chart: {str(e)}'}

def _create_crypto_chart(symbol, time_period, days):
    """Create crypto price chart using CoinGecko API"""
    try:
        coingecko_base_url = "https://api.coingecko.com/api/v3"
        
        # First try to find the coin ID
        coin_id = None
        
        # Try direct symbol first (lowercase)
        url = f"{coingecko_base_url}/coins/{symbol.lower()}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'daily' if days > 1 else 'hourly'
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            # Search for coin ID using search endpoint
            search_url = f"{coingecko_base_url}/search"
            search_params = {'query': symbol}
            search_response = requests.get(search_url, params=search_params, timeout=10)
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                coins = search_data.get('coins', [])
                
                # Look for exact symbol match
                for coin in coins:
                    if coin.get('symbol', '').upper() == symbol.upper():
                        coin_id = coin.get('id')
                        break
                
                if coin_id:
                    url = f"{coingecko_base_url}/coins/{coin_id}/market_chart"
                    response = requests.get(url, params=params, timeout=10)
                else:
                    return {'success': False, 'error': 'Cryptocurrency not found'}
            else:
                return {'success': False, 'error': 'Error searching for cryptocurrency'}

        if response.status_code == 200:
            data = response.json()
            prices = data.get('prices', [])
            
            if not prices:
                return {'success': False, 'error': 'No price data available'}

            # Convert to DataFrame
            df = pd.DataFrame(prices, columns=['timestamp', 'price'])
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms')

            # Create chart
            plt.figure(figsize=(12, 6))
            plt.plot(df['date'], df['price'], linewidth=2, color='#f7931a')
            plt.title(f'{symbol.upper()} Price Chart ({time_period})', fontsize=16, fontweight='bold')
            plt.xlabel('Date')
            plt.ylabel('Price (USD)')
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)

            # Format y-axis
            if df['price'].max() > 1000:
                plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            else:
                plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.2f}'))

            plt.tight_layout()

            # Save to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            chart_b64 = base64.b64encode(img_buffer.read()).decode()
            plt.close()

            return {
                'success': True,
                'chart_data': chart_b64,
                'current_price': df['price'].iloc[-1],
                'price_change': ((df['price'].iloc[-1] - df['price'].iloc[0]) / df['price'].iloc[0] * 100),
                'symbol': symbol.upper()
            }
        else:
            return {'success': False, 'error': 'Failed to fetch cryptocurrency data'}

    except Exception as e:
        return {'success': False, 'error': f'Error creating crypto chart: {str(e)}'}

def _create_stock_chart(symbol, time_period, days):
    """Create stock price chart using Alpha Vantage API"""
    try:
        alpha_vantage_api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if not alpha_vantage_api_key:
            return {'success': False, 'error': 'Alpha Vantage API key required for stock charts'}

        alpha_vantage_base_url = "https://www.alphavantage.co/query"
        
        # Determine the function and outputsize based on time period
        if days <= 7:
            # Use intraday data for short periods
            function = 'TIME_SERIES_INTRADAY'
            interval = '60min'  # 1 hour intervals
            params = {
                'function': function,
                'symbol': symbol.upper(),
                'interval': interval,
                'apikey': alpha_vantage_api_key,
                'outputsize': 'compact'
            }
            time_series_key = f'Time Series ({interval})'
        elif days <= 100:
            # Use daily data for medium periods
            function = 'TIME_SERIES_DAILY'
            params = {
                'function': function,
                'symbol': symbol.upper(),
                'apikey': alpha_vantage_api_key,
                'outputsize': 'compact' if days <= 100 else 'full'
            }
            time_series_key = 'Time Series (Daily)'
        else:
            # Use daily data with full output for longer periods
            function = 'TIME_SERIES_DAILY'
            params = {
                'function': function,
                'symbol': symbol.upper(),
                'apikey': alpha_vantage_api_key,
                'outputsize': 'full'
            }
            time_series_key = 'Time Series (Daily)'

        print(f"DEBUG - Alpha Vantage request: {function} for {symbol} with params: {params}")

        response = requests.get(alpha_vantage_base_url, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()
            print(f"DEBUG - Alpha Vantage response keys: {list(data.keys())}")

            # Check for API limit or error messages
            if 'Error Message' in data:
                return {'success': False, 'error': f'Alpha Vantage error: {data["Error Message"]}'}
            
            if 'Note' in data:
                return {'success': False, 'error': 'API rate limit reached. Please try again later.'}

            if time_series_key not in data:
                return {'success': False, 'error': f'No time series data found. Available keys: {list(data.keys())}'}

            time_series = data[time_series_key]
            
            if not time_series:
                return {'success': False, 'error': 'No stock data available'}

            # Convert to DataFrame
            dates = []
            prices = []
            
            # Sort by date and limit to requested period
            sorted_dates = sorted(time_series.keys(), reverse=True)
            
            for date_str in sorted_dates[:days * 24 if function == 'TIME_SERIES_INTRADAY' else days]:
                try:
                    if function == 'TIME_SERIES_INTRADAY':
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    else:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    dates.append(date_obj)
                    prices.append(float(time_series[date_str]['4. close']))
                except (ValueError, KeyError) as e:
                    print(f"DEBUG - Error parsing date {date_str}: {e}")
                    continue

            if not dates or not prices:
                return {'success': False, 'error': 'No valid price data found'}

            # Create DataFrame and sort by date (ascending)
            df = pd.DataFrame({
                'date': dates,
                'price': prices
            }).sort_values('date')

            # Limit to requested time period
            if days < len(df):
                cutoff_date = df['date'].max() - timedelta(days=days)
                df = df[df['date'] >= cutoff_date]

            print(f"DEBUG - Final dataset: {len(df)} data points from {df['date'].min()} to {df['date'].max()}")

            # Create chart
            plt.figure(figsize=(12, 6))
            plt.plot(df['date'], df['price'], linewidth=2, color='#1f77b4')
            plt.title(f'{symbol.upper()} Stock Price Chart ({time_period})', fontsize=16, fontweight='bold')
            plt.xlabel('Date')
            plt.ylabel('Price (USD)')
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.2f}'))
            plt.tight_layout()

            # Save to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            chart_b64 = base64.b64encode(img_buffer.read()).decode()
            plt.close()

            return {
                'success': True,
                'chart_data': chart_b64,
                'current_price': df['price'].iloc[-1],
                'price_change': ((df['price'].iloc[-1] - df['price'].iloc[0]) / df['price'].iloc[0] * 100),
                'symbol': symbol.upper()
            }
        else:
            return {'success': False, 'error': f'Failed to fetch stock data from Alpha Vantage. Status: {response.status_code}'}

    except Exception as e:
        return {'success': False, 'error': f'Error creating stock chart: {str(e)}'}