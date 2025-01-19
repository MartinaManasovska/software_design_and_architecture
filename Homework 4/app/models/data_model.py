import sqlite3
import pandas as pd
import requests
from app.models.database_factory import DatabaseFactory

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

class DataModel:
    def __init__(self):
        # Initialize with SQLite database
        self.db = DatabaseFactory.get_database("sqlite", "updated_stocks_database.db")
        self.signal_service_url = 'http://signal-service:5001/process' #defines url of the service you wanna call
        #self.signal_service_url = 'http://localhost:5001/process' #defines url of the service you wanna call
    
    def get_db_connection(self):
        """Create a database connection using the factory"""
        return self.db.connect()
    
    def fetch_issuers_from_db(self):
        """Fetch unique issuers from database with error handling"""
        try:
            conn = self.get_db_connection()
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
        
    def fetch_stock_data_from_db(self, issuer, from_date, to_date):
        """Fetch stock data with comprehensive error handling"""
        try:
            conn = self.get_db_connection()
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
        
    def calculate_rsi_signals(self, data):
        """Calculate RSI and generate trading signals"""
        try:
            if not data:
                return []
            # Convert to records
            response = requests.post(
            self.signal_service_url, 
            json={'data': data}
            )
            return response.json()['signals']
        except Exception as e:
            print(f"Error calculating RSI signals: {e}")
            return []