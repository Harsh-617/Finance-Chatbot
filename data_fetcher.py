import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time

# Load environment variables
load_dotenv()

class DataFetcher:
    def __init__(self):
        self.finnhub_api_key = os.getenv('FINNHUB_API_KEY')
        self.alpha_vantage_api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.cryptocompare_api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
        self.cryptocompare_base_url = "https://min-api.cryptocompare.com/data"
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        self.finnhub_base_url = "https://finnhub.io/api/v1"
        self.alpha_vantage_base_url = "https://www.alphavantage.co/query"

    # ============= CRYPTO DATA FETCHERS (CryptoCompare & CoinGecko) =============
    
    def get_crypto_price_overview(self, symbol):
        """Get crypto price overview from CryptoCompare"""
        try:
            url = f"{self.cryptocompare_base_url}/pricemultifull"
            params = {
                'fsyms': symbol.upper(),
                'tsyms': 'USD',
                'api_key': self.cryptocompare_api_key
            }
            response = requests.get(url, params=params)
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

    def get_crypto_supply_info(self, symbol):
        """Get crypto supply information from CoinGecko with improved symbol mapping"""
        try:
            # Common symbol mappings
            symbol_mappings = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum', 
                'SOL': 'solana',
                'ADA': 'cardano',
                'DOT': 'polkadot',
                'MATIC': 'polygon',
                'AVAX': 'avalanche-2',
                'LINK': 'chainlink',
                'UNI': 'uniswap',
                'LTC': 'litecoin',
                'BCH': 'bitcoin-cash',
                'XRP': 'ripple',
                'DOGE': 'dogecoin',
                'SHIB': 'shiba-inu',
                'TRX': 'tron',
                'ATOM': 'cosmos',
                'FTM': 'fantom',
                'ALGO': 'algorand',
                'VET': 'vechain',
                'ICP': 'internet-computer',
                'NEAR': 'near',
                'FLOW': 'flow',
                'MANA': 'decentraland',
                'SAND': 'the-sandbox',
                'APE': 'apecoin',
                'CRO': 'cronos',
                'LDO': 'lido-dao'
            }
            
            # First try direct symbol mapping
            coin_id = symbol_mappings.get(symbol.upper())
            
            if not coin_id:
                # Fallback to search API
                search_url = f"{self.coingecko_base_url}/search"
                params = {'query': symbol}
                search_response = requests.get(search_url, params=params)
                search_response.raise_for_status()
                search_data = search_response.json()
                
                # Look for exact symbol match in coins
                for coin in search_data.get('coins', []):
                    if coin.get('symbol', '').lower() == symbol.lower():
                        coin_id = coin.get('id')
                        break
                
                if not coin_id:
                    print(f"Coin ID not found for symbol: {symbol}")
                    return None
            
            print(f"DEBUG - Using coin ID: {coin_id} for symbol: {symbol}")
            
            # Get detailed coin data including supply information
            coin_url = f"{self.coingecko_base_url}/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'false',
                'developer_data': 'false',
                'sparkline': 'false'
            }
            
            response = requests.get(coin_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            print(f"DEBUG - CoinGecko response keys: {list(data.keys())}")
            
            # Extract supply data from market_data
            market_data = data.get('market_data', {})
            
            if not market_data:
                print("No market data found")
                return None
                
            supply_data = {
                'circulating_supply': market_data.get('circulating_supply'),
                'total_supply': market_data.get('total_supply'),
                'max_supply': market_data.get('max_supply')
            }
            
            print(f"DEBUG - Supply data: {supply_data}")
            return supply_data
            
        except Exception as e:
            print(f"Error fetching crypto supply info from CoinGecko: {e}")
            return None

    def get_crypto_ath_atl(self, symbol):
        """Get crypto ATH/ATL from CoinGecko"""
        try:
            # Use the same mapping logic as supply info
            symbol_mappings = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum', 
                'SOL': 'solana',
                'ADA': 'cardano',
                'DOT': 'polkadot',
                'MATIC': 'polygon',
                'AVAX': 'avalanche-2',
                'LINK': 'chainlink',
                'UNI': 'uniswap',
                'LTC': 'litecoin',
                'BCH': 'bitcoin-cash',
                'XRP': 'ripple',
                'DOGE': 'dogecoin'
            }
            
            coin_id = symbol_mappings.get(symbol.upper())
            
            if not coin_id:
                # Fallback to coins list
                coins_url = f"{self.coingecko_base_url}/coins/list"
                response = requests.get(coins_url)
                response.raise_for_status()
                coins = response.json()
                
                for coin in coins:
                    if coin['symbol'].lower() == symbol.lower():
                        coin_id = coin['id']
                        break
            
            if not coin_id:
                return None
            
            # Get coin data
            coin_url = f"{self.coingecko_base_url}/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'false',
                'developer_data': 'false',
                'sparkline': 'false'
            }
            response = requests.get(coin_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            market_data = data.get('market_data', {})
            
            return {
                'ath': market_data.get('ath', {}).get('usd'),
                'ath_date': market_data.get('ath_date', {}).get('usd'),
                'atl': market_data.get('atl', {}).get('usd'),
                'atl_date': market_data.get('atl_date', {}).get('usd')
            }
            
        except Exception as e:
            print(f"Error fetching crypto ATH/ATL: {e}")
            return None

    def get_crypto_ohlc(self, symbol, timeframe='daily'):
        """Get crypto OHLC data from CryptoCompare"""
        try:
            # Determine the endpoint and limit based on timeframe
            if timeframe == 'daily':
                endpoint = 'v2/histoday'
                limit = 1
            elif timeframe == 'weekly':
                endpoint = 'v2/histoday'
                limit = 7
            else:  # monthly
                endpoint = 'v2/histoday'
                limit = 30
            
            url = f"{self.cryptocompare_base_url}/{endpoint}"
            params = {
                'fsym': symbol.upper(),
                'tsym': 'USD',
                'limit': limit,
                'api_key': self.cryptocompare_api_key
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'Data' in data and 'Data' in data['Data'] and len(data['Data']['Data']) > 0:
                latest = data['Data']['Data'][-1]  # Get most recent OHLC
                return {
                    'open': latest['open'],
                    'high': latest['high'],
                    'low': latest['low'],
                    'close': latest['close']
                }
            
            return None
            
        except Exception as e:
            print(f"Error fetching crypto OHLC: {e}")
            return None

    def get_crypto_exchange_info(self, symbol):
        """Get crypto exchange information from CryptoCompare"""
        try:
            url = f"{self.cryptocompare_base_url}/top/exchanges/full"
            params = {
                'fsym': symbol.upper(),
                'tsym': 'USD',
                'limit': 5,
                'api_key': self.cryptocompare_api_key
            }
            response = requests.get(url, params=params)
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

    def get_crypto_metadata(self, symbol):
        """Get crypto metadata from CryptoCompare"""
        try:
            url = f"{self.cryptocompare_base_url}/coinlist"
            params = {
                'api_key': self.cryptocompare_api_key
            }
            response = requests.get(url, params=params)
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

    # ============= STOCK DATA FETCHERS (Finnhub) =============

    def get_stock_price_overview(self, symbol):
        """Get stock price overview from Finnhub"""
        try:
            url = f"{self.finnhub_base_url}/quote"
            params = {
                'symbol': symbol.upper(),
                'token': self.finnhub_api_key
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return data
            
        except Exception as e:
            print(f"Error fetching stock price overview: {e}")
            return None

    def get_stock_fundamentals(self, symbol):
        """Get stock fundamentals from Finnhub"""
        try:
            url = f"{self.finnhub_base_url}/stock/metric"
            params = {
                'symbol': symbol.upper(),
                'metric': 'all',
                'token': self.finnhub_api_key
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return data.get('metric', {})
            
        except Exception as e:
            print(f"Error fetching stock fundamentals: {e}")
            return None

    def get_stock_ohlc(self, symbol, timeframe='daily'):
        """Get stock OHLC data from Finnhub"""
        try:
            # Calculate date range
            end_date = int(time.time())
            if timeframe == 'daily':
                start_date = end_date - (24 * 60 * 60)  # 1 day
                resolution = 'D'
            elif timeframe == 'weekly':
                start_date = end_date - (7 * 24 * 60 * 60)  # 1 week
                resolution = 'W'
            else:
                start_date = end_date - (30 * 24 * 60 * 60)  # 1 month
                resolution = 'M'
            
            url = f"{self.finnhub_base_url}/stock/candle"
            params = {
                'symbol': symbol.upper(),
                'resolution': resolution,
                'from': start_date,
                'to': end_date,
                'token': self.finnhub_api_key
            }
            response = requests.get(url, params=params)
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
            print(f"Error fetching stock OHLC: {e}")
            return None

    def get_stock_earnings(self, symbol):
        """Get stock earnings data from Finnhub"""
        try:
            url = f"{self.finnhub_base_url}/stock/earnings"
            params = {
                'symbol': symbol.upper(),
                'token': self.finnhub_api_key
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            print(f"DEBUG - Raw earnings data: {data}")
            return data
            
        except Exception as e:
            print(f"Error fetching stock earnings: {e}")
            return None

    def get_stock_analyst_ratings(self, symbol):
        """Get stock analyst ratings from Finnhub"""
        try:
            url = f"{self.finnhub_base_url}/stock/recommendation"
            params = {
                'symbol': symbol.upper(),
                'token': self.finnhub_api_key
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return data[0] if data else None
            
        except Exception as e:
            print(f"Error fetching stock analyst ratings: {e}")
            return None

    def get_stock_insider_ownership(self, symbol):
        """Get stock insider transactions from Finnhub"""
        try:
            url = f"{self.finnhub_base_url}/stock/insider-transactions"
            params = {
                'symbol': symbol.upper(),
                'token': self.finnhub_api_key
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return data.get('data', [])[:5]  # Return top 5 transactions
            
        except Exception as e:
            print(f"Error fetching stock insider data: {e}")
            return None

    def get_stock_technicals(self, symbol):
        """Get stock technical indicators from Alpha Vantage"""
        try:
            # RSI
            rsi_params = {
                'function': 'RSI',
                'symbol': symbol.upper(),
                'interval': 'daily',
                'time_period': 14,
                'series_type': 'close',
                'apikey': self.alpha_vantage_api_key
            }
            rsi_response = requests.get(self.alpha_vantage_base_url, params=rsi_params)
            rsi_data = rsi_response.json()
            
            # SMA
            sma_params = {
                'function': 'SMA',
                'symbol': symbol.upper(),
                'interval': 'daily',
                'time_period': 20,
                'series_type': 'close',
                'apikey': self.alpha_vantage_api_key
            }
            sma_response = requests.get(self.alpha_vantage_base_url, params=sma_params)
            sma_data = sma_response.json()
            
            # Extract latest values
            rsi_values = rsi_data.get('Technical Analysis: RSI', {})
            sma_values = sma_data.get('Technical Analysis: SMA', {})
            
            latest_rsi = None
            latest_sma = None
            
            if rsi_values:
                latest_date = max(rsi_values.keys())
                latest_rsi = rsi_values[latest_date]['RSI']
            
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

    # ============= FOREX DATA FETCHERS (Multiple APIs) =============

    def get_forex_exchange_rate(self, base, quote):
        """Get forex exchange rate - improved with better API handling"""
        print(f"DEBUG - Fetching forex rate for {base}/{quote}")
        
        # Try Alpha Vantage first (most reliable for major pairs)
        try:
            url = self.alpha_vantage_base_url
            params = {
                'function': 'CURRENCY_EXCHANGE_RATE',
                'from_currency': base.upper(),
                'to_currency': quote.upper(),
                'apikey': self.alpha_vantage_api_key
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            print(f"DEBUG - Alpha Vantage response: {data}")
            
            if 'Realtime Currency Exchange Rate' in data:
                exchange_data = data['Realtime Currency Exchange Rate']
                current_rate = float(exchange_data.get('5. Exchange Rate', 0))
                
                # Try to get additional data
                try:
                    # Get intraday data for high/low
                    intraday_params = {
                        'function': 'FX_INTRADAY',
                        'from_symbol': base.upper(),
                        'to_symbol': quote.upper(),
                        'interval': '60min',
                        'apikey': self.alpha_vantage_api_key
                    }
                    intraday_response = requests.get(url, params=intraday_params)
                    intraday_data = intraday_response.json()
                    
                    time_series = intraday_data.get(f'Time Series FX ({intraday_params["interval"]})', {})
                    if time_series:
                        latest_data = list(time_series.values())[0]
                        return {
                            'c': current_rate,
                            'dp': 0,  # Calculate if we have previous data
                            'h': float(latest_data.get('2. high', current_rate)),
                            'l': float(latest_data.get('3. low', current_rate))
                        }
                except:
                    pass
                
                return {
                    'c': current_rate,
                    'dp': 0,
                    'h': current_rate,
                    'l': current_rate
                }
                
        except Exception as e:
            print(f"Alpha Vantage forex error: {e}")
        
        # Fallback to Finnhub with various formats
        forex_formats = [
            f"OANDA:{base.upper()}_{quote.upper()}",
            f"{base.upper()}{quote.upper()}=X",
            f"FOREX:{base.upper()}{quote.upper()}",
            f"{base.upper()}{quote.upper()}"
        ]
        
        for forex_symbol in forex_formats:
            try:
                quote_url = f"{self.finnhub_base_url}/quote"
                params = {
                    'symbol': forex_symbol,
                    'token': self.finnhub_api_key
                }
                response = requests.get(quote_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                print(f"DEBUG - Finnhub response for {forex_symbol}: {data}")
                
                if data.get('c') and data.get('c') > 0:  # Valid rate
                    return data
                    
            except Exception as e:
                print(f"Finnhub error for {forex_symbol}: {e}")
                continue
        
        # Try a simple exchange rate API as final fallback
        try:
            fallback_url = f"https://api.exchangerate-api.com/v4/latest/{base.upper()}"
            response = requests.get(fallback_url)
            response.raise_for_status()
            data = response.json()
            
            if quote.upper() in data.get('rates', {}):
                rate = data['rates'][quote.upper()]
                return {
                    'c': rate,
                    'dp': 0,
                    'h': rate,
                    'l': rate
                }
        except Exception as e:
            print(f"Fallback API error: {e}")
        
        print("All forex sources failed")
        return None

    def get_forex_ohlc(self, base, quote, timeframe='daily'):
        """Get forex OHLC data from Finnhub"""
        try:
            # Calculate date range
            end_date = int(time.time())
            if timeframe == 'daily':
                start_date = end_date - (24 * 60 * 60)  # 1 day
                resolution = 'D'
            elif timeframe == 'weekly':
                start_date = end_date - (7 * 24 * 60 * 60)  # 1 week
                resolution = 'W'
            else:
                start_date = end_date - (30 * 24 * 60 * 60)  # 1 month
                resolution = 'M'
            
            url = f"{self.finnhub_base_url}/forex/candle"
            params = {
                'symbol': f"OANDA:{base.upper()}_{quote.upper()}",
                'resolution': resolution,
                'from': start_date,
                'to': end_date,
                'token': self.finnhub_api_key
            }
            response = requests.get(url, params=params)
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

    def get_forex_historical_rate(self, base, quote, date):
        """Get historical forex rate from Finnhub"""
        try:
            # Convert date to timestamp
            if isinstance(date, str):
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                timestamp = int(date_obj.timestamp())
            else:
                timestamp = int(date) if date else int((datetime.now() - timedelta(days=1)).timestamp())
            
            url = f"{self.finnhub_base_url}/forex/candle"
            params = {
                'symbol': f"OANDA:{base.upper()}_{quote.upper()}",
                'resolution': 'D',
                'from': timestamp - 86400,  # Start from day before
                'to': timestamp + 86400,    # End day after
                'token': self.finnhub_api_key
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('s') == 'ok' and len(data.get('c', [])) > 0:
                return {
                    'date': date,
                    'rate': data['c'][-1]  # Get the closing rate
                }
            
            return None
            
        except Exception as e:
            print(f"Error fetching forex historical rate: {e}")
            return None

    def get_forex_economic_data(self, country='US'):
        """Get economic data from Finnhub"""
        try:
            url = f"{self.finnhub_base_url}/calendar/economic"
            params = {
                'token': self.finnhub_api_key
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Filter by country if specified
            if country and 'economicCalendar' in data:
                filtered_data = []
                for event in data['economicCalendar']:
                    if event.get('country', '').upper() == country.upper():
                        filtered_data.append(event)
                return filtered_data[:10]  # Return top 10 events
            
            return data.get('economicCalendar', [])[:10]
            
        except Exception as e:
            print(f"Error fetching forex economic data: {e}")
            return None