# 配置文件
import os

# API 密钥（优先使用环境变量，方便部署）
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', "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")
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', "sk-79529efd5f434d8aa9eea08c17441096")  # 阿里云百炼 API for Qwen3
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', "d1ivl31r01qhbuvsiufgd1ivl31r01qhbuvsiug0")

# 交易配置
INITIAL_BALANCE = 100000  # 初始资金（美元）
# ⚡ 性能优化：降低更新频率，减少服务器压力
TRADING_INTERVAL = 2  # 交易间隔（秒）- 每2秒更新价格与持仓
NUM_AI_TRADERS = 5  # AI 交易员数量

# 支持的加密货币
SUPPORTED_CRYPTOS = ['BTC', 'ETH', 'SOL', 'BNB', 'DOGE', 'XRP']

# Binance 交易对映射（严格使用真实交易对，无前缀）
CRYPTO_SYMBOLS = {
    'BTC': 'BTCUSDT',
    'ETH': 'ETHUSDT',
    'SOL': 'SOLUSDT',
    'BNB': 'BNBUSDT',
    'DOGE': 'DOGEUSDT',
    'XRP': 'XRPUSDT'
}

# Binance 基础端点（自动降级切换）
BINANCE_BASE_URLS = [
    'https://api.binance.com',
    'https://api1.binance.com',
    'https://api2.binance.com',
    'https://api3.binance.com',
    'https://api4.binance.com'
]

# K线与价格刷新参数
KLINE_INTERVAL = '1m'
KLINE_LIMIT = 500  # 初始拉取根数
PRICE_REFRESH_SECONDS = 0.5  # 价格缓存0.5秒，接近实时

# AI 模型配置 - 最新版本
AI_MODELS = [
    {
        'id': 1,
        'name': 'QWEN3 MAX',
        'model': 'qwen/qwen3-vl-32b-instruct',  # Qwen3 VL 32B Instruct
        'strategy': 'aggressive'
    },
    {
        'id': 2,
        'name': 'DEEPSEEK V3.2',
        'model': 'deepseek/deepseek-v3.2-exp',  # DeepSeek V3.2
        'strategy': 'balanced'
    }
]

