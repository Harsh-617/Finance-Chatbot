import requests
import os
import json
from dotenv import load_dotenv
# Import RAG components
try:
    from rag.rag_retrieval import get_rag_retrieval, get_knowledge_context
    RAG_AVAILABLE = True
except ImportError:
    print("RAG components not available. Financial queries will work without RAG enhancement.")
    RAG_AVAILABLE = False

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ============= UTILITY FORMATTING FUNCTIONS =============

def format_currency(value):
    """Format currency values with appropriate suffixes"""
    if value is None:
        return 'N/A'
    try:
        if value >= 1e12:
            return f"${value/1e12:.2f}T"
        elif value >= 1e9:
            return f"${value/1e9:.2f}B"
        elif value >= 1e6:
            return f"${value/1e6:.2f}M"
        else:
            return f"${value:,.2f}"
    except:
        return str(value)

def format_percentage(value):
    """Format percentage values with + or - sign"""
    if value is None:
        return 'N/A'
    try:
        return f"{value:+.2f}%"
    except:
        return str(value)

def format_supply_number(num):
    """Format supply numbers with appropriate suffixes"""
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

def format_large_number(num):
    """Format large numbers for financial data"""
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

# ============= CRYPTO RESPONSE FORMATTERS =============

def format_crypto_price_response(data, symbol):
    """Format crypto price overview response"""
    if not data:
        return f"Sorry, I couldn't fetch price data for {symbol.upper()}."
    
    return f"""💰 **{symbol.upper()} Price Overview**

Current Price: {format_currency(data.get('price'))}
24h Change: {format_percentage(data.get('percent_change_24h'))}
7d Change: {format_percentage(data.get('percent_change_7d'))}
Market Cap: {format_currency(data.get('market_cap_usd'))}
24h Volume: {format_currency(data.get('volume_24h_usd'))}
"""

def format_crypto_supply_response(data, symbol):
    """Format crypto supply information response"""
    if not data:
        return f"Sorry, I couldn't fetch supply data for {symbol.upper()}."
    
    max_supply_text = format_supply_number(data.get('max_supply')) if data.get('max_supply') else 'Unlimited'
    
    return f"""📊 **{symbol.upper()} Supply Information**

Circulating Supply: {format_supply_number(data.get('circulating_supply'))}
Total Supply: {format_supply_number(data.get('total_supply'))}
Max Supply: {max_supply_text}
"""

def format_crypto_ath_atl_response(data, symbol):
    """Format crypto ATH/ATL response"""
    if not data:
        return f"Sorry, I couldn't fetch ATH/ATL data for {symbol.upper()}."
    
    return f"""🏔️ **{symbol.upper()} All-Time High/Low**

ATH Price: ${data.get('ath', 'N/A')}
ATH Date: {data.get('ath_date', 'N/A')}
ATL Price: ${data.get('atl', 'N/A')}
ATL Date: {data.get('atl_date', 'N/A')}
"""

def format_crypto_ohlc_response(data, symbol, time_period):
    """Format crypto OHLC response"""
    if not data:
        return f"Sorry, I couldn't fetch OHLC data for {symbol.upper()}."
    
    return f"""📈 **{symbol.upper()} OHLC Data ({time_period})**

Open: ${data.get('open', 'N/A')}
High: ${data.get('high', 'N/A')}
Low: ${data.get('low', 'N/A')}
Close: ${data.get('close', 'N/A')}
"""

def format_crypto_exchange_response(data, symbol):
    """Format crypto exchange information response"""
    if not data:
        return f"Sorry, I couldn't fetch exchange data for {symbol.upper()}."
    
    response = f"🏦 **{symbol.upper()} Top Exchanges**\n\n"
    for i, exchange in enumerate(data[:5], 1):
        response += f"{i}. **{exchange.get('exchange_name', 'N/A')}**\n"
        response += f"   Price: ${exchange.get('price', 'N/A')}\n"
        response += f"   24h Volume: {exchange.get('volume_24h', 'N/A')}\n\n"
    
    return response

def format_crypto_metadata_response(data, symbol):
    """Format crypto metadata response"""
    if not data:
        return f"Sorry, I couldn't fetch metadata for {symbol.upper()}."
    
    description = data.get('description', 'No description available')
    if len(description) > 200:
        description = description[:200] + "..."
    
    return f"""ℹ️ **{symbol.upper()} Information**

Name: {data.get('name', 'N/A')}
Full Name: {data.get('full_name', 'N/A')}
Algorithm: {data.get('algorithm', 'N/A')}
Proof Type: {data.get('proof_type', 'N/A')}
Description: {description}
"""

# ============= STOCK RESPONSE FORMATTERS =============

def format_stock_price_response(data, symbol):
    """Format stock price overview response"""
    if not data:
        return f"Sorry, I couldn't fetch price data for {symbol.upper()}."
    
    return f"""📈 **{symbol.upper()} Stock Overview**

Current Price: ${data.get('c', 'N/A')}
Daily Change: {format_percentage(data.get('dp'))}
High: ${data.get('h', 'N/A')}
Low: ${data.get('l', 'N/A')}
Previous Close: ${data.get('pc', 'N/A')}
"""

def format_stock_fundamentals_response(data, symbol):
    """Format stock fundamentals response"""
    if not data:
        return f"Sorry, I couldn't fetch fundamental data for {symbol.upper()}."
    
    return f"""📊 **{symbol.upper()} Fundamentals**

Market Cap: {format_large_number(data.get('marketCapitalization'))}
P/E Ratio: {data.get('peBasicExclExtraTTM', 'N/A')}
EPS: ${data.get('epsInclExtraItemsTTM', 'N/A')}
Beta: {data.get('beta', 'N/A')}
"""

def format_stock_earnings_response(data, symbol):
    """Format stock earnings response"""
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
    """Format stock analyst ratings response"""
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
    """Format stock insider transactions response"""
    if not data:
        return f"Sorry, I couldn't fetch insider data for {symbol.upper()}."
    
    response = f"🔍 **{symbol.upper()} Recent Insider Transactions**\n\n"
    for i, transaction in enumerate(data[:3], 1):
        response += f"{i}. **{transaction.get('name', 'N/A')}**\n"
        response += f"   Shares: {transaction.get('share', 'N/A')}\n"
        response += f"   Transaction: {transaction.get('transactionCode', 'N/A')}\n\n"
    
    return response

def format_stock_technicals_response(data, symbol):
    """Format stock technical indicators response"""
    if not data:
        return f"Sorry, I couldn't fetch technical data for {symbol.upper()}."
    
    return f"""📊 **{symbol.upper()} Technical Indicators**

RSI (14): {data.get('rsi', 'N/A')}
SMA (20): {data.get('sma_20', 'N/A')}
"""

def format_stock_ohlc_response(data, symbol, time_period):
    """Format stock OHLC response"""
    if not data:
        return f"Sorry, I couldn't fetch OHLC data for {symbol.upper()}."
    
    return f"""📈 **{symbol.upper()} OHLC Data ({time_period})**

Open: ${data.get('open', 'N/A')}
High: ${data.get('high', 'N/A')}
Low: ${data.get('low', 'N/A')}
Close: ${data.get('close', 'N/A')}
"""

# ============= FOREX RESPONSE FORMATTERS =============

def format_forex_rate_response(data, base, quote):
    """Format forex exchange rate response"""
    if not data:
        return f"Sorry, I couldn't fetch exchange rate for {base}/{quote}."
    
    def format_forex_percentage(value):
        if value is None:
            return 'N/A'
        try:
            return f"{value:+.4f}%"
        except:
            return str(value)
    
    return f"""💱 **{base}/{quote} Exchange Rate**

Current Rate: {data.get('c', 'N/A')}
Daily Change: {format_forex_percentage(data.get('dp'))}
High: {data.get('h', 'N/A')}
Low: {data.get('l', 'N/A')}
"""

def format_forex_ohlc_response(data, base, quote, timeframe):
    """Format forex OHLC response"""
    if not data:
        return f"Sorry, I couldn't fetch OHLC data for {base}/{quote}."
    
    return f"""📈 **{base}/{quote} OHLC Data ({timeframe})**

Open: {data.get('open', 'N/A')}
High: {data.get('high', 'N/A')}
Low: {data.get('low', 'N/A')}
Close: {data.get('close', 'N/A')}
"""

def format_forex_historical_response(data, base, quote):
    """Format forex historical rate response"""
    if not data:
        return f"Sorry, I couldn't fetch historical data for {base}/{quote}."
    
    return f"""📅 **{base}/{quote} Historical Rate**

Date: {data.get('date', 'N/A')}
Rate: {data.get('rate', 'N/A')}
"""

def format_economic_data_response(data):
    """Format economic data response"""
    if not data:
        return "Sorry, I couldn't fetch economic data."
    
    response = "📊 **Recent Economic Events**\n\n"
    for i, event in enumerate(data[:5], 1):
        response += f"{i}. **{event.get('event', 'N/A')}**\n"
        response += f"   Country: {event.get('country', 'N/A')}\n"
        response += f"   Time: {event.get('time', 'N/A')}\n\n"
    
    return response

def format_top_movers_response(data, asset_type, count):
    """
    Pretty-print the top-<count> list for crypto / stock / forex.
    data  : list[dict]  (from get_top_*_by_mcap)
    asset_type : 'crypto' | 'stock' | 'forex'
    count : int (user-requested number)
    """
    if not data:
        return f"Sorry, I couldn't fetch the top {asset_type} list right now."

    emoji = {'crypto': '🪙', 'stock': '📈', 'forex': '💱'}.get(asset_type, '📊')
    lines = [f"{emoji} **Top {count} {asset_type.capitalize()} Assets**", ""]

    for idx, it in enumerate(data[:count], 1):          # slice to requested length
        sym   = it['symbol']
        name  = it.get('name', '')
        price = it['price']
        chg   = it.get('change_24h')

        price_str = f"${price:,.2f}" if price else "N/A"
        chg_str   = f"{chg:+.2f}%"  if chg  else "N/A"

        lines.append(f"{idx}. **{sym}**  {name}")
        lines.append(f"   Price: {price_str}  |  24h: {chg_str}")

    return "\n".join(lines)

# ============= CHATBOT RESPONSE FUNCTIONS =============

def answer_financial_query(user_input):
    """Answer general financial questions using Groq with RAG enhancement"""
    if not GROQ_API_KEY:
        return "I apologize, but I need API access to answer financial questions right now."
    
    # Get RAG context if available
    rag_context = ""
    if RAG_AVAILABLE:
        try:
            rag = get_rag_retrieval()
            if rag.is_available():
                search_result = rag.smart_search(user_input)
                if search_result["found_relevant"]:
                    rag_context = search_result["context"]
                    print(f"DEBUG - RAG found relevant knowledge using {search_result['method']}")
                else:
                    print(f"DEBUG - RAG search completed but low relevance (max: {search_result.get('max_similarity', 0):.2f})")
        except Exception as e:
            print(f"DEBUG - RAG search error: {e}")
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Enhanced prompt with RAG context
    base_prompt = """You are a knowledgeable financial advisor AI with expertise in stocks, cryptocurrency, forex, and financial markets. 
Answer the user's financial question clearly and comprehensively. Be concise and direct.

Guidelines:
- Provide accurate, educational explanations of financial concepts
- Use simple language but maintain professional accuracy
- If the question requires real-time data, suggest specific queries they can ask
- Draw from your knowledge of financial markets, trading, investment principles, and economic concepts
- Be helpful and informative without being overly technical
- Try to answer each query in 2-3 paragraphs
- Answer only what is asked"""

    if rag_context:
        prompt = f"""{base_prompt}

{rag_context}

Based on the above knowledge and your expertise, please answer this question:
User question: {user_input}

If the provided knowledge is relevant, incorporate it naturally into your answer. If not relevant, answer based on your general knowledge."""
    else:
        prompt = f"""{base_prompt}

User question: {user_input}"""
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 400  # Increased for RAG-enhanced responses
    }
    
    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"I apologize, but I'm having trouble processing your financial query right now. Error: {e}"

def handle_greetings_conversation(user_input):
    """Handle greetings and general conversation using Groq"""
    if not GROQ_API_KEY:
        return "Hello! I'm your financial assistant. I can help you with stock prices, crypto data, forex rates, and financial questions. How can I assist you today?"
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    You are a friendly financial chatbot assistant. Respond to this greeting/conversation in a warm, 
    professional way. Keep it brief and guide the conversation toward how you can help with financial 
    information like stock prices, crypto data, forex rates, etc.

    User message: {user_input}
    """
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 200
    }
    
    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        return "Hello! I'm your financial assistant. I can help you with stock prices, crypto data, forex rates, and financial questions. How can I assist you today?"