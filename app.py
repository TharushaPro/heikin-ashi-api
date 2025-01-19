# app.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os

app = FastAPI(title="Binance Futures Heikin Ashi API")

BINANCE_API_URL = "https://fapi.binance.com/fapi/v1/klines"

class CandleRequest(BaseModel):
    ticker: str
    interval: str  # e.g., '1m', '5m', '1h'
    limit: int     # Number of candles to retrieve

def calculate_heikin_ashi(candles):
    heikin_ashi = []
    for i, candle in enumerate(candles):
        open_price = float(candle[1])
        high = float(candle[2])
        low = float(candle[3])
        close_price = float(candle[4])

        if i == 0:
            ha_close = (open_price + high + low + close_price) / 4
            ha_open = (open_price + close_price) / 2
        else:
            ha_close = (open_prev['open'] + open_prev['close'] + open_prev['high'] + open_prev['low']) / 4
            ha_open = (ha_prev['open'] + ha_prev['close']) / 2

        ha = {
            'open': ha_open,
            'high': high,
            'low': low,
            'close': ha_close
        }
        heikin_ashi.append(ha)
        ha_prev = ha
    return heikin_ashi

@app.post("/heikin-ashi")
def get_heikin_ashi(request: CandleRequest):
    params = {
        'symbol': request.ticker.upper(),
        'interval': request.interval,
        'limit': request.limit
    }

    response = requests.get(BINANCE_API_URL, params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Error fetching data from Binance API")

    candles = response.json()
    heikin_ashi = calculate_heikin_ashi(candles)

    return {"heikin_ashi_candles": heikin_ashi}
