"""
市场数据获取模块
改为使用 Binance 公共API 获取实时价格与历史K线（严格真实，无任何模拟）。
"""

import time
import json
import requests
from typing import Dict, Any, List, Optional

from config import (
    CRYPTO_SYMBOLS,
    BINANCE_BASE_URLS,
    KLINE_INTERVAL,
    KLINE_LIMIT,
    PRICE_REFRESH_SECONDS,
)


class MarketData:
    def __init__(self):
        self.prices: Dict[str, float] = {}
        self.price_changes: Dict[str, float] = {}
        self.last_update: Dict[str, float] = {}  # 每个币种独立缓存时间

    # -------- Binance HTTP Helper --------
    def _binance_get(self, path: str, params: Dict[str, Any]) -> Any:
        last_exc: Optional[Exception] = None
        for base in BINANCE_BASE_URLS:
            url = f"{base}{path}"
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers={
                        'User-Agent': 'TrigoNexus/1.0',
                        'Accept': 'application/json'
                    },
                    timeout=15  # 增加超时时间
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                last_exc = e
                continue
        raise RuntimeError(f"Binance请求失败: {path} {params} -> {last_exc}")

    # -------- Futures (Perps) Helpers --------
    def _binance_fapi_get(self, path: str, params: Dict[str, Any]) -> Any:
        # Binance Futures base
        bases = [
            'https://fapi.binance.com',
            'https://fapi1.binance.com',
            'https://fapi2.binance.com',
            'https://fapi3.binance.com'
        ]
        last_exc: Optional[Exception] = None
        for base in bases:
            url = f"{base}{path}"
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers={
                        'User-Agent': 'TrigoNexus/1.0',
                        'Accept': 'application/json'
                    },
                    timeout=15
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                last_exc = e
                continue
        raise RuntimeError(f"Binance FAPI请求失败: {path} {params} -> {last_exc}")

    # -------- Backup: CoinGecko API --------
    def _get_price_from_coingecko(self, symbol: str) -> tuple[float, float]:
        """从 CoinGecko 获取价格（备选方案）"""
        coin_ids = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'SOL': 'solana',
            'BNB': 'binancecoin',
            'DOGE': 'dogecoin',
            'XRP': 'ripple'
        }
        coin_id = coin_ids.get(symbol)
        if not coin_id:
            raise ValueError(f"CoinGecko 不支持的币种: {symbol}")
        
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': coin_id,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            price = float(data[coin_id]['usd'])
            change_percent = float(data[coin_id].get('usd_24h_change', 0))
            return price, change_percent
        except Exception as e:
            raise RuntimeError(f"CoinGecko请求失败: {symbol} -> {e}")

    # -------- Realtime Prices --------
    def get_crypto_price(self, symbol: str) -> float:
        """获取单个加密货币的实时价格（Binance + CoinGecko 备选）"""
        current_time = time.time()
        # 每个币种独立缓存判断
        if symbol in self.prices and symbol in self.last_update and (current_time - self.last_update[symbol]) < PRICE_REFRESH_SECONDS:
            return self.prices[symbol]

        pair = CRYPTO_SYMBOLS.get(symbol)
        if not pair:
            raise ValueError(f"不支持的币种: {symbol}")

        # 先尝试 Binance
        try:
            data = self._binance_get('/api/v3/ticker/24hr', {'symbol': pair})
            price = float(data['lastPrice'])
            change_percent = float(data['priceChangePercent'])
            print(f"✓ {symbol} Binance价格: ${price:,.2f} ({change_percent:+.2f}%)")
        except Exception as e:
            # Binance 失败，切换到 CoinGecko
            print(f"⚠ {symbol} Binance失败，切换CoinGecko: {e}")
            try:
                price, change_percent = self._get_price_from_coingecko(symbol)
                print(f"✓ {symbol} CoinGecko价格: ${price:,.2f} ({change_percent:+.2f}%)")
            except Exception as e2:
                print(f"❌ {symbol} CoinGecko也失败: {e2}")
                raise

        self.prices[symbol] = price
        self.price_changes[symbol] = change_percent
        self.last_update[symbol] = current_time  # 每个币种独立时间戳
        return price

    def get_all_prices(self, force_refresh: bool = False) -> Dict[str, float]:
        if force_refresh:
            self.last_update = {}  # 清空所有币种的缓存
        prices: Dict[str, float] = {}
        for symbol in CRYPTO_SYMBOLS.keys():
            prices[symbol] = self.get_crypto_price(symbol)
        return prices

    def get_price_change(self, symbol: str) -> float:
        return self.price_changes.get(symbol, 0.0)

    # -------- Klines --------
    def get_historical_candles(self, symbol: str, days: int = 3) -> List[Dict[str, Any]]:
        """获取历史K线（严格真实）。默认取最近 KLINE_LIMIT 根 1m K线。"""
        pair = CRYPTO_SYMBOLS.get(symbol)
        if not pair:
            raise ValueError(f"不支持的币种: {symbol}")

        # 直接取最近 KLINE_LIMIT 根，满足前端和指标计算需求
        raw = self._binance_get('/api/v3/klines', {
            'symbol': pair,
            'interval': KLINE_INTERVAL,
            'limit': KLINE_LIMIT
        })

        candles: List[Dict[str, Any]] = []
        for k in raw:
            # Binance返回: [openTime, open, high, low, close, volume, closeTime, ...]
            candles.append({
                'timestamp': int(k[0]),           # 毫秒
                'open': float(k[1]),
                'high': float(k[2]),
                'low': float(k[3]),
                'close': float(k[4]),
                'volume': float(k[5])
            })

        print(f"✓ {symbol} Binance历史K线: {len(candles)} 根", flush=True)
        return candles

    # -------- Futures Metrics (OI & Funding) --------
    def get_open_interest(self, symbol: str) -> float:
        pair = CRYPTO_SYMBOLS.get(symbol)
        if not pair:
            return 0.0
        data = self._binance_fapi_get('/fapi/v1/openInterest', {'symbol': pair})
        try:
            return float(data.get('openInterest', 0.0))
        except Exception:
            return 0.0

    def get_open_interest_avg(self, symbol: str, period: str = '5m', limit: int = 30) -> float:
        pair = CRYPTO_SYMBOLS.get(symbol)
        if not pair:
            return 0.0
        # historical open interest series
        try:
            data = self._binance_fapi_get('/futures/data/openInterestHist', {
                'symbol': pair,
                'period': period,
                'limit': limit
            })
            if isinstance(data, list) and len(data) > 0:
                vals = [float(x.get('sumOpenInterest', x.get('sumOpenInterestValue', 0))) for x in data if x]
                if len(vals) > 0:
                    return sum(vals) / len(vals)
        except Exception:
            pass
        return 0.0

    def get_funding_rate(self, symbol: str) -> float:
        pair = CRYPTO_SYMBOLS.get(symbol)
        if not pair:
            return 0.0
        try:
            data = self._binance_fapi_get('/fapi/v1/fundingRate', {'symbol': pair, 'limit': 1})
            if isinstance(data, list) and len(data) > 0:
                return float(data[0].get('fundingRate', 0.0))
        except Exception:
            pass
        return 0.0

    def get_recent_klines(self, symbol: str, limit: int = 3) -> List[Dict[str, Any]]:
        pair = CRYPTO_SYMBOLS.get(symbol)
        if not pair:
            raise ValueError(f"不支持的币种: {symbol}")
        raw = self._binance_get('/api/v3/klines', {
            'symbol': pair,
            'interval': KLINE_INTERVAL,
            'limit': max(1, min(limit, 1000))
        })
        recent: List[Dict[str, Any]] = []
        for k in raw:
            recent.append({
                'timestamp': int(k[0]),
                'open': float(k[1]),
                'high': float(k[2]),
                'low': float(k[3]),
                'close': float(k[4]),
                'volume': float(k[5])
            })
        return recent

