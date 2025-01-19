from flask import Flask, request, jsonify
import pandas as pd
from ta.momentum import RSIIndicator

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_signals():
    raw_data = request.json['data']
    # Complex signal processing logic isolated here
    processed_signals = calculate_signals(raw_data)
    return jsonify({'signals': processed_signals})

def calculate_signals(data):
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
    return df[['date', 'last_trade_price', 'RSI', 'signal']].to_dict('records')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)