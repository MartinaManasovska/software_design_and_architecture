from flask import Flask, render_template, jsonify, request
import sqlite3
import datetime

app = Flask(__name__)

# Helper function to connect to the SQLite DB
def get_db_connection():
    conn = sqlite3.connect("updated_stocks_database.db")
    conn.row_factory = sqlite3.Row  # To get results as dictionaries
    return conn

# Route to render the index page (your HTML file)
@app.route('/')
def index():
    return render_template('index.html')  # Ensure your HTML file is in the templates folder

# Fetch all issuers from the database
def fetch_issuers_from_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT issuer FROM transactions")  # Query to get all distinct issuers
    issuers = cursor.fetchall()
    conn.close()
    return [{"code": issuer[0], "name": issuer[0]} for issuer in issuers]

@app.route('/api/issuers', methods=['GET'])
def get_issuers():
    issuers = fetch_issuers_from_db()
    return jsonify(issuers)

# Helper function to format the price
def format_price(price):
    if price:
        return float(price.replace('.', '').replace(',', '.'))
    return 0.0

# Function to fetch stock data for the selected issuer and date range
def fetch_stock_data_from_db(issuer, from_date, to_date):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT issuer, date, last_trade_price, max, min, volume, turnover_best
    FROM transactions
    WHERE issuer = ? AND date BETWEEN ? AND ?
    """
    cursor.execute(query, (issuer, from_date, to_date))
    stock_data = cursor.fetchall()
    conn.close()

    if stock_data:
        return [
            {
                "issuer": row[0],
                "date": row[1],
                "lastTradePrice": format_price(row[2]),  # Format the price here
                "max": row[3],
                "min": row[4],
                "volume": row[5],
                "turnoverBest": row[6]
            }
            for row in stock_data
        ]
    else:
        return None

@app.route('/api/getStockData', methods=['GET'])
def get_stock_data():
    issuer = request.args.get('issuer')
    from_date = request.args.get('from')
    to_date = request.args.get('to')

    if not issuer or not from_date or not to_date:
        return jsonify({"error": "Missing parameters"}), 400

    # Validate date format
    try:
        from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d').date()
        to_date = datetime.datetime.strptime(to_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use 'YYYY-MM-DD'."}), 400

    # Fetch stock data from the database
    data = fetch_stock_data_from_db(issuer, from_date, to_date)
    if data:
        return jsonify(data)
    else:
        return jsonify({"error": "No data found for the given period."}), 404

if __name__ == '__main__':
    app.run(debug=True)
