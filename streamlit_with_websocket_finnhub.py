import streamlit as st
import websocket
import threading
import json
import queue
import time

# Global queue to communicate between WebSocket thread and Streamlit
data_queue = queue.Queue()
# Global flag to control the WebSocket connection
is_running = False
ws_app = None
# Global variable to store the symbol to subscribe to
subscribed_symbol = ""

def on_message(ws, message):
    print(f"Received message: {message}") # Log raw message to console
    try:
        data = json.loads(message)
        data_queue.put(data)
    except Exception as e:
        print(f"Error parsing message: {e}")

def on_error(ws, error):
    print(f"WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    global subscribed_symbol
    print(f"WebSocket Opened. Subscribing to: {subscribed_symbol}")
    if subscribed_symbol:
        subscribe_msg = json.dumps({"type": "subscribe", "symbol": subscribed_symbol})
        ws.send(subscribe_msg)
        print(f"Sent subscription message: {subscribe_msg}")

def run_websocket():
    global ws_app
    websocket.enableTrace(True)
    ws_app = websocket.WebSocketApp("wss://ws.finnhub.io?token=d4c4hk1r01qoua32fpu0d4c4hk1r01qoua32fpug",
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    ws_app.on_open = on_open
    ws_app.run_forever()

def start_listening(symbol):
    global is_running, subscribed_symbol
    if not is_running:
        subscribed_symbol = symbol
        is_running = True
        t = threading.Thread(target=run_websocket)
        t.daemon = True
        t.start()

def stop_listening():
    global is_running, ws_app
    if is_running and ws_app:
        ws_app.close()
        is_running = False

st.title("Real-time Stock Price (WebSocket)")

# Input for ticker symbol
symbol = st.text_input("Enter Ticker Symbol (e.g., AAPL, BINANCE:BTCUSDT)", value="AAPL")

col1, col2 = st.columns(2)

with col1:
    if st.button("Subscribe"):
        start_listening(symbol)
        st.success(f"Subscribed to {symbol}")

with col2:
    if st.button("Stop"):
        stop_listening()
        st.warning("Stopped subscription")

# Placeholder for real-time data
placeholder = st.empty()

# Display data from the queue
if is_running:
    st.write(f"Listening for data for {subscribed_symbol}...")
    while is_running:
        try:
            # Non-blocking get
            data = data_queue.get(timeout=0.1)
            with placeholder.container():
                st.write(data) # Write raw data first to see structure
                if data.get('type') == 'trade':
                     st.dataframe(data.get('data'))
                else:
                     st.json(data)
        except queue.Empty:
            pass
        except Exception as e:
            st.error(f"Error: {e}")
        
        # Add a small sleep to prevent high CPU usage in the loop if queue is empty
        time.sleep(0.01)
