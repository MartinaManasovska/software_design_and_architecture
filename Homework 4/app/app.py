from app.controllers.controller import DataController
from flask import Flask, render_template, jsonify, request
import datetime
import numpy as np

# Initialize Flask app
app = Flask(__name__)

controller=DataController() #creates an object from the type DataController

@app.route('/')
def index():
    """Render the main page"""
    return render_template('frontend-graph.html')

@app.route('/api/issuers', methods=['GET'])
def get_issuers():
    """API endpoint to get list of issuers"""
    return controller.fetch_issuers()

@app.route('/api/getStockData', methods=['GET'])
def get_stock_data():
    """API endpoint to get stock data"""
    return controller.get_stock_data(request)

@app.route('/api/getRSISignals', methods=['GET'])
def get_rsi_signals():
    """API endpoint to get RSI signals"""
    return controller.get_rsi_signals(request)

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