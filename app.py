from flask import Flask, request, jsonify, render_template
import os
import json
import requests
import re
from dotenv import load_dotenv
from data_fetcher import DataFetcher

# Load environment variables
load_dotenv()

app = Flask(__name__)
data_fetcher = DataFetcher()

class ChatBot:
    def __init__(self):
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
    

    def analyze_user_input(self, user_input):
        """Analyze user input using Groq's natural language understanding without rigid rules"""
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""
        You are an intelligent financial assistant with deep understanding of natural language and financial contexts. Your job is to understand what the user really wants, regardless of how they phrase it.

        AVAILABLE INTENTS:

        📚 EDUCATIONAL/EXPLANATORY:
        - answer_financial_query: When user wants to understand, learn about, or get explanations of financial concepts, companies, assets, or how things work

        🗣️ CONVERSATION:
        - greeting_conversation: Basic greetings, small talk, casual conversation

        💎 CRYPTOCURRENCY DATA:
        - crypto_price_overview: Current price, market cap, volume, price changes
        - crypto_supply_info: Supply metrics (circulating, total, max supply)
        - crypto_ath_atl: All-time high/low prices and dates
        - crypto_ohlc: Open/High/Low/Close trading data
        - crypto_exchange_info: Exchange listings and trading information
        - crypto_metadata: Technical details, algorithms, blockchain specifications

        📊 STOCK DATA:
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

        UNDERSTANDING USER INTENT:

        Think like a human financial advisor. When someone asks you something, consider:

        1. CORE INTENT ANALYSIS:
        - Are they trying to LEARN/UNDERSTAND something? → Educational
        - Are they trying to GET SPECIFIC DATA/NUMBERS? → Data request
        - Are they just being social? → Conversation

        2. CONTEXT UNDERSTANDING:
        - What's the underlying need behind their question?
        - What would be the most helpful response?
        - What type of information would satisfy their query?

        3. FLEXIBLE INTERPRETATION:
        - Don't rely on exact phrases or keywords
        - Understand meaning even with typos, slang, or unusual phrasing
        - Consider multiple possible interpretations and choose the most likely

        4. ENTITY EXTRACTION:
        - Identify any financial instruments mentioned (stocks, cryptos, currencies)
        - Handle abbreviations, full names, nicknames, or even misspellings
        - Extract symbols, company names, currency codes flexibly

        USER QUERY: "{user_input}"

        ANALYSIS APPROACH:
        1. What is the user fundamentally asking for?
        2. What would be the most helpful type of response?
        3. Are they seeking knowledge/understanding OR specific current data?
        4. What financial entities (if any) are they interested in?

        RESPONSE STRATEGY:
        - If unclear between educational vs data request, prefer educational (it's safer and more helpful)
        - If you detect a financial entity but unclear intent, consider what's most commonly asked about that entity
        - Don't overthink - trust your natural language understanding

        EXAMPLE THOUGHT PROCESS:
        
        "what is btc" → User wants to understand what BTC is → answer_financial_query
        "btc info" → Could be educational or data, but "info" suggests general information → answer_financial_query  
        "btc now" → "now" suggests current data → crypto_price_overview
        "how's bitcoin doing" → Informal way of asking about performance → crypto_price_overview
        "tell me about tesla" → "about" suggests educational → answer_financial_query
        "tesla numbers" → "numbers" suggests data → stock_fundamentals or stock_price_overview
        "usd eur" → Two currencies mentioned → forex_exchange_rate
        "apple quarterly results" → Specific request for earnings → stock_earnings

        Return ONLY a valid JSON object with your best interpretation:
        {{"intent": "most_appropriate_intent", "asset_name": "company_or_asset_name_if_any", "asset_symbol": "symbol_if_identified", "timeframe": null, "date_range": null, "base_currency": "base_currency_if_forex", "quote_currency": "quote_currency_if_forex"}}

        Trust your understanding. Don't second-guess. Choose the intent that would provide the most helpful response to the user's actual need.
        """
        
        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,  # Slightly higher for more natural interpretation
            "max_tokens": 300
        }
        
        try:
            response = requests.post(self.groq_url, headers=headers, json=payload)
            response.raise_for_status()
            
            content = response.json()['choices'][0]['message']['content'].strip()
            print(f"DEBUG - Raw Groq response: {content}")
            
            # Clean up the response
            content = content.replace('```json', '').replace('```', '').strip()
            
            # Find and extract JSON
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                result = json.loads(json_str)
                print(f"DEBUG - Parsed result: {result}")
                return result
            else:
                raise ValueError("No valid JSON found")
            
        except Exception as e:
            print(f"Error analyzing user input: {e}")
            # Intelligent fallback - try to determine if it's likely educational or data request
            user_lower = user_input.lower()
            
            # Simple heuristics for fallback
            if any(word in user_lower for word in ['what', 'how', 'why', 'explain', 'tell me about', 'define']):
                intent = "answer_financial_query"
            elif any(word in user_lower for word in ['price', 'current', 'now', 'today', 'latest', 'show']):
                # Try to determine asset type for data request
                if any(crypto in user_lower for crypto in ['btc', 'bitcoin', 'eth', 'ethereum', 'crypto']):
                    intent = "crypto_price_overview"
                elif any(stock in user_lower for stock in ['aapl', 'apple', 'tsla', 'tesla', 'stock']):
                    intent = "stock_price_overview"
                else:
                    intent = "answer_financial_query"
            elif any(greeting in user_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good evening']):
                intent = "greeting_conversation"
            else:
                intent = "answer_financial_query"
            
            return {
                "intent": intent,
                "asset_name": None,
                "asset_symbol": None,
                "timeframe": None,
                "date_range": None,
                "base_currency": None,
                "quote_currency": None
            }

    
    def answer_financial_query(self, user_input):
        """Answer general financial questions using Groq"""
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""
        You are a knowledgeable financial advisor AI with expertise in stocks, cryptocurrency, forex, and financial markets. 
        Answer the user's financial question clearly and comprehensively.
        
        Guidelines:
        - Provide accurate, educational explanations of financial concepts
        - Use simple language but maintain professional accuracy
        - If the question requires real-time data, suggest specific queries they can ask
        - Draw from your knowledge of financial markets, trading, investment principles, and economic concepts
        - Be helpful and informative without being overly technical

        User question: {user_input}
        """
        
        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(self.groq_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            return f"I apologize, but I'm having trouble processing your financial query right now. Error: {e}"
    
    def handle_greetings_conversation(self, user_input):
        """Handle greetings and general conversation using Groq"""
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""
        You are a friendly financial chatbot assistant. Respond to this greeting/conversation in a warm, 
        professional way. Keep it brief and guide the conversation toward how you can help with financial 
        information like stock prices, crypto data, forex rates, etc.

        User message: {user_input}
        """
        
        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8,
            "max_tokens": 200
        }
        
        try:
            response = requests.post(self.groq_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            return "Hello! I'm your financial assistant. I can help you with stock prices, crypto data, forex rates, and financial questions. How can I assist you today?"

chatbot = ChatBot()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')
    
    if not user_input:
        return jsonify({'response': 'Please provide a message.'})
    
    # Analyze user input to extract intent and parameters
    analysis = chatbot.analyze_user_input(user_input)
    intent = analysis.get('intent')
    
    print(f"DEBUG - Final intent: {intent}")
    print(f"DEBUG - Full analysis: {analysis}")
    
    try:
        if intent == 'greeting_conversation':
            response = chatbot.handle_greetings_conversation(user_input)
            
        elif intent == 'answer_financial_query':
            response = chatbot.answer_financial_query(user_input)
            
        elif intent == 'crypto_price_overview':
            symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
            if symbol:
                symbol = symbol.upper()
                print(f"DEBUG - Fetching crypto data for: {symbol}")
                data = data_fetcher.get_crypto_price_overview(symbol)
                print(f"DEBUG - Crypto data received: {data}")
                response = format_crypto_price_response(data, symbol)
            else:
                response = "Please specify which cryptocurrency you'd like to know about."
                
        elif intent == 'crypto_supply_info':
            symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
            if symbol:
                # Keep original case for CoinGecko API
                print(f"DEBUG - Fetching crypto supply for: {symbol}")
                data = data_fetcher.get_crypto_supply_info(symbol)
                print(f"DEBUG - Supply data received: {data}")
                response = format_crypto_supply_response(data, symbol)
            else:
                response = "Please specify which cryptocurrency's supply information you'd like to know."
                
        elif intent == 'crypto_ath_atl':
            symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
            if symbol:
                data = data_fetcher.get_crypto_ath_atl(symbol)
                response = format_crypto_ath_atl_response(data, symbol)
            else:
                response = "Please specify which cryptocurrency's ATH/ATL you'd like to know."
                
        elif intent == 'crypto_ohlc':
            symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
            timeframe = analysis.get('timeframe', 'daily')
            if symbol:
                symbol = symbol.upper()
                data = data_fetcher.get_crypto_ohlc(symbol, timeframe)
                response = format_crypto_ohlc_response(data, symbol, timeframe)
            else:
                response = "Please specify which cryptocurrency's OHLC data you'd like to see."
                
        elif intent == 'crypto_exchange_info':
            symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
            if symbol:
                symbol = symbol.upper()
                data = data_fetcher.get_crypto_exchange_info(symbol)
                response = format_crypto_exchange_response(data, symbol)
            else:
                response = "Please specify which cryptocurrency's exchange information you'd like to see."
                
        elif intent == 'crypto_metadata':
            symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
            if symbol:
                symbol = symbol.upper()
                data = data_fetcher.get_crypto_metadata(symbol)
                response = format_crypto_metadata_response(data, symbol)
            else:
                response = "Please specify which cryptocurrency's information you'd like to see."
                
        elif intent == 'stock_price_overview':
            symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
            if symbol:
                symbol = symbol.upper()
                data = data_fetcher.get_stock_price_overview(symbol)
                response = format_stock_price_response(data, symbol)
            else:
                response = "Please specify which stock you'd like to know about."
                
        elif intent == 'stock_fundamentals':
            symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
            if symbol:
                symbol = symbol.upper()
                data = data_fetcher.get_stock_fundamentals(symbol)
                response = format_stock_fundamentals_response(data, symbol)
            else:
                response = "Please specify which stock's fundamentals you'd like to see."
                
        elif intent == 'stock_earnings':
            symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
            if symbol:
                symbol = symbol.upper()
                print(f"DEBUG - Fetching earnings for: {symbol}")
                data = data_fetcher.get_stock_earnings(symbol)
                print(f"DEBUG - Earnings data received: {data}")
                response = format_stock_earnings_response(data, symbol)
            else:
                response = "Please specify which stock's earnings you'd like to see."
                
        elif intent == 'stock_analyst_ratings':
            symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
            if symbol:
                symbol = symbol.upper()
                data = data_fetcher.get_stock_analyst_ratings(symbol)
                response = format_stock_ratings_response(data, symbol)
            else:
                response = "Please specify which stock's analyst ratings you'd like to see."
                
        elif intent == 'stock_insider_ownership':
            symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
            if symbol:
                symbol = symbol.upper()
                data = data_fetcher.get_stock_insider_ownership(symbol)
                response = format_stock_insider_response(data, symbol)
            else:
                response = "Please specify which stock's insider data you'd like to see."
                
        elif intent == 'stock_technicals':
            symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
            if symbol:
                symbol = symbol.upper()
                data = data_fetcher.get_stock_technicals(symbol)
                response = format_stock_technicals_response(data, symbol)
            else:
                response = "Please specify which stock's technical indicators you'd like to see."
                
        elif intent == 'stock_ohlc':
            symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
            timeframe = analysis.get('timeframe', 'daily')
            if symbol:
                symbol = symbol.upper()
                data = data_fetcher.get_stock_ohlc(symbol, timeframe)
                response = format_stock_ohlc_response(data, symbol, timeframe)
            else:
                response = "Please specify which stock's OHLC data you'd like to see."
                
        elif intent == 'forex_exchange_rate':
            base = analysis.get('base_currency')
            quote = analysis.get('quote_currency')
            
            # Handle common variations
            if base and quote:
                base = base.upper()
                quote = quote.upper()
                print(f"DEBUG - Fetching forex rate for {base}/{quote}")
                data = data_fetcher.get_forex_exchange_rate(base, quote)
                print(f"DEBUG - Forex data received: {data}")
                response = format_forex_rate_response(data, base, quote)
            else:
                response = "Please specify the currency pair (e.g., EUR to USD, dollar to INR)."
                
        elif intent == 'forex_ohlc':
            base = analysis.get('base_currency')
            quote = analysis.get('quote_currency')
            timeframe = analysis.get('timeframe', 'daily')
            if base and quote:
                base = base.upper()
                quote = quote.upper()
                data = data_fetcher.get_forex_ohlc(base, quote, timeframe)
                response = format_forex_ohlc_response(data, base, quote, timeframe)
            else:
                response = "Please specify the currency pair for OHLC data."
                
        elif intent == 'forex_historical_rate':
            base = analysis.get('base_currency')
            quote = analysis.get('quote_currency')
            date = analysis.get('date_range')
            if base and quote:
                base = base.upper()
                quote = quote.upper()
                data = data_fetcher.get_forex_historical_rate(base, quote, date)
                response = format_forex_historical_response(data, base, quote)
            else:
                response = "Please specify the currency pair and date for historical rates."
                
        elif intent == 'forex_economic_data':
            data = data_fetcher.get_forex_economic_data()
            response = format_economic_data_response(data)
            
        else:
            response = "I understand you're asking about financial data, but I need more specific information. Try asking about stock prices, crypto data, or forex rates."
            
    except Exception as e:
        print(f"DEBUG - Error in chat route: {e}")
        response = f"I apologize, but I encountered an error while processing your request: {str(e)}"
    
    return jsonify({'response': response})

# Response formatting functions
def format_crypto_price_response(data, symbol):
    if not data:
        return f"Sorry, I couldn't fetch price data for {symbol.upper()}."
    
    # Format numbers properly
    def format_currency(value):
        if value is None:
            return 'N/A'
        try:
            if value >= 1e9:
                return f"${value/1e9:.2f}B"
            elif value >= 1e6:
                return f"${value/1e6:.2f}M"
            else:
                return f"${value:,.2f}"
        except:
            return str(value)
    
    def format_percentage(value):
        if value is None:
            return 'N/A'
        try:
            return f"{value:+.2f}%"
        except:
            return str(value)
    
    return f"""💰 **{symbol.upper()} Price Overview**

Current Price: {format_currency(data.get('price'))}
24h Change: {format_percentage(data.get('percent_change_24h'))}
7d Change: {format_percentage(data.get('percent_change_7d'))}
Market Cap: {format_currency(data.get('market_cap_usd'))}
24h Volume: {format_currency(data.get('volume_24h_usd'))}
"""

def format_crypto_supply_response(data, symbol):
    if not data:
        return f"Sorry, I couldn't fetch supply data for {symbol.upper()}."
    
    def format_supply_number(num):
        if num is None:
            return 'N/A'
        try:
            if num >= 1e9:
                return f"{num/1e9:.2f}B"
            elif num >= 1e6:
                return f"{num/1e6:.2f}M"
            elif num >= 1e3:
                return f"{num/1e3:.2f}K"
            else:
                return f"{num:,.0f}"
        except:
            return str(num)
    
    return f"""📊 **{symbol.upper()} Supply Information**

Circulating Supply: {format_supply_number(data.get('circulating_supply'))}
Total Supply: {format_supply_number(data.get('total_supply'))}
Max Supply: {format_supply_number(data.get('max_supply')) if data.get('max_supply') else 'Unlimited'}
"""

def format_crypto_metadata_response(data, symbol):
    if not data:
        return f"Sorry, I couldn't fetch metadata for {symbol.upper()}."
    
    return f"""ℹ️ **{symbol.upper()} Information**

Name: {data.get('name', 'N/A')}
Full Name: {data.get('full_name', 'N/A')}
Algorithm: {data.get('algorithm', 'N/A')}
Proof Type: {data.get('proof_type', 'N/A')}
Description: {data.get('description', 'No description available')[:200]}...
"""

def format_crypto_exchange_response(data, symbol):
    if not data:
        return f"Sorry, I couldn't fetch exchange data for {symbol.upper()}."
    
    response = f"🏦 **{symbol.upper()} Top Exchanges**\n\n"
    for i, exchange in enumerate(data[:5], 1):
        response += f"{i}. **{exchange.get('exchange_name', 'N/A')}**\n"
        response += f"   Price: ${exchange.get('price', 'N/A')}\n"
        response += f"   24h Volume: {exchange.get('volume_24h', 'N/A')}\n\n"
    
    return response

def format_crypto_ath_atl_response(data, symbol):
    if not data:
        return f"Sorry, I couldn't fetch ATH/ATL data for {symbol.upper()}."
    
    return f"""🏔️ **{symbol.upper()} All-Time High/Low**

ATH Price: ${data.get('ath', 'N/A')}
ATH Date: {data.get('ath_date', 'N/A')}
ATL Price: ${data.get('atl', 'N/A')}
ATL Date: {data.get('atl_date', 'N/A')}
"""

def format_crypto_ohlc_response(data, symbol, timeframe):
    if not data:
        return f"Sorry, I couldn't fetch OHLC data for {symbol.upper()}."
    
    return f"""📈 **{symbol.upper()} OHLC Data ({timeframe})**

Open: ${data.get('open', 'N/A')}
High: ${data.get('high', 'N/A')}
Low: ${data.get('low', 'N/A')}
Close: ${data.get('close', 'N/A')}
"""

def format_stock_price_response(data, symbol):
    if not data:
        return f"Sorry, I couldn't fetch price data for {symbol.upper()}."
    
    def format_percentage(value):
        if value is None:
            return 'N/A'
        try:
            return f"{value:+.2f}%"
        except:
            return str(value)
    
    return f"""📈 **{symbol.upper()} Stock Overview**

Current Price: ${data.get('c', 'N/A')}
Daily Change: {format_percentage(data.get('dp'))}
High: ${data.get('h', 'N/A')}
Low: ${data.get('l', 'N/A')}
Previous Close: ${data.get('pc', 'N/A')}
"""

def format_stock_fundamentals_response(data, symbol):
    if not data:
        return f"Sorry, I couldn't fetch fundamental data for {symbol.upper()}."
    
    def format_large_number(num):
        if num is None:
            return 'N/A'
        try:
            if num >= 1e12:
                return f"${num/1e12:.2f}T"
            elif num >= 1e9:
                return f"${num/1e9:.2f}B"
            elif num >= 1e6:
                return f"${num/1e6:.2f}M"
            else:
                return f"${num:,.0f}"
        except:
            return str(num)
    
    return f"""📊 **{symbol.upper()} Fundamentals**

Market Cap: {format_large_number(data.get('marketCapitalization'))}
P/E Ratio: {data.get('peBasicExclExtraTTM', 'N/A')}
EPS: ${data.get('epsInclExtraItemsTTM', 'N/A')}
Beta: {data.get('beta', 'N/A')}
"""

def format_stock_earnings_response(data, symbol):
    if not data or len(data) == 0:
        return f"Sorry, I couldn't fetch earnings data for {symbol.upper()}."
    
    response = f"💼 **{symbol.upper()} Recent Earnings**\n\n"
    
    # Sort by period to get most recent first
    sorted_earnings = sorted(data, key=lambda x: x.get('period', ''), reverse=True)
    
    for i, earning in enumerate(sorted_earnings[:4], 1):
        period = earning.get('period', 'N/A')
        actual = earning.get('actual', 'N/A')
        estimate = earning.get('estimate', 'N/A')
        
        # Try to determine quarter from period
        quarter = f"Period {i}"
        if isinstance(period, str) and period != 'N/A':
            if '2024-12-31' in period or '2024-Q4' in period:
                quarter = "Q4 2024"
            elif '2024-09-30' in period or '2024-Q3' in period:
                quarter = "Q3 2024"
            elif '2024-06-30' in period or '2024-Q2' in period:
                quarter = "Q2 2024"
            elif '2024-03-31' in period or '2024-Q1' in period:
                quarter = "Q1 2024"
        
        response += f"**{quarter}:**\n"
        response += f"Actual EPS: ${actual}\n"
        response += f"Estimate EPS: ${estimate}\n"
        response += f"Period: {period}\n\n"
    
    return response

def format_stock_ratings_response(data, symbol):
    if not data:
        return f"Sorry, I couldn't fetch analyst ratings for {symbol.upper()}."
    
    return f"""🎯 **{symbol.upper()} Analyst Ratings**

Strong Buy: {data.get('strongBuy', 'N/A')}
Buy: {data.get('buy', 'N/A')}
Hold: {data.get('hold', 'N/A')}
Sell: {data.get('sell', 'N/A')}
Strong Sell: {data.get('strongSell', 'N/A')}
"""

def format_stock_insider_response(data, symbol):
    if not data:
        return f"Sorry, I couldn't fetch insider data for {symbol.upper()}."
    
    response = f"🔍 **{symbol.upper()} Recent Insider Transactions**\n\n"
    for i, transaction in enumerate(data[:3], 1):
        response += f"{i}. **{transaction.get('name', 'N/A')}**\n"
        response += f"   Shares: {transaction.get('share', 'N/A')}\n"
        response += f"   Transaction: {transaction.get('transactionCode', 'N/A')}\n\n"
    
    return response

def format_stock_technicals_response(data, symbol):
    if not data:
        return f"Sorry, I couldn't fetch technical data for {symbol.upper()}."
    
    return f"""📊 **{symbol.upper()} Technical Indicators**

RSI (14): {data.get('rsi', 'N/A')}
SMA (20): {data.get('sma_20', 'N/A')}
"""

def format_stock_ohlc_response(data, symbol, timeframe):
    if not data:
        return f"Sorry, I couldn't fetch OHLC data for {symbol.upper()}."
    
    return f"""📈 **{symbol.upper()} OHLC Data ({timeframe})**

Open: ${data.get('open', 'N/A')}
High: ${data.get('high', 'N/A')}
Low: ${data.get('low', 'N/A')}
Close: ${data.get('close', 'N/A')}
"""

def format_forex_rate_response(data, base, quote):
    if not data:
        return f"Sorry, I couldn't fetch exchange rate for {base}/{quote}."
    
    def format_percentage(value):
        if value is None:
            return 'N/A'
        try:
            return f"{value:+.4f}%"
        except:
            return str(value)
    
    return f"""💱 **{base}/{quote} Exchange Rate**

Current Rate: {data.get('c', 'N/A')}
Daily Change: {format_percentage(data.get('dp'))}
High: {data.get('h', 'N/A')}
Low: {data.get('l', 'N/A')}
"""

def format_forex_ohlc_response(data, base, quote, timeframe):
    if not data:
        return f"Sorry, I couldn't fetch OHLC data for {base}/{quote}."
    
    return f"""📈 **{base}/{quote} OHLC Data ({timeframe})**

Open: {data.get('open', 'N/A')}
High: {data.get('high', 'N/A')}
Low: {data.get('low', 'N/A')}
Close: {data.get('close', 'N/A')}
"""

def format_forex_historical_response(data, base, quote):
    if not data:
        return f"Sorry, I couldn't fetch historical data for {base}/{quote}."
    
    return f"""📅 **{base}/{quote} Historical Rate**

Date: {data.get('date', 'N/A')}
Rate: {data.get('rate', 'N/A')}
"""

def format_economic_data_response(data):
    if not data:
        return "Sorry, I couldn't fetch economic data."
    
    response = "📊 **Recent Economic Events**\n\n"
    for i, event in enumerate(data[:5], 1):
        response += f"{i}. **{event.get('event', 'N/A')}**\n"
        response += f"   Country: {event.get('country', 'N/A')}\n"
        response += f"   Time: {event.get('time', 'N/A')}\n\n"
    
    return response

if __name__ == '__main__':
    app.run(debug=True)