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

 📊 MARKET OVERVIEW:
 - top_market_movers: When user asks for "top 5/10/20 cryptos/stocks/forex", "best performers", "biggest gainers", "top market cap", "list top assets"

 for the top_market_movers intent, extract the limit, for example if user asks for top 5 cryptos, then extract the '5' into the limit field.

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
    - "top 10 cryptocurrencies" → top_market_movers (crypto)
    - "top 5 stocks" → top_market_movers (stock)
    - "best forex pairs", "top currencies" → top_market_movers (forex)

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
 - CRITICAL: if the user message literally contains a ticker symbol (e.g. CJET, YAAS, AAPL, BTC), copy that exact ticker into asset_symbol and the corresponding name into asset_name; do NOT invent or swap to a different symbol.

 TIME-PERIOD RULE FOR CHARTS:
 - always return one of these exact strings: 1d, 7d, 30d, 90d, 1y
 - map "today|1 day|daily" → "1d"
 - map "last week|7 days|1 week" → "7d"
 - map "last month|30 days|1 month" → "30d"
 - map "last 90 days|3 months" → "90d"
 - map "last year|1 year|12 months" → "1y"
 - if none found, default to "30d"

 example:
 "show me a 1-day chart for bitcoin" → intent:"chart", asset_type:"crypto", time_period:"1d"

 USER QUERY: "{user_input}"

 Return ONLY this JSON:
 {{"intent": "intent_name", "asset_name": "name_if_found", "asset_symbol": "SYMBOL_IF_FOUND",  "asset_type": "crypto_or_stock_or_null", "base_currency": "BASE_IF_FOREX", "quote_currency": "QUOTE_IF_FOREX", "time_period": "period_if_chart", "timeframe": null, "date_range": null, "limit": "Number_or_null"}}

 Be precise. If someone asks "what is the price of bitcoin" they want DATA not education. Also tesla ohlc data is stock ohlc not crypto ohlc.

 Also extract timeframe for OHLC data for both crypto and stocks.
 for example: if user asks daily ohlc for btc, then here the timeframe is daily."""

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

    # ---- NEW TOP-MOVERS INTENT ----
    m = re.search(r'\b(?:top|list|best)\s+(\d{1,2})\b', user_lower)
    if m:
        digit = m.group(1)
        # decide asset_type from the rest of the sentence
        if 'crypto' in user_lower:
            at = 'crypto'
        elif 'stock' in user_lower:
            at = 'stock'
        elif 'forex' in user_lower or 'currency' in user_lower:
            at = 'forex'
        else:
            at = 'crypto'          # fallback
        return create_intent_response("top_market_movers",
                                    asset_type=at,
                                    limit=digit)       # <-- real home for the count 
    
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
        return create_intent_response(intent, symbol, symbol, asset_type, timeframe=time_period)
    
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
                         base_currency=None, quote_currency=None, time_period=None, timeframe=None, limit=None):
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
        "date_range": None,
        "limit":limit
    }