import sqlite3
import pandas as pd
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, CCIIndicator, SMAIndicator, EMAIndicator
import numpy as np
import logging
from ta.momentum import WilliamsRIndicator, ROCIndicator
from ta.trend import ADXIndicator
from ta.volatility import BollingerBands, AverageTrueRange

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_data(issuer):
    """Load data from SQLite database"""
    try:
        conn = sqlite3.connect('updated_stocks_database.db')
        query = f"""
        SELECT date, last_trade_price, max, min, volume 
        FROM transactions 
        WHERE issuer = '{issuer}'
        ORDER BY date
        """
        df = pd.read_sql_query(query, conn)
        print(df)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)

        #conversion 
        df['last_trade_price'] = df['last_trade_price'].str.replace(',', '', regex=False)
        df['max'] = df['max'].str.replace(',', '', regex=False)
        df['min'] = df['min'].str.replace(',', '', regex=False)
        df['volume'] = df['volume'].str.replace(',', '', regex=False)
        
        # Convert columns to numeric
        df['last_trade_price'] = pd.to_numeric(df['last_trade_price'], errors='coerce')
        df['max'] = pd.to_numeric(df['max'], errors='coerce')
        df['min'] = pd.to_numeric(df['min'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        # Remove any rows with NaN values
        print("After conversion", df)
        df = df.dropna()
        print("After drop: ", issuer, df)
        conn.close()
        return df
    except Exception as e:
        logger.error(f"Error loading data for {issuer}: {e}")
        return pd.DataFrame()


def calculate_indicators_and_generate_signals(df):
    """Calculate technical indicators and generate trading signals"""
    try:
        # RSI
        df['RSI'] = RSIIndicator(close=df['last_trade_price'], window=2).rsi()
        
        # Stochastic
        df['STOCH'] = StochasticOscillator(
            high=df['max'],
            low=df['min'],
            close=df['last_trade_price'],
            window=14
        ).stoch()
        
        # MACD
        macd = MACD(close=df['last_trade_price'])
        df['MACD'] = macd.macd()
        df['Signal_Line'] = macd.macd_signal()
        
        # Moving Averages
        df['SMA'] = SMAIndicator(close=df['last_trade_price'], window=2).sma_indicator()
        df['EMA'] = EMAIndicator(close=df['last_trade_price'], window=2).ema_indicator()
        
        # Generate signals
        df['RSI_Signal'] = 'Hold'
        df.loc[df['RSI'] < 30, 'RSI_Signal'] = 'Buy'
        df.loc[df['RSI'] > 70, 'RSI_Signal'] = 'Sell'
        
        df['STOCH_Signal'] = 'Hold'
        df.loc[df['STOCH'] < 20, 'STOCH_Signal'] = 'Buy'
        df.loc[df['STOCH'] > 80, 'STOCH_Signal'] = 'Sell'
        
        df['MACD_Signal'] = 'Hold'
        df.loc[df['MACD'] > df['Signal_Line'], 'MACD_Signal'] = 'Buy'
        df.loc[df['MACD'] < df['Signal_Line'], 'MACD_Signal'] = 'Sell'
        
        return df
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        return df

def resample_data(df, freq):
    """Resample data to specified frequency"""
    try:
        df_resampled = df.resample(freq).agg({
            'last_trade_price': 'last',
            'max': 'max',
            'min': 'min',
            'volume': 'sum'
        }).dropna()
        return df_resampled
    except Exception as e:
        logger.error(f"Error resampling data: {e}")
        return pd.DataFrame()

def save_results(df, issuer, freq):
    """Save analysis results to database"""
    try:
        conn = sqlite3.connect('updated_stocks_database.db')
        df.reset_index(inplace=True)
        df['issuer'] = issuer
        df['time_period'] = freq
        
        # Use INSERT OR REPLACE to avoid unique constraint violations
        df.to_sql('analysis_results', conn, if_exists='replace', index=False)
        conn.close()
        logger.info(f"Successfully saved results for {issuer} - {freq}")
    except Exception as e:
        logger.error(f"Error saving results: {e}")


def get_issuers():
    """Get list of unique issuers from database"""
    try:
        conn = sqlite3.connect('updated_stocks_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT issuer FROM transactions")
        issuers = [row[0] for row in cursor.fetchall()]
        conn.close()
        return issuers
    except Exception as e:
        logger.error(f"Error getting issuers: {e}")
        return []

def create_analysis_table():
    """Create analysis_results table if it doesn't exist"""
    try:
        conn = sqlite3.connect('updated_stocks_database.db')
        cursor = conn.cursor()
        cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS analysis_results (
            date DATE,
            issuer TEXT,
            time_period TEXT,
            last_trade_price FLOAT,
            max FLOAT,
            min FLOAT,
            volume FLOAT,
            RSI FLOAT,
            STOCH FLOAT,
            MACD FLOAT,
            Signal_Line FLOAT,
            SMA FLOAT,
            EMA FLOAT,
            RSI_Signal TEXT,
            STOCH_Signal TEXT,
            MACD_Signal TEXT,
            PRIMARY KEY (date, issuer, time_period)
        )
        ''')
        conn.commit()
        conn.close()
        logger.info("Analysis table created/verified successfully")
    except Exception as e:
        logger.error(f"Error creating analysis table: {e}")

def main():
    # Create analysis table
    #create_analysis_table()
    
    # Get list of issuers
    #issuers = get_issuers()
    issuers=['ALK']
    logger.info(f"Found {len(issuers)} issuers to process")
    
    for issuer in issuers:
        logger.info(f"Processing issuer: {issuer}")
        
        # Load data
        df = load_data(issuer)
        if df.empty:
            logger.warning(f"No data found for {issuer}")
            continue
            
        # Process different time periods
        time_periods = {
            '1 Day': 'D',  # Daily
            '1 Week': 'W',  # Weekly
            '1 Month': 'ME'  # Monthly
        }
        
        for period_name, period_code in time_periods.items():
            logger.info(f"Processing {period_name} data for {issuer}")
            
            # Resample and calculate indicators
            df_resampled = resample_data(df, period_code)
            if df_resampled.empty:
                continue
                
            df_analyzed = calculate_indicators_and_generate_signals(df_resampled)
            
            # Save results
            #save_results(df_analyzed, issuer, period_name)
            print (df_analyzed)

if __name__ == "__main__":
    main()
