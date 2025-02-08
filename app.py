from flask import Flask, render_template, request
import ccxt
import pandas as pd
import pandas_ta as ta  # ta-lib ki jagah pandas_ta ka use karein

app = Flask(__name__)

binance = ccxt.binance()

def get_signals(symbol, timeframe='1h'):
    try:
        ohlcv = binance.fetch_ohlcv(symbol, timeframe)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Indicators add karein (pandas_ta ka use karke)
        df['EMA20'] = ta.ema(df['close'], length=20)
        df['EMA50'] = ta.ema(df['close'], length=50)
        df['RSI'] = ta.rsi(df['close'], length=14)
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        signal = {
            'symbol': symbol,
            'action': 'HOLD',
            'entry': latest['close'],
            'sl': None,
            'tp1': None,
            'tp2': None
        }
        
        # Trend analysis
        if latest['EMA20'] > latest['EMA50'] and latest['RSI'] < 70:
            signal['action'] = 'BUY/LONG'
            signal['sl'] = round(latest['low'] * 0.98, 4)  # 2% stop loss
            signal['tp1'] = round(latest['close'] * 1.04, 4)  # 4% take profit
            signal['tp2'] = round(latest['close'] * 1.08, 4)
        elif latest['EMA20'] < latest['EMA50'] and latest['RSI'] > 30:
            signal['action'] = 'SELL/SHORT'
            signal['sl'] = round(latest['high'] * 1.02, 4)
            signal['tp1'] = round(latest['close'] * 0.96, 4)
            signal['tp2'] = round(latest['close'] * 0.92, 4)
            
        return signal
        
    except Exception as e:
        print(f"Error: {e}")
        return None

@app.route('/')
def index():
    markets = binance.load_markets()
    symbols = [symbol for symbol in markets.keys() if '/USDT' in symbol]
    return render_template('index.html', symbols=symbols)

@app.route('/get_signal', methods=['POST'])
def generate_signal():
    symbol = request.form['symbol']
    timeframe = request.form['timeframe']
    signal = get_signals(symbol, timeframe)
    return render_template('results.html', signal=signal)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
