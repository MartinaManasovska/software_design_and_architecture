from flask import render_template, jsonify
from app.models.data_model import DataModel
from datetime import datetime, timedelta

class DataController:
    def __init__(self):
        self.model = DataModel()

    def fetch_issuers(self):
        issuers = self.model.fetch_issuers_from_db()
        if not issuers:
            return jsonify({"error": "No issuers found"}), 404
        return jsonify(issuers)
    
    def get_rsi_signals(self, request):
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
            raw_data = self.model.fetch_stock_data_from_db(issuer, from_date, to_date)
            if not raw_data:
                return jsonify({"error": f"No data found for {issuer} between {from_date} and {to_date}"}), 404

            # Calculate signals
            signals = self.model.calculate_rsi_signals(raw_data)
            if not signals:
                return jsonify({"error": "Error calculating signals"}), 500

            return jsonify(signals)
        except Exception as e:
            #return jsonify({"error": str(e)}), 500
            import traceback
            print(f"Error in get_rsi_signals: {str(e)}")
            print(traceback.format_exc())
            return jsonify({"error": str(e)}), 500
        
    def get_stock_data(self, request):
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

            data = self.model.fetch_stock_data_from_db(issuer, from_date, to_date)
            if not data:
                return jsonify({"error": f"No data found for {issuer} between {from_date} and {to_date}"}), 404

            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500