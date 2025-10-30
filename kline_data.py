"""
K线数据管理模块
获取、存储和计算技术指标
"""

import pandas as pd
from collections import deque
import time

class KLineData:
    """K线数据管理类"""
    
    def __init__(self, market_data):
        self.market_data = market_data
        self.klines = {}  # {symbol: deque of price points}
        self.max_length = 500  # 保留最近500个数据点
        self.initialized = False
        
    def initialize_historical_data(self):
        """初始化历史K线数据（Binance 真实K线，失败则模拟）"""
        print("📊 初始化历史K线（Binance真实数据）...", flush=True)
        from config import CRYPTO_SYMBOLS
        for symbol in CRYPTO_SYMBOLS.keys():
            print(f"  拉取 {symbol} 历史K线...", flush=True)
            try:
                historical = self.market_data.get_historical_candles(symbol, days=3)
                if historical and len(historical) > 0:
                    self.klines[symbol] = deque(historical, maxlen=self.max_length)
                    print(f"  ✓ {symbol}: {len(historical)} 根K线", flush=True)
                else:
                    # Binance失败，使用Finnhub模拟
                    self._simulate_klines_from_price(symbol)
            except Exception as e:
                print(f"  ⚠️ {symbol}: Binance失败 ({str(e)[:50]}), 使用Finnhub价格模拟", flush=True)
                self._simulate_klines_from_price(symbol)
        
        self.initialized = True
        print("✓ 历史K线初始化完成", flush=True)
    
    def _simulate_klines_from_price(self, symbol):
        """使用Finnhub当前价格模拟K线数据"""
        try:
            price_data = self.market_data.get_crypto_price(symbol)
            current_price = price_data[0] if isinstance(price_data, tuple) else price_data
            # 模拟500个K线点，价格在±2%范围内波动
            import random
            current_time = int(time.time() * 1000)
            simulated = []
            for i in range(500):
                ts = current_time - (500 - i) * 60000  # 每分钟一个
                variation = random.uniform(0.98, 1.02)
                price = current_price * variation
                simulated.append({
                    'timestamp': ts,
                    'open': price,
                    'high': price * 1.001,
                    'low': price * 0.999,
                    'close': price,
                    'volume': 1000000
                })
            self.klines[symbol] = deque(simulated, maxlen=self.max_length)
            print(f"  ✓ {symbol}: 已模拟500根K线（基于Finnhub价格${current_price:.2f}）", flush=True)
        except Exception as e:
            print(f"  ✗ {symbol}: 模拟K线失败: {e}", flush=True)
            self.klines[symbol] = deque(maxlen=self.max_length)
    
    def update_klines(self):
        """更新K线数据 - 添加最新价格"""
        # 首次调用时初始化历史数据
        if not self.initialized:
            self.initialize_historical_data()
        
        # 直接从Binance取最近几根真实K线并追加（去重）
        from config import CRYPTO_SYMBOLS
        for symbol in CRYPTO_SYMBOLS.keys():
            try:
                recent = self.market_data.get_recent_klines(symbol, limit=2)
                if symbol not in self.klines:
                    self.klines[symbol] = deque(maxlen=self.max_length)
                # 仅在时间戳比最后一条更新时追加
                last_ts = self.klines[symbol][-1]['timestamp'] if len(self.klines[symbol]) else None
                for c in recent:
                    if (last_ts is None) or (c['timestamp'] > last_ts):
                        self.klines[symbol].append(c)
            except Exception as e:
                # Binance失败，使用Finnhub价格追加模拟K线
                try:
                    price_data = self.market_data.get_crypto_price(symbol)
                    current_price = price_data[0] if isinstance(price_data, tuple) else price_data
                    current_time = int(time.time() * 1000)
                    if symbol not in self.klines:
                        self.klines[symbol] = deque(maxlen=self.max_length)
                    
                    # 追加一个新的模拟K线点
                    last_ts = self.klines[symbol][-1]['timestamp'] if len(self.klines[symbol]) else 0
                    if current_time > last_ts:
                        self.klines[symbol].append({
                            'timestamp': current_time,
                            'open': current_price,
                            'high': current_price * 1.001,
                            'low': current_price * 0.999,
                            'close': current_price,
                            'volume': 1000000
                        })
                except Exception as e2:
                    pass  # 静默失败，不打印太多错误
    
    def get_dataframe(self, symbol, periods=100):
        """获取指定币种的DataFrame"""
        if symbol not in self.klines or len(self.klines[symbol]) < 2:
            return None
        
        data = list(self.klines[symbol])[-periods:]
        df = pd.DataFrame(data)
        # Binance 返回的 openTime 为毫秒时间戳
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def calculate_indicators(self, symbol):
        """计算所有技术指标"""
        df = self.get_dataframe(symbol, 200)
        if df is None or len(df) < 20:  # 降低最小要求从50到20
            return None
        
        # 计算指标（纯 pandas 实现）
        # EMA
        df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
        
        # MACD
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD_12_26_9'] = ema12 - ema26
        df['MACDs_12_26_9'] = df['MACD_12_26_9'].ewm(span=9, adjust=False).mean()
        df['MACDh_12_26_9'] = df['MACD_12_26_9'] - df['MACDs_12_26_9']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
        rs = gain / loss
        df['RSI_7'] = 100 - (100 / (1 + rs))
        
        gain14 = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss14 = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs14 = gain14 / loss14
        df['RSI_14'] = 100 - (100 / (1 + rs14))
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATRr_3'] = tr.rolling(window=3).mean()
        df['ATRr_14'] = tr.rolling(window=14).mean()
        
        # 获取最新值
        latest = df.iloc[-1]
        
        indicators = {
            'current_price': latest['close'],
            'ema_20': latest.get('EMA_20', None),
            'ema_50': latest.get('EMA_50', None),
            'macd': latest.get('MACD_12_26_9', None),
            'macd_signal': latest.get('MACDs_12_26_9', None),
            'macd_hist': latest.get('MACDh_12_26_9', None),
            'rsi_7': latest.get('RSI_7', None),
            'rsi_14': latest.get('RSI_14', None),
            'atr_3': latest.get('ATR_3', None),
            'atr_14': latest.get('ATR_14', None),
            'volume': latest.get('volume', 0)
        }
        
        # 计算一些序列（用于AI分析）- 扩展到30个数据点
        recent_30 = df.tail(30)
        indicators['price_series'] = recent_30['close'].tolist()
        
        if 'EMA_20' in recent_30.columns:
            indicators['ema_20_series'] = recent_30['EMA_20'].tolist()
        if 'MACD_12_26_9' in recent_30.columns:
            indicators['macd_series'] = recent_30['MACD_12_26_9'].tolist()
        if 'RSI_7' in recent_30.columns:
            indicators['rsi_7_series'] = recent_30['RSI_7'].tolist()
        if 'RSI_14' in recent_30.columns:
            indicators['rsi_14_series'] = recent_30['RSI_14'].tolist()
        
        return indicators
    
    def get_all_indicators(self):
        """获取所有币种的技术指标"""
        all_indicators = {}
        for symbol in self.klines.keys():
            indicators = self.calculate_indicators(symbol)
            if indicators:
                all_indicators[symbol] = indicators
        return all_indicators

