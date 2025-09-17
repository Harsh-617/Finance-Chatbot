from flask import Flask, request, jsonify, render_template
import os
import json
import requests
import re
from dotenv import load_dotenv

# Import your custom modules
import data_fetcher
import intent_recognizer as chatbot
import response_handler
from response_handler import (
    format_crypto_price_response,
    format_crypto_supply_response, 
    format_crypto_ath_atl_response,
    format_crypto_ohlc_response,
    format_crypto_exchange_response,
    format_crypto_metadata_response,
    format_stock_price_response,
    format_stock_fundamentals_response,
    format_stock_earnings_response,
    format_stock_ratings_response,
    format_stock_insider_response,
    format_stock_technicals_response,
    format_stock_ohlc_response,
    format_forex_rate_response,
    format_forex_ohlc_response,
    format_forex_historical_response,
    format_economic_data_response
)
from visualization import create_price_chart

# Load environment variables
load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint that processes user messages"""
    try:
        user_input = request.json.get('message', '').strip()
        
        if not user_input:
            return jsonify({'response': 'Please provide a message.'})
        
        print(f"DEBUG - User input: {user_input}")
        
        # Analyze user input to extract intent and parameters
        analysis = chatbot.analyze_user_input(user_input)
        intent = analysis.get('intent')
        
        print(f"DEBUG - Final intent: {intent}")
        print(f"DEBUG - Full analysis: {analysis}")
        
        # Route to appropriate handler based on intent
        if intent == 'greeting_conversation':
            response = response_handler.handle_greetings_conversation(user_input)
            
        elif intent == 'answer_financial_query':
            response = response_handler.answer_financial_query(user_input)
            
        elif intent == 'crypto_price_overview':
            response = handle_crypto_price_request(analysis)
                
        elif intent == 'crypto_supply_info':
            response = handle_crypto_supply_request(analysis)
                
        elif intent == 'crypto_ath_atl':
            response = handle_crypto_ath_atl_request(analysis)
                
        elif intent == 'crypto_ohlc':
            response = handle_crypto_ohlc_request(analysis)
                
        elif intent == 'crypto_exchange_info':
            response = handle_crypto_exchange_request(analysis)
                
        elif intent == 'crypto_metadata':
            response = handle_crypto_metadata_request(analysis)
                
        elif intent == 'stock_price_overview':
            response = handle_stock_price_request(analysis)
                
        elif intent == 'stock_fundamentals':
            response = handle_stock_fundamentals_request(analysis)
                
        elif intent == 'stock_earnings':
            response = handle_stock_earnings_request(analysis)
                
        elif intent == 'stock_analyst_ratings':
            response = handle_stock_analyst_ratings_request(analysis)
                
        elif intent == 'stock_insider_ownership':
            response = handle_stock_insider_request(analysis)
                
        elif intent == 'stock_technicals':
            response = handle_stock_technicals_request(analysis)
                
        elif intent == 'stock_ohlc':
            response = handle_stock_ohlc_request(analysis)
                
        elif intent == 'forex_exchange_rate':
            response = handle_forex_rate_request(analysis)
                
        elif intent == 'forex_ohlc':
            response = handle_forex_ohlc_request(analysis)
                
        elif intent == 'forex_historical_rate':
            response = handle_forex_historical_request(analysis)
                
        elif intent == 'forex_economic_data':
            response = handle_economic_data_request()

        elif intent == 'chart':
            return handle_chart_request(analysis)

        else:
            response = "I understand you're asking about financial data, but I need more specific information. Try asking about stock prices, crypto data, or forex rates."
            
    except Exception as e:
        print(f"DEBUG - Error in chat route: {e}")
        response = f"I apologize, but I encountered an error while processing your request. Please try again."
    
    return jsonify({'response': response})

# Helper functions for handling different request types
def handle_crypto_price_request(analysis):
    """Handle cryptocurrency price overview requests"""
    symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
    if symbol:
        symbol = symbol.upper()
        print(f"DEBUG - Fetching crypto data for: {symbol}")
        data = data_fetcher.get_crypto_price_overview(symbol)
        print(f"DEBUG - Crypto data received: {data}")
        return format_crypto_price_response(data, symbol)
    else:
        return "Please specify which cryptocurrency you'd like to know about."

def handle_crypto_supply_request(analysis):
    """Handle cryptocurrency supply information requests"""
    symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
    if symbol:
        print(f"DEBUG - Fetching crypto supply for: {symbol}")
        data = data_fetcher.get_crypto_supply_info(symbol)
        print(f"DEBUG - Supply data received: {data}")
        return format_crypto_supply_response(data, symbol)
    else:
        return "Please specify which cryptocurrency's supply information you'd like to know."

def handle_crypto_ath_atl_request(analysis):
    """Handle cryptocurrency ATH/ATL requests"""
    symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
    if symbol:
        data = data_fetcher.get_crypto_ath_atl(symbol)
        return format_crypto_ath_atl_response(data, symbol)
    else:
        return "Please specify which cryptocurrency's ATH/ATL you'd like to know."

def handle_crypto_ohlc_request(analysis):
    """Handle stock OHLC requests"""
    symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
    time_period = analysis.get('timeframe') or '30d'
    if symbol:
        symbol = symbol.upper()
        data = data_fetcher.get_crypto_ohlc(symbol, time_period)
        return format_crypto_ohlc_response(data, symbol, time_period)
    else:
        return "Please specify which cryptocurrency's OHLC data you'd like to see."

def handle_crypto_exchange_request(analysis):
    """Handle cryptocurrency exchange information requests"""
    symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
    if symbol:
        symbol = symbol.upper()
        data = data_fetcher.get_crypto_exchange_info(symbol)
        return format_crypto_exchange_response(data, symbol)
    else:
        return "Please specify which cryptocurrency's exchange information you'd like to see."

def handle_crypto_metadata_request(analysis):
    """Handle cryptocurrency metadata requests"""
    symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
    if symbol:
        symbol = symbol.upper()
        data = data_fetcher.get_crypto_metadata(symbol)
        return format_crypto_metadata_response(data, symbol)
    else:
        return "Please specify which cryptocurrency's information you'd like to see."

def handle_stock_price_request(analysis):
    """Handle stock price overview requests"""
    symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
    if symbol:
        symbol = symbol.upper()
        data = data_fetcher.get_stock_price_overview(symbol)
        return format_stock_price_response(data, symbol)
    else:
        return "Please specify which stock you'd like to know about."

def handle_stock_fundamentals_request(analysis):
    """Handle stock fundamentals requests"""
    symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
    if symbol:
        symbol = symbol.upper()
        data = data_fetcher.get_stock_fundamentals(symbol)
        return format_stock_fundamentals_response(data, symbol)
    else:
        return "Please specify which stock's fundamentals you'd like to see."

def handle_stock_earnings_request(analysis):
    """Handle stock earnings requests"""
    symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
    if symbol:
        symbol = symbol.upper()
        print(f"DEBUG - Fetching earnings for: {symbol}")
        data = data_fetcher.get_stock_earnings(symbol)
        print(f"DEBUG - Earnings data received: {data}")
        return format_stock_earnings_response(data, symbol)
    else:
        return "Please specify which stock's earnings you'd like to see."

def handle_stock_analyst_ratings_request(analysis):
    """Handle stock analyst ratings requests"""
    symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
    if symbol:
        symbol = symbol.upper()
        data = data_fetcher.get_stock_analyst_ratings(symbol)
        return format_stock_ratings_response(data, symbol)
    else:
        return "Please specify which stock's analyst ratings you'd like to see."

def handle_stock_insider_request(analysis):
    """Handle stock insider ownership requests"""
    symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
    if symbol:
        symbol = symbol.upper()
        data = data_fetcher.get_stock_insider_ownership(symbol)
        return format_stock_insider_response(data, symbol)
    else:
        return "Please specify which stock's insider data you'd like to see."

def handle_stock_technicals_request(analysis):
    """Handle stock technical indicators requests"""
    symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
    if symbol:
        symbol = symbol.upper()
        data = data_fetcher.get_stock_technicals(symbol)
        return format_stock_technicals_response(data, symbol)
    else:
        return "Please specify which stock's technical indicators you'd like to see."

def handle_stock_ohlc_request(analysis):
    """Handle stock OHLC requests"""
    symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
    time_period = analysis.get('timeframe') or '30d'
    if symbol:
        symbol = symbol.upper()
        data = data_fetcher.get_stock_ohlc(symbol, time_period)
        return format_stock_ohlc_response(data, symbol, time_period)
    else:
        return "Please specify which stock's OHLC data you'd like to see."

def handle_forex_rate_request(analysis):
    """Handle forex exchange rate requests"""
    base = analysis.get('base_currency')
    quote = analysis.get('quote_currency')
    
    if base and quote:
        base = base.upper()
        quote = quote.upper()
        print(f"DEBUG - Fetching forex rate for {base}/{quote}")
        data = data_fetcher.get_forex_exchange_rate(base, quote)
        print(f"DEBUG - Forex data received: {data}")
        return format_forex_rate_response(data, base, quote)
    else:
        return "Please specify the currency pair (e.g., EUR to USD, dollar to INR)."

def handle_forex_ohlc_request(analysis):
    """Handle forex OHLC requests"""
    base = analysis.get('base_currency')
    quote = analysis.get('quote_currency')
    timeframe = analysis.get('timeframe', 'daily')
    if base and quote:
        base = base.upper()
        quote = quote.upper()
        data = data_fetcher.get_forex_ohlc(base, quote, timeframe)
        return format_forex_ohlc_response(data, base, quote, timeframe)
    else:
        return "Please specify the currency pair for OHLC data."

def handle_forex_historical_request(analysis):
    """Handle forex historical rate requests"""
    base = analysis.get('base_currency')
    quote = analysis.get('quote_currency')
    date = analysis.get('date_range')
    if base and quote:
        base = base.upper()
        quote = quote.upper()
        data = data_fetcher.get_forex_historical_rate(base, quote, date)
        return format_forex_historical_response(data, base, quote)
    else:
        return "Please specify the currency pair and date for historical rates."

def handle_economic_data_request():
    """Handle economic data requests"""
    data = data_fetcher.get_forex_economic_data()
    return format_economic_data_response(data)

def handle_chart_request(analysis):
    """Handle chart generation requests"""
    symbol = analysis.get('asset_symbol') or analysis.get('asset_name')
    time_period = analysis.get('time_period', '30d')
    asset_type = analysis.get('asset_type')
    
    if not symbol:
        return jsonify({'response': 'Could not identify asset symbol for chart'})
    
    valid_periods = ["1d", "7d", "30d", "90d", "1y"]
    if time_period not in valid_periods:
        return jsonify({'response': f"Invalid time period. I can generate charts for: {', '.join(valid_periods)}"})
    
    if not asset_type:
        return jsonify({'response': "Could not determine if this is a crypto or stock asset"})
    
    print(f"DEBUG - Creating chart for {symbol}, period: {time_period}, type: {asset_type}")
    chart_result = create_price_chart(symbol, time_period, asset_type)
    
    if chart_result['success']:
        change_emoji = "📈" if chart_result['price_change'] >= 0 else "📉"
        response = f"""📊 **{chart_result['symbol']} Price Chart ({time_period})**

💰 Current Price: ${chart_result['current_price']:.2f}
{change_emoji} Period Change: {chart_result['price_change']:+.2f}%

📈 Chart generated successfully!"""
        
        return jsonify({
            'response': response.strip(),
            'chart': chart_result['chart_data']
        })
    else:
        return jsonify({'response': f"❌ {chart_result['error']}"})

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Check if required environment variables are set
    required_vars = ['GROQ_API_KEY', 'FINNHUB_API_KEY', 'ALPHA_VANTAGE_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("Some features may not work properly.")
    
    print("Starting Financial Chatbot...")
    print("Available endpoints:")
    print("- GET  /           : Chat interface")
    print("- POST /chat       : Chat API endpoint")
    
    app.run(debug=True, host='0.0.0.0', port=5000)