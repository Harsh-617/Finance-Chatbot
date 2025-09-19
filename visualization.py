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
    """1-day crypto chart via CryptoCompare (you have API key)"""
    import traceback, requests, io, base64, matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import pandas as pd
    from dotenv import load_dotenv
    load_dotenv()

    print(f'[CHART-CRYPTO] symbol={symbol} period={time_period} days={days}')

    try:
        api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
        base    = "https://min-api.cryptocompare.com/data"

        # ---- 1. hourly history for 1-day ----
        url  = f"{base}/v2/histohour"
        params = {
            'fsym': symbol.upper(),
            'tsym': 'USD',
            'limit': days * 24,          # 24 hours for 1d
            'api_key': api_key
        }
        r = requests.get(url, params=params, timeout=15)
        print('[CHART-CRYPTO] histohour status:', r.status_code)
        if r.status_code != 200:
            return {'success': False, 'error': f'CryptoCompare {r.status_code}'}

        data = r.json()
        raw  = data.get('Data', {}).get('Data', [])
        if not raw:
            return {'success': False, 'error': 'No hourly data'}

        # ---- 2. build DataFrame ----
        df = pd.DataFrame(raw)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df = df.sort_values('time')

        # ---- 3. plot ----
        plt.figure(figsize=(12, 6))
        plt.plot(df['time'], df['close'], color='#f7931a', linewidth=2)
        plt.title(f'{symbol.upper()} Price Chart ({time_period})', fontsize=16, fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel('Price (USD)')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        img.seek(0)
        b64 = base64.b64encode(img.read()).decode()

        # ---- 4. same return shape ----
        return {
            'success': True,
            'chart_data': b64,
            'current_price': float(df['close'].iloc[-1]),
            'price_change': float(((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100)),
            'symbol': symbol.upper()
        }

    except Exception as e:
        print('[CHART-CRYPTO] exception:', e)
        traceback.print_exc()
        return {'success': False, 'error': f'Crypto chart error: {e}'}
    

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