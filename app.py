from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
import logging

app = FastAPI(title="Binance Futures Heikin Ashi API")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fetch Binance API URL from environment variables or use the default
BINANCE_API_URL = os.getenv("BINANCE_API_URL", "https://fapi.binance.com/fapi/v1/klines")

class CandleRequest(BaseModel):
    ticker: str
    interval: str  # e.g., '1m', '5m', '1h'
    limit: int     # Number of candles to retrieve

def calculate_heikin_ashi(candles):
    heikin_ashi = []
    ha_prev = {}
    for i, candle in enumerate(candles):
        open_price = float(candle[1])
        high = float(candle[2])
        low = float(candle[3])
        close_price = float(candle[4])

        if i == 0:
            # For the first candle, HA Open is (Open + Close) / 2
            ha_open = (open_price + close_price) / 2
            # HA Close is (Open + High + Low + Close) / 4
            ha_close = (open_price + high + low + close_price) / 4
        else:
            # HA Open is the average of the previous HA Open and HA Close
            ha_open = (ha_prev['open'] + ha_prev['close']) / 2
            # HA Close is the average of Open, High, Low, Close
            ha_close = (open_price + high + low + close_price) / 4

        # HA High is the maximum of High, HA Open, HA Close
        ha_high = max(high, ha_open, ha_close)
        # HA Low is the minimum of Low, HA Open, HA Close
        ha_low = min(low, ha_open, ha_close)

        ha = {
            'open': ha_open,
            'high': ha_high,
            'low': ha_low,
            'close': ha_close
        }
        heikin_ashi.append(ha)
        ha_prev = ha  # Update previous HA candle

    return heikin_ashi

@app.post("/heikin-ashi")
def get_heikin_ashi(request: CandleRequest):
    logger.info(f"Received request: {request}")
    params = {
        'symbol': request.ticker.upper(),
        'interval': request.interval,
        'limit': request.limit
    }

    response = requests.get(BINANCE_API_URL, params=params)
    logger.info(f"Binance API Response Status Code: {response.status_code}")

    if response.status_code != 200:
        # Log the full response for debugging
        logger.error(f"Binance API Error Response: {response.text}")
        raise HTTPException(status_code=400, detail="Error fetching data from Binance API")

    candles = response.json()
    heikin_ashi = calculate_heikin_ashi(candles)
    logger.info("Successfully calculated Heikin Ashi candles")

    return {"heikin_ashi_candles": heikin_ashi}
