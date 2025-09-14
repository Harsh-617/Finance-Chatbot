# import requests
# import json
# import re
# import os
# from dotenv import load_dotenv

# load_dotenv()

# def analyze_user_input(user_input):
#     """Analyze user input using Groq's natural language understanding without rigid rules"""
#     groq_api_key = os.getenv('GROQ_API_KEY')
    
#     if not groq_api_key:
#         print("DEBUG - No Groq API key found, using fallback analysis")
#         return fallback_analysis(user_input)
    
#     groq_url = "https://api.groq.com/openai/v1/chat/completions"
    
#     headers = {
#         "Authorization": f"Bearer {groq_api_key}",
#         "Content-Type": "application/json"
#     }
    
#     prompt = f"""
#     You are an intelligent financial assistant with deep understanding of natural language and financial contexts. Your job is to understand what the user really wants, regardless of how they phrase it.

#     AVAILABLE INTENTS:

#     📚 EDUCATIONAL/EXPLANATORY:
#     - answer_financial_query: When user wants to understand, learn about, or get explanations of financial concepts, companies, assets, or how things work

#     💬 CONVERSATION:
#     - greeting_conversation: Basic greetings, small talk, casual conversation

#     📊 VISUALIZATION:
#     - chart: When user wants to see price charts, graphs, or visual data for stocks/crypto over time periods

#     🪙 CRYPTOCURRENCY DATA:
#     - crypto_price_overview: Current price, market cap, volume, price changes
#     - crypto_supply_info: Supply metrics (circulating, total, max supply)
#     - crypto_ath_atl: All-time high/low prices and dates
#     - crypto_ohlc: Open/High/Low/Close trading data
#     - crypto_exchange_info: Exchange listings and trading information
#     - crypto_metadata: Technical details, algorithms, blockchain specifications

#     📈 STOCK DATA:
#     - stock_price_overview: Current stock price, daily changes, trading info
#     - stock_fundamentals: Financial ratios, market cap, P/E, financial health
#     - stock_ohlc: Open/High/Low/Close trading data
#     - stock_earnings: Quarterly/annual earnings reports and results
#     - stock_analyst_ratings: Buy/sell recommendations from analysts
#     - stock_insider_ownership: Insider trading activities
#     - stock_technicals: Technical indicators like RSI, SMA

#     💱 FOREX DATA:
#     - forex_exchange_rate: Currency conversion rates
#     - forex_ohlc: Currency pair OHLC data
#     - forex_historical_rate: Historical exchange rates
#     - forex_economic_data: Economic events affecting currencies

#     UNDERSTANDING USER INTENT:

#     Think like a human financial advisor. When someone asks you something, consider:

#     1. CORE INTENT ANALYSIS:
#     - Are they trying to LEARN/UNDERSTAND something? → Educational (answer_financial_query)
#     - Are they trying to GET SPECIFIC DATA/NUMBERS? → Data request
#     - Are they trying to SEE VISUAL CHARTS/GRAPHS? → Chart request
#     - Are they just being social? → Conversation

#     2. CONTEXT UNDERSTANDING:
#     - What's the underlying need behind their question?
#     - What would be the most helpful response?
#     - What type of information would satisfy their query?

#     3. FLEXIBLE INTERPRETATION:
#     - Don't rely on exact phrases or keywords
#     - Understand meaning even with typos, slang, or unusual phrasing
#     - Consider multiple possible interpretations and choose the most likely

#     4. ENTITY EXTRACTION:
#     - Identify any financial instruments mentioned (stocks, cryptos, currencies)
#     - Handle abbreviations, full names, nicknames, or even misspellings
#     - Extract symbols, company names, currency codes flexibly
#     - For charts: identify time periods (1d, 7d, 30d, 90d, 1y) and asset type (crypto/stock)

#     5. TIME PERIOD EXTRACTION (VERY IMPORTANT):
#     - Look for time expressions like: "last 7 days", "past week", "1 week", "7d", "one week"
#     - Look for: "last 30 days", "past month", "1 month", "30d", "one month"
#     - Look for: "last 90 days", "3 months", "90d", "three months"  
#     - Look for: "last year", "1 year", "1y", "12 months"
#     - Look for: "today", "1 day", "1d", "daily"
#     - Map natural language to standard periods: 1d, 7d, 30d, 90d, 1y
#     - If no time period specified, default to 30d for charts

#     6. ASSET TYPE DETECTION:
#     - Crypto assets: BTC, Bitcoin, ETH, Ethereum, ADA, Cardano, SOL, Solana, DOGE, Dogecoin, etc.
#     - Stock assets: AAPL, Apple, TSLA, Tesla, MSFT, Microsoft, GOOGL, Google, AMZN, Amazon, etc.
#     - For charts, determine if mentioned asset is crypto or stock

#     7. CURRENCY EXTRACTION:
#     - For forex queries, extract base and quote currencies
#     - Handle phrases like "USD to EUR", "dollar to euro", "EUR/USD rate"
#     - Common currencies: USD, EUR, GBP, JPY, CAD, AUD, CHF, CNY, INR

#     USER QUERY: "{user_input}"

#     ANALYSIS APPROACH:
#     1. What is the user fundamentally asking for?
#     2. What would be the most helpful type of response?
#     3. Are they seeking knowledge/understanding OR specific current data OR visual charts?
#     4. What financial entities (if any) are they interested in?
#     5. For chart requests: what time period and asset type?
#     6. EXTRACT TIME PERIOD CAREFULLY - look for phrases like "last X days/weeks/months"
#     7. PRIORITIZE EDUCATIONAL INTENT for "what is", "explain", "tell me about" queries

#     RESPONSE STRATEGY:
#     - If unclear between educational vs data request, prefer educational (it's safer and more helpful)
#     - If you detect visual words (chart, graph, plot, show me), strongly consider chart intent
#     - If you detect a financial entity but unclear intent, consider what's most commonly asked about that entity
#     - For charts: determine if it's crypto or stock, extract time period if mentioned
#     - Don't overthink - trust your natural language understanding
#     - PAY SPECIAL ATTENTION to time expressions and map them correctly
#     - EDUCATIONAL QUERIES take priority over data queries

#     EXAMPLE THOUGHT PROCESS:
    
#     "what is bitcoin" → User wants to understand what Bitcoin is → answer_financial_query
#     "what's bitcoin" → User wants to learn about Bitcoin → answer_financial_query
#     "tell me about ethereum" → Educational request → answer_financial_query
#     "explain bitcoin" → Educational request → answer_financial_query
#     "bitcoin info" → Could be educational or data, but "info" suggests general information → answer_financial_query  
#     "bitcoin price" → User wants current price data → crypto_price_overview
#     "btc now" → "now" suggests current data → crypto_price_overview
#     "how's bitcoin doing" → Informal way of asking about performance → crypto_price_overview
#     "current price of bitcoin" → Clear price request → crypto_price_overview
#     "show me bitcoin chart" → User wants to see visual chart → chart (default: 30d, crypto)
#     "bitcoin chart last 7 days" → Chart request with specific timeframe → chart (7d, crypto)
#     "ethereum price chart 1 week" → Chart with timeframe → chart (7d, crypto)
#     "apple stock graph last 30 days" → Visual request for stock → chart (30d, stock)  
#     "tesla chart 90d" → Chart with specific timeframe → chart (90d, stock)
#     "btc 7d chart" → Chart with specific timeframe → chart (7d, crypto)
#     "show me apple stock for past month" → chart (30d, stock)
#     "bitcoin chart past week" → chart (7d, crypto)
#     "USD to EUR" → Currency conversion → forex_exchange_rate
#     "apple earnings" → Earnings data request → stock_earnings
#     "tesla fundamentals" → Financial metrics → stock_fundamentals

#     Return ONLY a valid JSON object with your best interpretation:
#     {{"intent": "most_appropriate_intent", "asset_name": "company_or_asset_name_if_any", "asset_symbol": "symbol_if_identified", "timeframe": null, "date_range": null, "base_currency": "base_currency_if_forex", "quote_currency": "quote_currency_if_forex", "time_period": "time_period_for_charts_if_chart_intent", "asset_type": "crypto_or_stock_for_charts_if_chart_intent"}}

#     Trust your understanding. Don't second-guess. Choose the intent that would provide the most helpful response to the user's actual need.
#     """
    
#     payload = {
#         "model": "llama-3.1-8b-instant",
#         "messages": [
#             {"role": "user", "content": prompt}
#         ],
#         "temperature": 0.1,
#         "max_tokens": 300
#     }
    
#     try:
#         response = requests.post(groq_url, headers=headers, json=payload, timeout=10)
#         response.raise_for_status()
        
#         content = response.json()['choices'][0]['message']['content'].strip()
#         print(f"DEBUG - Raw Groq response: {content}")
        
#         # Clean up the response
#         content = content.replace('```json', '').replace('```', '').strip()
        
#         # Try multiple JSON extraction methods for robust parsing
#         result = None
        
#         # Method 1: Direct JSON parse
#         try:
#             result = json.loads(content)
#             print(f"DEBUG - Method 1 success: {result}")
#         except json.JSONDecodeError as e:
#             print(f"DEBUG - Method 1 failed: {e}")
        
#         # Method 2: Find JSON object boundaries
#         if not result:
#             try:
#                 start_idx = content.find('{')
#                 end_idx = content.rfind('}') + 1
#                 if start_idx >= 0 and end_idx > start_idx:
#                     json_str = content[start_idx:end_idx]
#                     result = json.loads(json_str)
#                     print(f"DEBUG - Method 2 success: {result}")
#             except json.JSONDecodeError as e:
#                 print(f"DEBUG - Method 2 failed: {e}")
        
#         # Method 3: Regex extraction
#         if not result:
#             try:
#                 json_match = re.search(r'\{.*\}', content, re.DOTALL)
#                 if json_match:
#                     json_str = json_match.group()
#                     result = json.loads(json_str)
#                     print(f"DEBUG - Method 3 success: {result}")
#             except json.JSONDecodeError as e:
#                 print(f"DEBUG - Method 3 failed: {e}")
        
#         # Method 4: Line by line search for JSON
#         if not result:
#             try:
#                 lines = content.split('\n')
#                 for line in lines:
#                     line = line.strip()
#                     if line.startswith('{') and line.endswith('}'):
#                         result = json.loads(line)
#                         print(f"DEBUG - Method 4 success: {result}")
#                         break
#             except json.JSONDecodeError as e:
#                 print(f"DEBUG - Method 4 failed: {e}")
        
#         if result and isinstance(result, dict) and 'intent' in result:
#             print(f"DEBUG - Final parsed result: {result}")
#             return result
#         else:
#             print("DEBUG - All JSON parsing methods failed, using fallback")
#             return fallback_analysis(user_input)
        
#     except Exception as e:
#         print(f"DEBUG - Error with Groq API: {e}, using fallback analysis")
#         return fallback_analysis(user_input)


# def fallback_analysis(user_input):
#     """Enhanced fallback with better heuristics when LLM fails"""
#     user_lower = user_input.lower()
    
#     # Extract time period from input
#     time_period = "30d"  # default
#     if any(phrase in user_lower for phrase in ["last 7 days", "past 7 days", "7 days", "7d", "one week", "1 week", "past week", "last week"]):
#         time_period = "7d"
#     elif any(phrase in user_lower for phrase in ["last 30 days", "past 30 days", "30 days", "30d", "one month", "1 month", "past month", "last month"]):
#         time_period = "30d"
#     elif any(phrase in user_lower for phrase in ["last 90 days", "past 90 days", "90 days", "90d", "3 months", "three months"]):
#         time_period = "90d"
#     elif any(phrase in user_lower for phrase in ["last year", "past year", "1 year", "1y", "12 months"]):
#         time_period = "1y"
#     elif any(phrase in user_lower for phrase in ["today", "1 day", "1d", "daily"]):
#         time_period = "1d"
    
#     # Asset type detection
#     crypto_assets = ['btc', 'bitcoin', 'eth', 'ethereum', 'ada', 'cardano', 'sol', 'solana', 'doge', 'dogecoin', 'crypto', 'cryptocurrency']
#     stock_assets = ['aapl', 'apple', 'tsla', 'tesla', 'msft', 'microsoft', 'googl', 'google', 'amzn', 'amazon', 'stock', 'stocks']
    
#     detected_crypto = any(crypto in user_lower for crypto in crypto_assets)
#     detected_stock = any(stock in user_lower for stock in stock_assets)
    
#     # Asset mapping
#     asset_map = {
#         # Crypto
#         'bitcoin': {'symbol': 'BTC', 'type': 'crypto'},
#         'btc': {'symbol': 'BTC', 'type': 'crypto'},
#         'ethereum': {'symbol': 'ETH', 'type': 'crypto'},
#         'eth': {'symbol': 'ETH', 'type': 'crypto'},
#         'cardano': {'symbol': 'ADA', 'type': 'crypto'},
#         'ada': {'symbol': 'ADA', 'type': 'crypto'},
#         'solana': {'symbol': 'SOL', 'type': 'crypto'},
#         'sol': {'symbol': 'SOL', 'type': 'crypto'},
#         'dogecoin': {'symbol': 'DOGE', 'type': 'crypto'},
#         'doge': {'symbol': 'DOGE', 'type': 'crypto'},
        
#         # Stocks
#         'apple': {'symbol': 'AAPL', 'type': 'stock'},
#         'aapl': {'symbol': 'AAPL', 'type': 'stock'},
#         'tesla': {'symbol': 'TSLA', 'type': 'stock'},
#         'tsla': {'symbol': 'TSLA', 'type': 'stock'},
#         'microsoft': {'symbol': 'MSFT', 'type': 'stock'},
#         'msft': {'symbol': 'MSFT', 'type': 'stock'},
#         'google': {'symbol': 'GOOGL', 'type': 'stock'},
#         'googl': {'symbol': 'GOOGL', 'type': 'stock'},
#         'amazon': {'symbol': 'AMZN', 'type': 'stock'},
#         'amzn': {'symbol': 'AMZN', 'type': 'stock'}
#     }
    
#     # Find mentioned asset
#     mentioned_asset = None
#     for asset_name, asset_info in asset_map.items():
#         if asset_name in user_lower:
#             mentioned_asset = {
#                 'name': asset_name,
#                 'symbol': asset_info['symbol'],
#                 'type': asset_info['type']
#             }
#             break
    
#     # Currency extraction for forex
#     currencies = ['usd', 'eur', 'gbp', 'jpy', 'cad', 'aud', 'chf', 'cny', 'inr']
#     forex_patterns = [
#         r'(\w{3})\s+to\s+(\w{3})',  # USD to EUR
#         r'(\w{3})/(\w{3})',         # USD/EUR
#         r'(\w{3})-(\w{3})',         # USD-EUR
#     ]
    
#     base_currency = None
#     quote_currency = None
    
#     for pattern in forex_patterns:
#         match = re.search(pattern, user_lower)
#         if match:
#             base_currency = match.group(1).upper()
#             quote_currency = match.group(2).upper()
#             break
    
#     # Intent classification with priority rules
    
#     # 1. Educational queries (highest priority) - BUT exclude price queries
#     if any(phrase in user_lower for phrase in ['what is', 'what\'s', 'what are', 'explain', 'tell me about', 'how does', 'define', 'describe']):
#         # Check if this is actually a price query disguised as "what is"
#         if any(price_word in user_lower for price_word in ['price', 'current price', 'cost', 'worth', 'trading at']):
#             # This is a price query, not educational - continue to price logic below
#             pass
#         else:
#             # This is truly educational
#             return {
#                 "intent": "answer_financial_query",
#                 "asset_name": mentioned_asset['name'] if mentioned_asset else None,
#                 "asset_symbol": mentioned_asset['symbol'] if mentioned_asset else None,
#                 "timeframe": None,
#                 "date_range": None,
#                 "base_currency": None,
#                 "quote_currency": None,
#                 "time_period": None,
#                 "asset_type": None
#             }
    
#     # 2. Chart/visualization requests
#     elif any(word in user_lower for word in ['chart', 'graph', 'plot', 'show me', 'visualize']):
#         asset_type = mentioned_asset['type'] if mentioned_asset else ('crypto' if detected_crypto else ('stock' if detected_stock else None))
#         return {
#             "intent": "chart",
#             "asset_name": mentioned_asset['name'] if mentioned_asset else None,
#             "asset_symbol": mentioned_asset['symbol'] if mentioned_asset else None,
#             "timeframe": None,
#             "date_range": None,
#             "base_currency": None,
#             "quote_currency": None,
#             "time_period": time_period,
#             "asset_type": asset_type
#         }
    
#     # 3. Forex queries
#     elif base_currency and quote_currency:
#         if any(word in user_lower for word in ['rate', 'exchange', 'conversion', 'convert']):
#             return {
#                 "intent": "forex_exchange_rate",
#                 "asset_name": None,
#                 "asset_symbol": None,
#                 "timeframe": None,
#                 "date_range": None,
#                 "base_currency": base_currency,
#                 "quote_currency": quote_currency,
#                 "time_period": None,
#                 "asset_type": None
#             }
    
#     # 4. Specific data requests
#     elif mentioned_asset:
#         # Determine specific intent based on keywords
#         if any(word in user_lower for word in ['earnings', 'quarterly', 'annual', 'eps']):
#             return {
#                 "intent": "stock_earnings" if mentioned_asset['type'] == 'stock' else "answer_financial_query",
#                 "asset_name": mentioned_asset['name'],
#                 "asset_symbol": mentioned_asset['symbol'],
#                 "timeframe": None,
#                 "date_range": None,
#                 "base_currency": None,
#                 "quote_currency": None,
#                 "time_period": None,
#                 "asset_type": None
#             }
#         elif any(word in user_lower for word in ['fundamentals', 'ratios', 'pe ratio', 'market cap']):
#             return {
#                 "intent": "stock_fundamentals" if mentioned_asset['type'] == 'stock' else "answer_financial_query",
#                 "asset_name": mentioned_asset['name'],
#                 "asset_symbol": mentioned_asset['symbol'],
#                 "timeframe": None,
#                 "date_range": None,
#                 "base_currency": None,
#                 "quote_currency": None,
#                 "time_period": None,
#                 "asset_type": None
#             }
#         elif any(word in user_lower for word in ['supply', 'circulation', 'max supply', 'total supply']):
#             return {
#                 "intent": "crypto_supply_info" if mentioned_asset['type'] == 'crypto' else "answer_financial_query",
#                 "asset_name": mentioned_asset['name'],
#                 "asset_symbol": mentioned_asset['symbol'],
#                 "timeframe": None,
#                 "date_range": None,
#                 "base_currency": None,
#                 "quote_currency": None,
#                 "time_period": None,
#                 "asset_type": None
#             }
#         elif any(word in user_lower for word in ['ath', 'atl', 'all time high', 'all time low']):
#             return {
#                 "intent": "crypto_ath_atl" if mentioned_asset['type'] == 'crypto' else "answer_financial_query",
#                 "asset_name": mentioned_asset['name'],
#                 "asset_symbol": mentioned_asset['symbol'],
#                 "timeframe": None,
#                 "date_range": None,
#                 "base_currency": None,
#                 "quote_currency": None,
#                 "time_period": None,
#                 "asset_type": None
#             }
#         elif any(word in user_lower for word in ['price', 'current', 'now', 'today', 'latest', 'trading at', 'worth', 'cost']):
#             intent = "crypto_price_overview" if mentioned_asset['type'] == 'crypto' else "stock_price_overview"
#             return {
#                 "intent": intent,
#                 "asset_name": mentioned_asset['name'],
#                 "asset_symbol": mentioned_asset['symbol'],
#                 "timeframe": None,
#                 "date_range": None,
#                 "base_currency": None,
#                 "quote_currency": None,
#                 "time_period": None,
#                 "asset_type": None
#             }
#         else:
#             # General mention of asset without specific intent - default to educational
#             return {
#                 "intent": "answer_financial_query",
#                 "asset_name": mentioned_asset['name'],
#                 "asset_symbol": mentioned_asset['symbol'],
#                 "timeframe": None,
#                 "date_range": None,
#                 "base_currency": None,
#                 "quote_currency": None,
#                 "time_period": None,
#                 "asset_type": None
#             }
    
#     # 5. Greetings and conversation
#     elif any(greeting in user_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'how are you']):
#         return {
#             "intent": "greeting_conversation",
#             "asset_name": None,
#             "asset_symbol": None,
#             "timeframe": None,
#             "date_range": None,
#             "base_currency": None,
#             "quote_currency": None,
#             "time_period": None,
#             "asset_type": None
#         }
    
#     # 6. Default to educational/general query
#     else:
#         return {
#             "intent": "answer_financial_query",
#             "asset_name": None,
#             "asset_symbol": None,
#             "timeframe": None,
#             "date_range": None,
#             "base_currency": None,
#             "quote_currency": None,
#             "time_period": None,
#             "asset_type": None
#         }


import requests
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()

def analyze_user_input(user_input):
    """Analyze user input using LLM-first approach with smart fallback"""
    groq_api_key = os.getenv('GROQ_API_KEY')
    
    if not groq_api_key:
        print("DEBUG - No Groq API key found, using pattern fallback")
        return pattern_fallback_analysis(user_input)
    
    return llm_intent_analysis(user_input, groq_api_key)

def llm_intent_analysis(user_input, groq_api_key):
    """Primary LLM-based intent analysis"""
    groq_url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""You are a financial intent classifier. Analyze the user query and return ONLY a JSON object.

     AVAILABLE INTENTS:

     📚 EDUCATIONAL/EXPLANATORY:
     - answer_financial_query: When user wants to understand, learn about, or get explanations of financial concepts, companies, assets, or how things work

     💬 CONVERSATION:
     - greeting_conversation: Basic greetings, small talk, casual conversation

     📊 VISUALIZATION:
     - chart: When user wants to see price charts, graphs, or visual data for stocks/crypto over time periods

     🪙 CRYPTOCURRENCY DATA:
     - crypto_price_overview: Current price, market cap, volume, price changes
     - crypto_supply_info: Supply metrics (circulating, total, max supply)
     - crypto_ath_atl: All-time high/low prices and dates
     - crypto_ohlc: Open/High/Low/Close trading data
     - crypto_exchange_info: Exchange listings and trading information
     - crypto_metadata: Technical details, algorithms, blockchain specifications

     📈 STOCK DATA:
     - stock_price_overview: Current stock price, daily changes, trading info
     - stock_fundamentals: Financial ratios, market cap, P/E, financial health
     - stock_ohlc: Open/High/Low/Close trading data
     - stock_earnings: Quarterly/annual earnings reports and results
     - stock_analyst_ratings: Buy/sell recommendations from analysts
     - stock_insider_ownership: Insider trading activities
     - stock_technicals: Technical indicators like RSI, SMA

     💱 FOREX DATA:
     - forex_exchange_rate: Currency conversion rates
     - forex_ohlc: Currency pair OHLC data
     - forex_historical_rate: Historical exchange rates
     - forex_economic_data: Economic events affecting currencies

carefully read each and every word of the user query and then decide which intent best suites the query.
for example, if there are words like what, how, explain, etc then most probably it is related to the intent answer_financial_query.
if price or rate or other similar words like this then most probably its related to the other crypto, stocks, or forex intents. 

INTENT RULES:
1. DATA REQUESTS (user wants current/specific numbers):
   - "bitcoin price", "price of bitcoin" → crypto_price_overview
   - "apple stock price", "aapl price" → stock_price_overview  
   - "tesla earnings", "aapl quarterly results" → stock_earnings
   - "apple fundamentals", "msft pe ratio" → stock_fundamentals
   - "bitcoin ohlc" → crypto_ohlc
   - "tesla ohlc data" → stock_ohlc
   - "usd to eur", "dollar euro rate" → forex_exchange_rate

2. VISUAL REQUESTS (user wants charts/graphs):
   - "bitcoin chart", "show me apple graph" → chart

3. EDUCATIONAL (user wants to learn/understand):
   - "what is bitcoin", "explain blockchain", "whats btc" → answer_financial_query

4. CONVERSATION:
   - "hello", "how are you" → greeting_conversation

ENTITY EXTRACTION:
- Extract ANY symbol/name mentioned (BTC, Bitcoin, AAPL, Apple, Tesla, EUR, USD, etc.)
- Determine if it's crypto, stock, or currency based on context
- For time periods: extract "7d", "30d", "1 week", "last month" etc.

USER QUERY: "{user_input}"

Return ONLY this JSON:
{{"intent": "intent_name", "asset_name": "name_if_found", "asset_symbol": "SYMBOL_IF_FOUND",  "asset_type": "crypto_or_stock_or_null", "base_currency": "BASE_IF_FOREX", "quote_currency": "QUOTE_IF_FOREX", "time_period": "period_if_chart", "timeframe": null, "date_range": null}}

Be precise. If someone asks "what is the price of bitcoin" they want DATA not education. Also tesla ohlc data is stock ohlc not crypto ohlc."""

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 200
    }
    
    try:
        response = requests.post(groq_url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        content = response.json()['choices'][0]['message']['content'].strip()
        print(f"DEBUG - LLM response: {content}")
        
        # Clean and parse JSON
        content = content.replace('```json', '').replace('```', '').strip()
        
        # Try to find JSON object
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            result = json.loads(json_str)
            
            # Validate result
            if isinstance(result, dict) and 'intent' in result:
                print(f"DEBUG - Parsed LLM result: {result}")
                return result
        
        print("DEBUG - Failed to parse LLM response, using fallback")
        return pattern_fallback_analysis(user_input)
        
    except Exception as e:
        print(f"DEBUG - LLM error: {e}, using fallback")
        return pattern_fallback_analysis(user_input)

def pattern_fallback_analysis(user_input):
    """Pattern-based fallback when LLM fails"""
    user_lower = user_input.lower().strip()
    
    # Basic greeting detection
    greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
    if any(greeting in user_lower for greeting in greetings):
        return create_intent_response("greeting_conversation")
    
    # Extract potential symbols/names using regex
    # Look for 2-5 letter sequences that could be symbols
    potential_symbols = re.findall(r'\b[A-Z]{2,5}\b', user_input.upper())
    potential_symbols.extend(re.findall(r'\b(?:bitcoin|ethereum|apple|tesla|microsoft|google|amazon)\b', user_lower))
    
    # Extract time periods
    time_period = "30d"  # default
    time_patterns = {
        r'\b(?:7d|7\s*days?|one\s*week|1\s*week|week)\b': "7d",
        r'\b(?:30d|30\s*days?|one\s*month|1\s*month|month)\b': "30d", 
        r'\b(?:90d|90\s*days?|3\s*months?|three\s*months?)\b': "90d",
        r'\b(?:1y|1\s*year|one\s*year|year)\b': "1y",
        r'\b(?:1d|1\s*day|today|daily)\b': "1d"
    }
    
    for pattern, period in time_patterns.items():
        if re.search(pattern, user_lower):
            time_period = period
            break
    
    # Chart/visualization requests
    if re.search(r'\b(?:chart|graph|plot|show\s+me|visualize)\b', user_lower):
        symbol = potential_symbols[0] if potential_symbols else None
        asset_type = guess_asset_type(symbol, user_lower) if symbol else None
        return create_intent_response("chart", symbol, symbol, asset_type, time_period=time_period)
    
    # Crypto-specific intents
    elif re.search(r'\b(?:supply|circulation|max\s*supply|total\s*supply)\b', user_lower):
        symbol = potential_symbols[0] if potential_symbols else None
        if guess_asset_type(symbol, user_lower) == "crypto":
            return create_intent_response("crypto_supply_info", symbol, symbol, "crypto")
    
    elif re.search(r'\b(?:ath|atl|all\s*time\s*high|all\s*time\s*low)\b', user_lower):
        symbol = potential_symbols[0] if potential_symbols else None
        if guess_asset_type(symbol, user_lower) == "crypto":
            return create_intent_response("crypto_ath_atl", symbol, symbol, "crypto")
    
    elif re.search(r'\b(?:exchange|exchanges|trading\s*pairs?|where\s*to\s*buy)\b', user_lower):
        symbol = potential_symbols[0] if potential_symbols else None
        if guess_asset_type(symbol, user_lower) == "crypto":
            return create_intent_response("crypto_exchange_info", symbol, symbol, "crypto")
    
    elif re.search(r'\b(?:metadata|algorithm|proof\s*type|blockchain\s*info)\b', user_lower):
        symbol = potential_symbols[0] if potential_symbols else None
        if guess_asset_type(symbol, user_lower) == "crypto":
            return create_intent_response("crypto_metadata", symbol, symbol, "crypto")
    
    # Stock-specific intents
    elif re.search(r'\b(?:earnings|quarterly|eps|annual\s*report)\b', user_lower):
        symbol = potential_symbols[0] if potential_symbols else None
        return create_intent_response("stock_earnings", symbol, symbol, "stock")
    
    elif re.search(r'\b(?:fundamentals|ratios|pe\s*ratio|market\s*cap|financial\s*health)\b', user_lower):
        symbol = potential_symbols[0] if potential_symbols else None
        return create_intent_response("stock_fundamentals", symbol, symbol, "stock")
    
    elif re.search(r'\b(?:analyst|ratings?|recommendations?|buy|sell|hold)\b', user_lower):
        symbol = potential_symbols[0] if potential_symbols else None
        return create_intent_response("stock_analyst_ratings", symbol, symbol, "stock")
    
    elif re.search(r'\b(?:insider|insider\s*trading|insider\s*ownership)\b', user_lower):
        symbol = potential_symbols[0] if potential_symbols else None
        return create_intent_response("stock_insider_ownership", symbol, symbol, "stock")
    
    elif re.search(r'\b(?:technical|technicals|rsi|sma|indicators?)\b', user_lower):
        symbol = potential_symbols[0] if potential_symbols else None
        return create_intent_response("stock_technicals", symbol, symbol, "stock")
    
    # OHLC requests (works for both crypto and stocks)
    elif re.search(r'\bohlc\b', user_lower):
        symbol = potential_symbols[0] if potential_symbols else None
        asset_type = guess_asset_type(symbol, user_lower) if symbol else None
        intent = "crypto_ohlc" if asset_type == "crypto" else "stock_ohlc"
        return create_intent_response(intent, symbol, symbol, asset_type, timeframe="daily")
    
    # General price requests
    elif re.search(r'\b(?:price|current|now|today|cost|worth|trading)\b', user_lower):
        symbol = potential_symbols[0] if potential_symbols else None
        asset_type = guess_asset_type(symbol, user_lower) if symbol else None
        
        if asset_type == "crypto":
            return create_intent_response("crypto_price_overview", symbol, symbol, asset_type)
        elif asset_type == "stock":
            return create_intent_response("stock_price_overview", symbol, symbol, asset_type)
    
    # Forex detection
    forex_match = re.search(r'\b([A-Z]{3})\s*(?:to|/|-)\s*([A-Z]{3})\b', user_input.upper())
    if forex_match:
        base, quote = forex_match.groups()
        
        if re.search(r'\bohlc\b', user_lower):
            return create_intent_response("forex_ohlc", base_currency=base, quote_currency=quote, timeframe="daily")
        elif re.search(r'\b(?:historical|history|past)\b', user_lower):
            return create_intent_response("forex_historical_rate", base_currency=base, quote_currency=quote)
        else:
            return create_intent_response("forex_exchange_rate", base_currency=base, quote_currency=quote)
    
    elif re.search(r'\b(?:economic\s*data|economic\s*events|economic\s*calendar)\b', user_lower):
        return create_intent_response("forex_economic_data")
    
    # Educational queries
    elif re.search(r'\b(?:what\s+is|explain|tell\s+me\s+about|how\s+does|define)\b', user_lower):
        # Check if it's actually a price question disguised as educational
        if not re.search(r'\b(?:price|current|cost|worth)\b', user_lower):
            symbol = potential_symbols[0] if potential_symbols else None
            return create_intent_response("answer_financial_query", symbol, symbol)
    
    # Default to educational for unrecognized queries
    symbol = potential_symbols[0] if potential_symbols else None
    return create_intent_response("answer_financial_query", symbol, symbol)

def guess_asset_type(symbol, user_input):
    """Guess if symbol is crypto or stock based on context"""
    if not symbol:
        return None
    
    symbol_lower = symbol.lower()
    user_lower = user_input.lower()
    
    # Crypto indicators
    crypto_keywords = ['crypto', 'cryptocurrency', 'bitcoin', 'ethereum', 'coin', 'token']
    crypto_common = ['btc', 'eth', 'ada', 'sol', 'doge', 'ltc', 'xrp', 'bnb']
    
    # Stock indicators  
    stock_keywords = ['stock', 'share', 'equity', 'company', 'corporation']
    stock_common = ['aapl', 'tsla', 'msft', 'googl', 'amzn', 'nvda', 'meta']
    
    # Check context keywords
    if any(keyword in user_lower for keyword in crypto_keywords):
        return "crypto"
    elif any(keyword in user_lower for keyword in stock_keywords):
        return "stock"
    
    # Check common symbols
    if symbol_lower in crypto_common:
        return "crypto"
    elif symbol_lower in stock_common:
        return "stock"
    
    # Default based on symbol characteristics
    # Most 3-letter symbols are crypto, 4+ letters often stocks
    if len(symbol) == 3:
        return "crypto"
    elif len(symbol) >= 4:
        return "stock"
    
    return None

def create_intent_response(intent, asset_symbol=None, asset_name=None, asset_type=None, 
                         base_currency=None, quote_currency=None, time_period=None, timeframe=None):
    """Create standardized intent response"""
    return {
        "intent": intent,
        "asset_symbol": asset_symbol,
        "asset_name": asset_name, 
        "asset_type": asset_type,
        "base_currency": base_currency,
        "quote_currency": quote_currency,
        "time_period": time_period,
        "timeframe": timeframe,
        "date_range": None
    }