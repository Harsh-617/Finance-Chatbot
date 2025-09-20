import requests
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# API Keys and URLs
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
CRYPTOCOMPARE_API_KEY = os.getenv('CRYPTOCOMPARE_API_KEY')
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")

CRYPTOCOMPARE_BASE_URL = "https://min-api.cryptocompare.com/data"
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# ============= CRYPTO DATA FETCHERS =============

def get_crypto_price_overview(symbol):
    """Get crypto price overview from CryptoCompare"""
    try:
        url = f"{CRYPTOCOMPARE_BASE_URL}/pricemultifull"
        params = {
            'fsyms': symbol.upper(),
            'tsyms': 'USD'
        }
        if CRYPTOCOMPARE_API_KEY:
            params['api_key'] = CRYPTOCOMPARE_API_KEY
            
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'RAW' in data and symbol.upper() in data['RAW'] and 'USD' in data['RAW'][symbol.upper()]:
            raw_data = data['RAW'][symbol.upper()]['USD']
            return {
                'price': raw_data.get('PRICE'),
                'percent_change_24h': raw_data.get('CHANGEPCT24HOUR'),
                'percent_change_7d': raw_data.get('CHANGEPCTDAY'),
                'market_cap_usd': raw_data.get('MKTCAP'),
                'volume_24h_usd': raw_data.get('VOLUME24HOURTO')
            }
        return None
        
    except Exception as e:
        print(f"Error fetching crypto price overview: {e}")
        return None

def get_crypto_supply_info(symbol):
    """Get crypto supply information from CoinGecko"""
    try:
        coin_id = find_coingecko_coin_id(symbol)
        if not coin_id:
            return None
            
        url = f"{COINGECKO_BASE_URL}/coins/{coin_id}"
        params = {
            'localization': 'false',
            'tickers': 'false',
            'market_data': 'true',
            'community_data': 'false',
            'developer_data': 'false',
            'sparkline': 'false'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        market_data = data.get('market_data', {})
        if market_data:
            return {
                'circulating_supply': market_data.get('circulating_supply'),
                'total_supply': market_data.get('total_supply'),
                'max_supply': market_data.get('max_supply')
            }
        return None
        
    except Exception as e:
        print(f"Error fetching crypto supply info: {e}")
        return None

def get_crypto_ath_atl(symbol):
    """Get crypto ATH/ATL from CoinGecko"""
    try:
        coin_id = find_coingecko_coin_id(symbol)
        if not coin_id:
            return None
            
        url = f"{COINGECKO_BASE_URL}/coins/{coin_id}"
        params = {
            'localization': 'false',
            'tickers': 'false',
            'market_data': 'true',
            'community_data': 'false',
            'developer_data': 'false',
            'sparkline': 'false'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        market_data = data.get('market_data', {})
        if market_data:
            return {
                'ath': market_data.get('ath', {}).get('usd'),
                'ath_date': market_data.get('ath_date', {}).get('usd'),
                'atl': market_data.get('atl', {}).get('usd'),
                'atl_date': market_data.get('atl_date', {}).get('usd')
            }
        return None
        
    except Exception as e:
        print(f"Error fetching crypto ATH/ATL: {e}")
        return None


def get_crypto_ohlc(symbol, time_period='30d'):
    """Crypto OHLC: daily candles, aggregated 7-day bar if 7d."""
    try:
        days_map = {'1d': 2, '7d': 7, '30d': 30, '90d': 90, '1y': 365}
        limit = days_map.get(time_period, 30)

        url = f"{CRYPTOCOMPARE_BASE_URL}/v2/histoday"
        params = {'fsym': symbol.upper(), 'tsym': 'USD', 'limit': limit}
        if CRYPTOCOMPARE_API_KEY:
            params['api_key'] = CRYPTOCOMPARE_API_KEY

        res = requests.get(url, params=params, timeout=10).json()
        if 'Data' not in res or 'Data' not in res['Data']:
            return None

        raw = res['Data']['Data']                      # list[dict]
        raw = raw[-days_map.get(time_period, 30):]     # slice requested span

        # ---- weekly aggregation (7-day bar) ----
        if time_period == '7d' and len(raw) == 7:
            return {'open':  raw[0]['open'],
                    'high':  max(d['high'] for d in raw),
                    'low':   min(d['low']  for d in raw),
                    'close': raw[-1]['close']}

        # ---- latest daily bar ----
        latest = raw[-1]
        return {'open': latest['open'], 'high': latest['high'],
                'low': latest['low'], 'close': latest['close']}

    except Exception as e:
        print(f"Crypto OHLC error: {e}")
        return None



def get_crypto_exchange_info(symbol):
    """Get crypto exchange information from CryptoCompare"""
    try:
        url = f"{CRYPTOCOMPARE_BASE_URL}/top/exchanges/full"
        params = {
            'fsym': symbol.upper(),
            'tsym': 'USD',
            'limit': 5
        }
        if CRYPTOCOMPARE_API_KEY:
            params['api_key'] = CRYPTOCOMPARE_API_KEY
            
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'Data' in data:
            exchange_data = []
            for exchange in data['Data']:
                exchange_data.append({
                    'exchange_name': exchange.get('exchange'),
                    'pair': f"{symbol.upper()}/USD",
                    'volume_24h': exchange.get('volume24h'),
                    'price': exchange.get('price')
                })
            return exchange_data
        return None
        
    except Exception as e:
        print(f"Error fetching crypto exchange info: {e}")
        return None

def get_crypto_metadata(symbol):
    """Get crypto metadata from CryptoCompare"""
    try:
        url = f"{CRYPTOCOMPARE_BASE_URL}/coinlist"
        params = {}
        if CRYPTOCOMPARE_API_KEY:
            params['api_key'] = CRYPTOCOMPARE_API_KEY
            
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'Data' in data and symbol.upper() in data['Data']:
            coin_data = data['Data'][symbol.upper()]
            return {
                'symbol': coin_data.get('Symbol'),
                'name': coin_data.get('CoinName'),
                'full_name': coin_data.get('FullName'),
                'algorithm': coin_data.get('Algorithm'),
                'proof_type': coin_data.get('ProofType'),
                'description': coin_data.get('Description', 'No description available')
            }
        return None
        
    except Exception as e:
        print(f"Error fetching crypto metadata: {e}")
        return None

def find_coingecko_coin_id(symbol):
    """Find CoinGecko coin ID from symbol"""
    try:
        # First try search API
        search_url = f"{COINGECKO_BASE_URL}/search"
        params = {'query': symbol}
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        search_data = response.json()
        
        # Look for exact symbol match
        for coin in search_data.get('coins', []):
            if coin.get('symbol', '').lower() == symbol.lower():
                return coin.get('id')
        
        # If not found, try coins list (limited to first 250 coins)
        coins_url = f"{COINGECKO_BASE_URL}/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 250,
            'page': 1
        }
        response = requests.get(coins_url, params=params, timeout=10)
        response.raise_for_status()
        coins_data = response.json()
        
        for coin in coins_data:
            if coin.get('symbol', '').lower() == symbol.lower():
                return coin.get('id')
        
        return None
        
    except Exception as e:
        print(f"Error finding CoinGecko coin ID: {e}")
        return None

# ============= STOCK DATA FETCHERS =============

def get_stock_price_overview(symbol):
    """Get stock price overview from Finnhub"""
    try:
        url = f"{FINNHUB_BASE_URL}/quote"
        params = {'symbol': symbol.upper(), 'token': FINNHUB_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching stock price overview: {e}")

    # ---------- Twelve Data fallback ----------
    try:
        url = "https://api.twelvedata.com/quote"
        params = {'symbol': symbol.upper(), 'apikey': TWELVE_DATA_API_KEY}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        # map Twelve Data fields to Finnhub format
        return {
            'c': data.get('close'),
            'h': data.get('high'),
            'l': data.get('low'),
            'o': data.get('open'),
            'pc': data.get('previous_close'),
            'dp': data.get('percent_change')
        }
    except Exception as e2:
        print(f"Twelve Data price fallback failed: {e2}")
        return None

def get_stock_fundamentals(symbol):
    """Get stock fundamentals from Finnhub"""
    try:
        url = f"{FINNHUB_BASE_URL}/stock/metric"
        params = {'symbol': symbol.upper(), 'metric': 'all', 'token': FINNHUB_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get('metric', {})
    except Exception as e:
        print(f"Error fetching stock fundamentals: {e}")

    # ---------- Twelve Data fallback ----------
    try:
        url = "https://api.twelvedata.com/statistics"
        params = {'symbol': symbol.upper(), 'apikey': TWELVE_DATA_API_KEY}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        # map to Finnhub-like dict
        d = data.get('statistics', {})
        return {
            'marketCapitalization': d.get('market_cap'),
            'peBasicExclExtraTTM':  d.get('pe_ratio'),
            'epsInclExtraItemsTTM': d.get('eps'),
            'beta': d.get('beta')
        }
    except Exception as e2:
        print(f"Twelve Data fundamentals fallback failed: {e2}")
        return None


def get_stock_ohlc(symbol, time_period='30d'):
    days_map = {'1d': 1, '7d': 7, '30d': 30, '90d': 90, '1y': 365}
    """Stock OHLC: Alpha-Vantage daily, aggregated 7-day bar if 7d, Finnhub fallback, Twelve Data final fallback."""
    try:
        # ---------- Alpha-Vantage block (keep your existing code) ----------
        url = "https://www.alphavantage.co/query"
        params = {'function': 'TIME_SERIES_DAILY', 'symbol': symbol.upper(),
                  'outputsize': 'full', 'apikey': ALPHA_VANTAGE_API_KEY}
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        if 'Error Message' in data or 'Note' in data:
            raise ValueError("AV error/limit")
        series = data.get('Time Series (Daily)', {})
        if not series:
            raise ValueError("No daily data")
        span = days_map.get(time_period, 30)
        dates = sorted(series.keys())[-span:]
        bars = [{'open': float(series[d]['1. open']),
                 'high': float(series[d]['2. high']),
                 'low':  float(series[d]['3. low']),
                 'close':float(series[d]['4. close'])} for d in dates]
        if time_period == '7d' and len(bars) == 7:
            return {'open': bars[0]['open'], 'high': max(b['high'] for b in bars),
                    'low':  min(b['low']  for b in bars), 'close': bars[-1]['close']}
        latest = bars[-1]
        return {'open': latest['open'], 'high': latest['high'],
                'low': latest['low'], 'close': latest['close']}
    except Exception as e:
        print(f"Alpha-Vantage OHLC failed for {symbol}: {e}")
        try:
            # ---------- Finnhub fallback (keep your existing code) ----------
            end = int(time.time())
            start = end - 86400 * (days_map.get(time_period, 30) + 1)
            url = f"{FINNHUB_BASE_URL}/stock/candle"
            params = {'symbol': symbol.upper(), 'resolution': 'D',
                      'from': start, 'to': end, 'token': FINNHUB_API_KEY}
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            if data.get('s') == 'ok' and len(data.get('c', [])) > 0:
                return {'open': data['o'][-1], 'high': data['h'][-1],
                        'low': data['l'][-1], 'close': data['c'][-1]}
        except Exception as e2:
            print(f"Finnhub fallback also failed: {e2}")

            # ---------- Twelve Data final fallback ----------
            try:
                interval = {'1d': '1min', '7d': '1day', '30d': '1day', '90d': '1day', '1y': '1day'}.get(time_period, '1day')
                url = "https://api.twelvedata.com/time_series"
                params = {'symbol': symbol.upper(), 'interval': interval,
                          'outputsize': str(days_map.get(time_period, 30) + 1),
                          'apikey': TWELVE_DATA_API_KEY}
                r = requests.get(url, params=params, timeout=10)
                r.raise_for_status()
                data = r.json()
                values = data.get('values', [])
                if not values:
                    raise ValueError("No data")
                latest = values[0]          # newest-first
                return {'open': float(latest['open']),
                        'high': float(latest['high']),
                        'low': float(latest['low']),
                        'close': float(latest['close'])}
            except Exception as e3:
                print(f"Twelve Data OHLC fallback failed: {e3}")
                return None
    return None


def get_stock_earnings(symbol):
    """Get stock earnings data from Finnhub"""
    try:
        url = f"{FINNHUB_BASE_URL}/stock/earnings"
        params = {'symbol': symbol.upper(), 'token': FINNHUB_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching stock earnings: {e}")

    # ---------- Twelve Data fallback ----------
    try:
        url = "https://api.twelvedata.com/earnings"
        params = {'symbol': symbol.upper(), 'apikey': TWELVE_DATA_API_KEY}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        # return list of quarterly records
        return data.get('earnings', [])
    except Exception as e2:
        print(f"Twelve Data earnings fallback failed: {e2}")
        return None
    

def get_stock_analyst_ratings(symbol):
    """Get stock analyst ratings from Finnhub"""
    try:
        url = f"{FINNHUB_BASE_URL}/stock/recommendation"
        params = {'symbol': symbol.upper(), 'token': FINNHUB_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data[0] if data else None
    except Exception as e:
        print(f"Error fetching stock analyst ratings: {e}")

    # ---------- Twelve Data fallback ----------
    try:
        url = "https://api.twelvedata.com/analyst_estimates"
        params = {'symbol': symbol.upper(), 'apikey': TWELVE_DATA_API_KEY}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        est = data.get('estimates', {})
        # map to Finnhub-like dict
        return {
            'strongBuy': est.get('strong_buy'),
            'buy': est.get('buy'),
            'hold': est.get('hold'),
            'sell': est.get('sell'),
            'strongSell': est.get('strong_sell')
        }
    except Exception as e2:
        print(f"Twelve Data analyst fallback failed: {e2}")
        return None
    

def get_stock_insider_ownership(symbol):
    """Get stock insider transactions from Finnhub"""
    try:
        url = f"{FINNHUB_BASE_URL}/stock/insider-transactions"
        params = {
            'symbol': symbol.upper(),
            'token': FINNHUB_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('data', [])[:5]  # Return top 5 transactions
        
    except Exception as e:
        print(f"Error fetching stock insider data: {e}")
        return None

def get_stock_technicals(symbol):
    """Get stock technical indicators from Alpha Vantage"""
    try:
        # Get RSI
        rsi_params = {
            'function': 'RSI',
            'symbol': symbol.upper(),
            'interval': 'daily',
            'time_period': 14,
            'series_type': 'close',
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        rsi_response = requests.get(ALPHA_VANTAGE_BASE_URL, params=rsi_params, timeout=15)
        rsi_data = rsi_response.json()
        
        # Get SMA
        sma_params = {
            'function': 'SMA',
            'symbol': symbol.upper(),
            'interval': 'daily',
            'time_period': 20,
            'series_type': 'close',
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        sma_response = requests.get(ALPHA_VANTAGE_BASE_URL, params=sma_params, timeout=15)
        sma_data = sma_response.json()
        
        # Extract latest values
        latest_rsi = None
        latest_sma = None
        
        rsi_values = rsi_data.get('Technical Analysis: RSI', {})
        if rsi_values:
            latest_date = max(rsi_values.keys())
            latest_rsi = rsi_values[latest_date]['RSI']
        
        sma_values = sma_data.get('Technical Analysis: SMA', {})
        if sma_values:
            latest_date = max(sma_values.keys())
            latest_sma = sma_values[latest_date]['SMA']
        
        return {
            'rsi': latest_rsi,
            'sma_20': latest_sma
        }
        
    except Exception as e:
        print(f"Error fetching stock technicals: {e}")
        return None

# ============= FOREX DATA FETCHERS =============

def get_forex_exchange_rate(base, quote):
    """Get forex exchange rate - Finnhub first, Alpha Vantage second, Twelve Data last"""
    result = get_forex_rate_finnhub(base, quote)
    if result:
        return result
    result = get_forex_rate_alpha_vantage(base, quote)
    if result:
        return result
    # ---------- final fallback ----------
    return get_forex_rate_twelve_data(base, quote)

def get_forex_rate_finnhub(base, quote):
    """Get forex rate from Finnhub"""
    try:
        forex_formats = [
            f"OANDA:{base.upper()}_{quote.upper()}",
            f"{base.upper()}{quote.upper()}=X",
            f"FOREX:{base.upper()}{quote.upper()}",
            f"{base.upper()}{quote.upper()}"
        ]
        
        for forex_symbol in forex_formats:
            try:
                url = f"{FINNHUB_BASE_URL}/quote"
                params = {
                    'symbol': forex_symbol,
                    'token': FINNHUB_API_KEY
                }
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data.get('c') and data.get('c') > 0:
                    return data
                    
            except Exception:
                continue
        
        return None
        
    except Exception as e:
        print(f"Error fetching forex rate from Finnhub: {e}")
        return None

def get_forex_rate_alpha_vantage(base, quote):
    """Get forex rate from Alpha Vantage"""
    try:
        params = {
            'function': 'CURRENCY_EXCHANGE_RATE',
            'from_currency': base.upper(),
            'to_currency': quote.upper(),
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if 'Realtime Currency Exchange Rate' in data:
            exchange_data = data['Realtime Currency Exchange Rate']
            current_rate = float(exchange_data.get('5. Exchange Rate', 0))
            
            # Try to get intraday data for high/low
            try:
                intraday_params = {
                    'function': 'FX_INTRADAY',
                    'from_symbol': base.upper(),
                    'to_symbol': quote.upper(),
                    'interval': '60min',
                    'apikey': ALPHA_VANTAGE_API_KEY
                }
                intraday_response = requests.get(ALPHA_VANTAGE_BASE_URL, params=intraday_params, timeout=15)
                intraday_data = intraday_response.json()
                
                time_series = intraday_data.get(f'Time Series FX ({intraday_params["interval"]})', {})
                if time_series:
                    latest_data = list(time_series.values())[0]
                    return {
                        'c': current_rate,
                        'dp': 0,
                        'h': float(latest_data.get('2. high', current_rate)),
                        'l': float(latest_data.get('3. low', current_rate))
                    }
            except Exception:
                pass
            
            return {
                'c': current_rate,
                'dp': 0,
                'h': current_rate,
                'l': current_rate
            }
        
        return None
        
    except Exception as e:
        print(f"Error fetching forex rate from Alpha Vantage: {e}")
        return None


def get_forex_rate_twelve_data(base, quote):
    """Last-resort forex rate from Twelve Data"""
    try:
        url = "https://api.twelvedata.com/quote"
        params = {'symbol': f"{base.upper()}/{quote.upper()}",
                  'apikey': TWELVE_DATA_API_KEY}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return {
            'c': float(data['close']),
            'h': float(data['high']),
            'l': float(data['low']),
            'dp': float(data.get('percent_change', 0))
        }
    except Exception as e:
        print(f"Twelve Data forex fallback failed: {e}")
        return None


def get_forex_ohlc(base, quote, timeframe='daily'):
    """Get forex OHLC data from Finnhub"""
    try:
        end_date = int(time.time())
        
        if timeframe == 'daily':
            start_date = end_date - (24 * 60 * 60)
            resolution = 'D'
        elif timeframe == 'weekly':
            start_date = end_date - (7 * 24 * 60 * 60)
            resolution = 'W'
        else:  # monthly
            start_date = end_date - (30 * 24 * 60 * 60)
            resolution = 'M'
        
        url = f"{FINNHUB_BASE_URL}/forex/candle"
        params = {
            'symbol': f"OANDA:{base.upper()}_{quote.upper()}",
            'resolution': resolution,
            'from': start_date,
            'to': end_date,
            'token': FINNHUB_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('s') == 'ok' and len(data.get('o', [])) > 0:
            return {
                'open': data['o'][-1],
                'high': data['h'][-1],
                'low': data['l'][-1],
                'close': data['c'][-1]
            }
        return None
        
    except Exception as e:
        print(f"Error fetching forex OHLC: {e}")
        return None

def get_forex_historical_rate(base, quote, date):
    """Get historical forex rate from Finnhub"""
    try:
        if isinstance(date, str):
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            timestamp = int(date_obj.timestamp())
        else:
            timestamp = int(date) if date else int((datetime.now() - timedelta(days=1)).timestamp())
        
        url = f"{FINNHUB_BASE_URL}/forex/candle"
        params = {
            'symbol': f"OANDA:{base.upper()}_{quote.upper()}",
            'resolution': 'D',
            'from': timestamp - 86400,
            'to': timestamp + 86400,
            'token': FINNHUB_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('s') == 'ok' and len(data.get('c', [])) > 0:
            return {
                'date': date,
                'rate': data['c'][-1]
            }
        return None
        
    except Exception as e:
        print(f"Error fetching forex historical rate: {e}")
        return None

def get_forex_economic_data(country='US'):
    """Get economic data from Finnhub"""
    try:
        url = f"{FINNHUB_BASE_URL}/calendar/economic"
        params = {
            'token': FINNHUB_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if country and 'economicCalendar' in data:
            filtered_data = []
            for event in data['economicCalendar']:
                if event.get('country', '').upper() == country.upper():
                    filtered_data.append(event)
            return filtered_data[:10]
        
        return data.get('economicCalendar', [])[:10]
        
    except Exception as e:
        print(f"Error fetching forex economic data: {e}")
        return None


# ========== TOP-MOVERS FETCHERS ==========
def get_top_crypto_by_mcap(limit=10):
    """Top cryptos by market-cap from CoinGecko"""
    try:
        url = f"{COINGECKO_BASE_URL}/coins/markets"
        params = {'vs_currency':'usd','order':'market_cap_desc','per_page':limit,'page':1}
        r = requests.get(url, params=params, timeout=10).json()
        return [{'symbol':c['symbol'].upper(),'name':c['name'],'price':c['current_price'],
                 'mcap':c['market_cap'],'change_24h':c.get('price_change_percentage_24h')} for c in r]
    except Exception as e:
        print('Top crypto error:',e); return None

def get_top_stocks_by_mcap(limit=10):
    import os, requests, traceback

    # 1. Finnhub (keep your existing block)
    try:
        url = f"{FINNHUB_BASE_URL}/stock/most-active"
        r = requests.get(url, params={'token': FINNHUB_API_KEY}, timeout=10)
        if r.status_code != 200 or not r.text.startswith('{'):
            raise ValueError('Finnhub returned non-JSON')
        fh_data = r.json()
        most_active = fh_data.get('mostActiveStock', [])[:limit]
        if most_active:
            out = []
            for item in most_active:
                sym = item['symbol']
                quote = get_stock_price_overview(sym)
                out.append({'symbol': sym,
                            'name': item.get('companyName', 'N/A'),
                            'price': quote.get('c') if quote else None,
                            'change_24h': quote.get('dp') if quote else None,
                            'mcap': None})
            return out
    except Exception as e:
        print('FH most-active failed:', e)

    # 2. Alpha-Vantage fallback (keep your existing block)
    try:
        url = 'https://www.alphavantage.co/query'
        params = {'function': 'TOP_GAINERS_LOSERS', 'apikey': ALPHA_VANTAGE_API_KEY}
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        av_data = r.json()
        most_active = av_data.get('most_actively_traded', [])[:limit]
        if most_active:
            out = []
            for item in most_active:
                pc = item['change_percentage'].strip('%')
                out.append({'symbol': item['ticker'],
                            'name': item.get('company_name', item['ticker']),
                            'price': float(item['price']),
                            'change_24h': float(pc),
                            'mcap': None})
            return out
    except Exception as e:
        print('AV fallback failed:', e)
        traceback.print_exc()

    # 3. ---------- Twelve Data final fallback ----------
    try:
        url = "https://api.twelvedata.com/most_active"
        params = {'apikey': TWELVE_DATA_API_KEY}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        symbols = data.get('most_active', [])[:limit]
        out = []
        for item in symbols:
            out.append({'symbol': item['symbol'],
                        'name': item.get('name', item['symbol']),
                        'price': float(item['price']),
                        'change_24h': float(item['change_percent'].strip('%')),
                        'mcap': None})
        return out
    except Exception as e3:
        print("Twelve Data top-movers fallback failed:", e3)
        traceback.print_exc()

    return None

def get_top_forex_pairs(limit=10):
    """Return hard-coded major pairs (free forex APIs rarely give ranked list)"""
    majors = ['EURUSD','USDJPY','GBPUSD','AUDUSD','USDCAD','USDCHF','NZDUSD',
              'EURJPY','GBPJPY','EURGBP'][:limit]
    out = []
    for pair in majors:
        base,quote = pair[:3],pair[3:]
        data = get_forex_exchange_rate(base,quote)
        if data:
            out.append({'symbol':pair,'name':f'{base}/{quote}',
                        'price':data.get('c'),'change_24h':data.get('dp')})
    return out or None