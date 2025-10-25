"""
技术指标计算模块
实现 EMA、MACD、RSI、ATR 等指标
"""

class TechnicalIndicators:
    """技术指标计算类"""
    
    @staticmethod
    def ema(prices, period):
        """计算指数移动平均线"""
        if len(prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema_values = [sum(prices[:period]) / period]  # 初始SMA
        
        for price in prices[period:]:
            ema = (price * multiplier) + (ema_values[-1] * (1 - multiplier))
            ema_values.append(ema)
        
        return ema_values[-1]
    
    @staticmethod
    def ema_series(prices, period):
        """计算EMA序列"""
        if len(prices) < period:
            return []
        
        multiplier = 2 / (period + 1)
        ema_values = [sum(prices[:period]) / period]
        
        for price in prices[period:]:
            ema = (price * multiplier) + (ema_values[-1] * (1 - multiplier))
            ema_values.append(ema)
        
        return ema_values
    
    @staticmethod
    def macd(prices, fast=12, slow=26, signal=9):
        """计算MACD指标"""
        if len(prices) < slow:
            return None, None, None
        
        ema_fast = TechnicalIndicators.ema_series(prices, fast)
        ema_slow = TechnicalIndicators.ema_series(prices, slow)
        
        # MACD线 = 快线 - 慢线
        macd_line = []
        start_idx = slow - fast
        for i in range(len(ema_slow)):
            macd_line.append(ema_fast[i + start_idx] - ema_slow[i])
        
        # 信号线
        if len(macd_line) < signal:
            return macd_line[-1] if macd_line else None, None, None
        
        signal_line = TechnicalIndicators.ema_series(macd_line, signal)
        
        # 柱状图
        histogram = []
        start_idx = len(macd_line) - len(signal_line)
        for i in range(len(signal_line)):
            histogram.append(macd_line[i + start_idx] - signal_line[i])
        
        return (macd_line[-1], 
                signal_line[-1] if signal_line else None,
                histogram[-1] if histogram else None)
    
    @staticmethod
    def rsi(prices, period=14):
        """计算RSI指标"""
        if len(prices) < period + 1:
            return None
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            gains.append(change if change > 0 else 0)
            losses.append(abs(change) if change < 0 else 0)
        
        if len(gains) < period:
            return None
        
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        # 平滑处理后续值
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def rsi_series(prices, period=14):
        """计算RSI序列"""
        if len(prices) < period + 1:
            return []
        
        rsi_values = []
        
        for i in range(period, len(prices)):
            rsi_val = TechnicalIndicators.rsi(prices[:i+1], period)
            if rsi_val is not None:
                rsi_values.append(rsi_val)
        
        return rsi_values
    
    @staticmethod
    def atr(highs, lows, closes, period=14):
        """计算平均真实波幅"""
        if len(closes) < period + 1:
            return None
        
        true_ranges = []
        for i in range(1, len(closes)):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            tr = max(high_low, high_close, low_close)
            true_ranges.append(tr)
        
        if len(true_ranges) < period:
            return None
        
        # 初始ATR
        atr_val = sum(true_ranges[:period]) / period
        
        # 平滑
        for i in range(period, len(true_ranges)):
            atr_val = (atr_val * (period - 1) + true_ranges[i]) / period
        
        return atr_val



