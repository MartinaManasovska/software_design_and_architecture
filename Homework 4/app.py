from flask import Flask, render_template, jsonify, request
from ta.momentum import RSIIndicator
import sqlite3
import datetime
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Initialize Flask app
app = Flask(__name__)

def get_db_connection():
    """Create a database connection with error handling"""
    try:
        conn = sqlite3.connect("updated_stocks_database.db")
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def format_price(price):
    """Convert price string to float with robust error handling"""
    if isinstance(price, (int, float)):
        return float(price)
    if not price or not isinstance(price, str):
        return 0.0
    price = price.strip()
    try:
        return float(price.replace('.', '').replace(',', '.'))
    except ValueError:
        return 0.0

@app.route('/')
def index():
    """Render the main page"""
    return render_template('frontend-graph.html')

def fetch_issuers_from_db():
    """Fetch unique issuers from database with error handling"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT issuer FROM transactions ORDER BY issuer")
        issuers = cursor.fetchall()
        conn.close()
        return [{"code": issuer[0], "name": issuer[0]} for issuer in issuers]
    except sqlite3.Error as e:
        print(f"Error fetching issuers: {e}")
        return []

@app.route('/api/issuers', methods=['GET'])
def get_issuers():
    """API endpoint to get list of issuers"""
    issuers = fetch_issuers_from_db()
    if not issuers:
        return jsonify({"error": "No issuers found"}), 404
    return jsonify(issuers)

def fetch_stock_data_from_db(issuer, from_date, to_date):
    """Fetch stock data with comprehensive error handling"""
    try:
        conn = get_db_connection()
        if not conn:
            return None

        cursor = conn.cursor()
        query = """
        SELECT issuer, date, last_trade_price, max, min, volume, turnover_best
        FROM transactions
        WHERE issuer = ? 
        AND date BETWEEN ? AND ?
        ORDER BY date
        """
        
        cursor.execute(query, (issuer, from_date, to_date))
        stock_data = cursor.fetchall()
        conn.close()

        if not stock_data:
            return None

        return [
            {
                "issuer": row[0],
                "date": row[1],
                "last_trade_price": format_price(row[2]),
                "max": format_price(row[3]),
                "min": format_price(row[4]),
                "volume": row[5],
                "turnover_best": row[6]
            }
            for row in stock_data
        ]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return None

@app.route('/api/getStockData', methods=['GET'])
def get_stock_data():
    """API endpoint to get stock data"""
    try:
        issuer = request.args.get('issuer')
        from_date = request.args.get('from')
        to_date = request.args.get('to')

        if not all([issuer, from_date, to_date]):
            return jsonify({"error": "Missing required parameters"}), 400

        try:
            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        data = fetch_stock_data_from_db(issuer, from_date, to_date)
        if not data:
            return jsonify({"error": f"No data found for {issuer} between {from_date} and {to_date}"}), 404

        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def calculate_rsi_signals(data):
    """Calculate RSI and generate trading signals"""
    try:
        if not data:
            return []

        df = pd.DataFrame(data)
        
        # Ensure numeric type for calculations
        df['last_trade_price'] = pd.to_numeric(df['last_trade_price'], errors='coerce')
        
        # Calculate RSI
        rsi = RSIIndicator(close=df['last_trade_price'], window=14)
        df['RSI'] = rsi.rsi()
        
        # Generate signals
        df['signal'] = 'Hold'
        df.loc[df['RSI'] < 30, 'signal'] = 'Buy'
        df.loc[df['RSI'] > 70, 'signal'] = 'Sell'
        
        # Handle NaN values
        df = df.fillna({
            'RSI': 50,
            'signal': 'Hold'
        })
        
        # Convert to records
        return df[['date', 'last_trade_price', 'RSI', 'signal']].to_dict('records')
    except Exception as e:
        print(f"Error calculating RSI signals: {e}")
        return []

@app.route('/api/getRSISignals', methods=['GET'])
def get_rsi_signals():
    """API endpoint to get RSI signals"""
    try:
        # Get parameters
        issuer = request.args.get('issuer')
        from_date = request.args.get('from')
        to_date = request.args.get('to')

        if not all([issuer, from_date, to_date]):
            return jsonify({"error": "Missing required parameters"}), 400

        # Validate dates
        try:
            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        # Fetch data
        raw_data = fetch_stock_data_from_db(issuer, from_date, to_date)
        if not raw_data:
            return jsonify({"error": f"No data found for {issuer} between {from_date} and {to_date}"}), 404

        # Calculate signals
        signals = calculate_rsi_signals(raw_data)
        if not signals:
            return jsonify({"error": "Error calculating signals"}), 500

        return jsonify(signals)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)