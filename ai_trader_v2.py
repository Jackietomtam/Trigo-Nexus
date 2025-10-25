"""
AI交易代理 V2 - 支持杠杆交易和技术指标
"""

import requests
import json
import random
import time
try:
    # 可选依赖：若本地未安装 openai，也能回退到 requests 方案
    from openai import OpenAI  # type: ignore
    HAS_OPENAI = True
except Exception:  # noqa: BLE001 - 广泛捕获以确保运行时不因缺少依赖而中断
    OpenAI = None  # type: ignore
    HAS_OPENAI = False
from config import OPENROUTER_API_KEY, DASHSCOPE_API_KEY

class AITraderV2:
    """AI交易代理 - 杠杆版本"""
    
    def __init__(self, trader_id, name, strategy, model, leverage_engine, kline_data, order_manager):
        self.trader_id = trader_id
        self.name = name
        self.strategy = strategy
        self.model = model
        self.engine = leverage_engine
        self.kline_data = kline_data
        self.order_mgr = order_manager
        self.chat_history = []
        # 统计与时间
        self.start_ts = time.time()
        self.invocations = 0
        
    def make_decision(self):
        """做出交易决策"""
        try:
            self.invocations += 1
            print(f"  → {self.name} 开始获取账户...", flush=True)
            # 获取账户和持仓
            account = self.engine.get_account(self.trader_id)
            positions = self.engine.get_positions(self.trader_id)
            print(f"  → {self.name} 账户: ${account['total_value']:.2f}, 持仓数: {len(positions)}", flush=True)
            
            # 获取所有技术指标
            print(f"  → {self.name} 获取技术指标...", flush=True)
            all_indicators = self.kline_data.get_all_indicators()
            print(f"  → {self.name} 技术指标数量: {len(all_indicators) if all_indicators else 0}", flush=True)
            
            if not account:
                print(f"  ⚠ {self.name} 账户不存在", flush=True)
                return None
                
            if not all_indicators:
                print(f"  ⚠ {self.name} 技术指标不足，使用后备策略", flush=True)
                return self._fallback_decision(account, positions)
            
            # 生成详细的prompt
            print(f"  → {self.name} 构建prompt...", flush=True)
            prompt = self._build_detailed_prompt(account, positions, all_indicators)
            print(f"  → {self.name} prompt长度: {len(prompt)}", flush=True)
            
            # 节流：每3分钟最多一次决策/对话（不写入占位对话，避免"假对话"观感）
            now = time.time()
            if self.chat_history and (now - self.chat_history[-1]['timestamp'] < 180):
                return None

            # 调用AI
            print(f"  → {self.name} 调用AI模型: {self.model}...", flush=True)
            decision = self._call_ai(prompt)
            print(f"  → {self.name} AI返回: {decision}", flush=True)
            
            # 保存对话（包含prompt）
            self._save_chat(decision, account, positions, prompt)
            
            # 执行决策
            return self._execute_decision(decision, all_indicators, account, positions)
            
        except Exception as e:
            print(f"AI {self.name} 错误: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return self._fallback_decision(account if 'account' in locals() else None, 
                                          positions if 'positions' in locals() else {})
    
    def _build_detailed_prompt(self, account, positions, indicators):
        """构建详细的Alpha Arena风格prompt"""
        mins = int((time.time() - self.start_ts) / 60)
        now_str = time.strftime('%Y-%m-%d %H:%M:%S.%f', time.localtime())

        prompt = f"""It has been {mins} minutes since you started trading. The current time is {now_str} and you've been invoked {self.invocations} times. Below, we are providing you with a variety of state data, price data, and predictive signals so you can discover alpha. Below that is your current account information, value, performance, positions, etc.

ALL OF THE PRICE OR SIGNAL DATA BELOW IS ORDERED: OLDEST → NEWEST

Timeframes note: Unless stated otherwise in a section title, intraday series are provided at 3‑minute intervals. If a coin uses a different interval, it is explicitly stated in that coin's section.

CURRENT MARKET STATE FOR ALL COINS
"""
        
        # 技术指标（逐币种）
        import pandas as pd
        import pandas_ta as ta
        from market_data import MarketData
        mkt = MarketData()
        
        for symbol, ind in indicators.items():
            if not ind:
                continue
            
            # 扩展序列长度（从10条增加到30条，提供更多历史上下文）
            price_series = ind.get('price_series', [])
            ema20_series = ind.get('ema_20_series', []) if ind.get('ema_20') is not None else []
            macd_series = ind.get('macd_series', []) if ind.get('macd') is not None else []
            rsi7_series = ind.get('rsi_7_series', []) if ind.get('rsi_7') is not None else []
            rsi14_series = ind.get('rsi_14_series', []) if ind.get('rsi_14') is not None else []
            
            # 序列格式化（取最近30条，提供更丰富的历史数据）
            price_series_fmt = [round(p, 2) for p in price_series[-30:]]
            ema20_series_fmt = [round(e, 3) for e in ema20_series[-30:]]
            macd_series_fmt = [round(m, 3) for m in macd_series[-30:]]
            rsi7_series_fmt = [round(r, 3) for r in rsi7_series[-30:]]
            rsi14_series_fmt = [round(r, 3) for r in rsi14_series[-30:]]

            # 4小时聚合（完全对齐官方格式）
            df = self.kline_data.get_dataframe(symbol, 1500)
            long_ctx = ""
            if df is not None and len(df) > 0:
                try:
                    df4 = df.resample('240min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
                    if len(df4) >= 60:
                        df4.ta.ema(length=20, append=True)
                        df4.ta.ema(length=50, append=True)
                        df4.ta.atr(length=3, append=True)
                        df4.ta.atr(length=14, append=True)
                        macd4 = ta.macd(df4['close'], fast=12, slow=26, signal=9)
                        rsi4 = ta.rsi(df4['close'], length=14)
                        
                        ema20_4 = float(df4.iloc[-1].get('EMA_20', 0)) if 'EMA_20' in df4.columns else 0.0
                        ema50_4 = float(df4.iloc[-1].get('EMA_50', 0)) if 'EMA_50' in df4.columns else 0.0
                        atr3_4 = float(df4.iloc[-1].get('ATR_3', 0)) if 'ATR_3' in df4.columns else 0.0
                        atr14_4 = float(df4.iloc[-1].get('ATR_14', 0)) if 'ATR_14' in df4.columns else 0.0
                        vol_cur = float(df4.iloc[-1]['volume']) if 'volume' in df4.columns else 0.0
                        vol_avg = float(df4['volume'].tail(20).mean()) if 'volume' in df4.columns else 0.0
                        
                        # 扩展4小时序列（从10个增加到20个，覆盖80小时约3.3天）
                        macd4_series = [round(x, 3) for x in macd4['MACD_12_26_9'].dropna().tail(20).tolist()] if macd4 is not None and 'MACD_12_26_9' in macd4.columns else []
                        rsi4_series = [round(x, 3) for x in rsi4.dropna().tail(20).tolist()] if rsi4 is not None else []
                        
                        long_ctx = f"""
Longer‑term context (4‑hour timeframe):

20‑Period EMA: {ema20_4:.3f} vs. 50‑Period EMA: {ema50_4:.3f}

3‑Period ATR: {atr3_4:.3f} vs. 14‑Period ATR: {atr14_4:.3f}

Current Volume: {vol_cur:.3f} vs. Average Volume: {vol_avg:.3f}

MACD indicators: {macd4_series}

RSI indicators (14‑Period): {rsi4_series}
"""
                except Exception as e:
                    print(f"  ⚠ {symbol} 4小时数据生成失败: {e}", flush=True)
                    long_ctx = ""

            # 期货指标：OI、Funding Rate
            oi_latest = 0.0
            oi_avg = 0.0
            funding = 0.0
            try:
                oi_latest = mkt.get_open_interest(symbol)
                oi_avg = mkt.get_open_interest_avg(symbol, period='5m', limit=30)
                funding = mkt.get_funding_rate(symbol)
            except Exception:
                pass

            # 时间框架说明（BTC用1分钟，其他3分钟，或统一用3分钟）
            interval_note = "by minute" if symbol == 'BTC' else "3‑minute intervals"
            
            # 如果是BTC且用1分钟，需要特别说明
            symbol_section = f"""ALL {symbol} DATA
current_price = {ind['current_price']:.3f}, current_ema20 = {ind.get('ema_20', 0):.3f}, current_macd = {ind.get('macd', 0):.3f}, current_rsi (7 period) = {ind.get('rsi_7', 0):.3f}

In addition, here is the latest {symbol} open interest and funding rate for perps (the instrument you are trading):

Open Interest: Latest: {oi_latest:.2f} Average: {oi_avg:.2f}

Funding Rate: {funding}

Intraday series ({interval_note}, oldest → latest):

Mid prices: {price_series_fmt}

EMA indicators (20‑period): {ema20_series_fmt}

MACD indicators: {macd_series_fmt}

RSI indicators (7‑Period): {rsi7_series_fmt}

RSI indicators (14‑Period): {rsi14_series_fmt}
{long_ctx}"""
            
            prompt += symbol_section

        # 账户状态与绩效（增强版）
        total_fees = account.get('fees', 0)
        realized_pnl = account.get('realized_pnl', 0)
        margin_used = account.get('margin_used', 0)
        
        prompt += f"""
HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE
Current Total Return (percent): {account.get('profit_loss_percent', 0):.2f}%

Available Cash: {account.get('cash', 0):.2f}

Current Account Value: {account.get('total_value', 0):.2f}

Margin Used: {margin_used:.2f}

Total Fees Paid: {total_fees:.2f}

Realized P&L: {realized_pnl:.2f}
"""
        # 当前持仓（详细格式）
        if positions:
            prompt += f"\nCurrent live positions ({len(positions)} total):\n"
            for symbol, pos in positions.items():
                inv = pos.get('invalidation_condition', '').replace("'", "\\'") if 'invalidation_condition' in pos else ''
                pt = pos.get('profit_target', 0)
                sl = pos.get('stop_loss', 0)
                side = pos.get('side', 'long')
                entry_time = pos.get('entry_time', 0)
                
                prompt += f"""
  • {symbol} {side.upper()} {pos['leverage']}x
    Quantity: {pos['quantity']:.4f} | Entry: ${pos['entry_price']:.2f} | Current: ${pos['current_price']:.2f}
    Unrealized P&L: ${pos['unrealized_pnl']:.2f} | Liquidation: ${pos['liquidation_price']:.2f}
    Stop Loss: ${sl:.2f} | Profit Target: ${pt:.2f}
    Invalidation: {inv or 'None'}
    Confidence: {pos.get('confidence', 0.0):.0%} | Risk: ${pos.get('risk_usd', 0.0):.2f}
"""
        else:
            prompt += "\nNo current positions.\n"

        sharpe = account.get('sharpe', None)
        prompt += f"\nSharpe Ratio: {sharpe if sharpe is not None else 'N/A'}\n"
        
        # 不添加额外的输出格式说明，让AI自然响应
        
        return prompt
    
    def _call_ai(self, prompt):
        """调用AI API（Qwen用DashScope，DeepSeek用OpenRouter）"""
        try:
            # 根据模型选择API
            use_dashscope = 'qwen' in self.model.lower()
            
            if use_dashscope:
                # Qwen使用阿里云百炼 DashScope API（优先走OpenAI SDK；若未安装则回退requests）
                print(f"  → {self.name} 使用DashScope API", flush=True)
                if HAS_OPENAI and OpenAI is not None:
                    client = OpenAI(
                        api_key=DASHSCOPE_API_KEY,
                        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                    )
                    completion = client.chat.completions.create(
                        model="qwen3-max",
                        messages=[
                            {"role": "system", "content": f"You are {self.name}, a professional crypto trader. Analyze market data and return your decisions in this exact JSON format: {{\"analysis\": \"your 200-400 word market analysis\", \"decisions\": {{\"BTC\": {{\"signal\": \"hold/long/short\", \"leverage\": 10, \"percentage\": 20, \"confidence\": 0.75, \"stop_loss\": 0, \"profit_target\": 0, \"invalidation_condition\": \"\", \"risk_usd\": 0}}, \"ETH\": {{...}}}}}}. Include ALL coins (BTC, ETH, SOL, BNB, DOGE, XRP) in your response. Use 'hold' for no action."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.6,
                        max_tokens=2000,
                    )
                    content = completion.choices[0].message.content
                    response = type('obj', (object,), {'status_code': 200})()  # 模拟response对象
                    response_json = {'choices': [{'message': {'content': content}}]}
                else:
                    # 回退到requests（OpenAI SDK 未安装）
                    r = requests.post(
                        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "qwen3-max",
                            "messages": [
                                {"role": "system", "content": f"You are {self.name}, a professional crypto trader. Analyze market data and return your decisions in this exact JSON format: {{\"analysis\": \"your 200-400 word market analysis\", \"decisions\": {{\"BTC\": {{\"signal\": \"hold/long/short\", \"leverage\": 10, \"percentage\": 20, \"confidence\": 0.75, \"stop_loss\": 0, \"profit_target\": 0, \"invalidation_condition\": \"\", \"risk_usd\": 0}}, \"ETH\": {{...}}}}}}. Include ALL coins (BTC, ETH, SOL, BNB, DOGE, XRP) in your response. Use 'hold' for no action."},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.6,
                            "max_tokens": 2000
                        },
                        timeout=30
                    )
                    response = type('obj', (object,), {'status_code': r.status_code})()
                    response_json = r.json() if r.status_code == 200 else {}
            else:
                # DeepSeek使用OpenRouter
                print(f"  → {self.name} 使用OpenRouter API", flush=True)
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": f"You are {self.name}, a professional crypto trader. Analyze market data and return your decisions in this exact JSON format: {{\"analysis\": \"your 200-400 word market analysis\", \"decisions\": {{\"BTC\": {{\"signal\": \"hold/long/short\", \"leverage\": 10, \"percentage\": 20, \"confidence\": 0.75, \"stop_loss\": 0, \"profit_target\": 0, \"invalidation_condition\": \"\", \"risk_usd\": 0}}, \"ETH\": {{...}}}}}}. Include ALL coins (BTC, ETH, SOL, BNB, DOGE, XRP) in your response. Use 'hold' for no action."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 2000
                    },
                    timeout=30
                )
                response_json = response.json()
            
            # 统一处理返回内容
            if response.status_code == 200:
                content = response_json['choices'][0]['message']['content']
                print(f"  → {self.name} API原始返回长度: {len(content)}", flush=True)
                print(f"  → {self.name} 返回前100字: {content[:100]}", flush=True)
                
                # 清理Markdown代码块
                cleaned = content
                if '```' in content:
                    parts = content.split('```')
                    for i, part in enumerate(parts):
                        if i % 2 == 1:  # 代码块内部
                            # 移除语言标识
                            lines = part.split('\n')
                            if lines and lines[0].strip() in ['json', 'JSON', 'javascript']:
                                part = '\n'.join(lines[1:])
                            cleaned = part
                            break
                
                # 查找JSON
                if '{' in cleaned and '}' in cleaned:
                    try:
                        start = cleaned.index('{')
                        end = cleaned.rindex('}') + 1
                        json_str = cleaned[start:end]
                        data = json.loads(json_str)
                        
                        # 提取摘要（JSON之前的部分）
                        summary = content[:content.index('{')].strip() if '{' in content else ''
                        
                        if isinstance(data, dict):
                            # 确保analysis存在
                            if not data.get('analysis'):
                                data['analysis'] = summary[:600] if summary else 'Market analysis completed.'
                            print(f"  ✓ {self.name} JSON解析成功: {data.get('action', 'unknown')}", flush=True)
                            return data
                    except json.JSONDecodeError as e:
                        print(f"  ✗ {self.name} JSON解析失败: {e}", flush=True)
                        print(f"  → 尝试解析的内容: {json_str[:200]}", flush=True)
                    except Exception as e:
                        print(f"  ✗ {self.name} 处理错误: {e}", flush=True)
                
                print(f"  ✗ {self.name} 未找到有效JSON", flush=True)
                return None
            else:
                print(f"  ✗ {self.name} API返回状态码: {response.status_code}", flush=True)
                return None
            
        except Exception as e:
            print(f"AI API调用失败: {e}", flush=True)
            return None
    
    def _fallback_decision(self, account, positions):
        """后备决策 - 用户要求不使用预设/占位，直接跳过"""
        print(f"  → {self.name} 技术指标不足，跳过AI调用与占位对话", flush=True)
        return None
    
    def _execute_fallback(self, decision, account):
        """执行后备决策"""
        from market_data import MarketData
        market = MarketData()
        
        symbol = decision['symbol']
        leverage = decision['leverage']
        percentage = decision['percentage']
        
        # 获取当前价格
        current_price = market.get_crypto_price(symbol)
        if not current_price:
            print(f"  ✗ {self.name} 无法获取{symbol}价格", flush=True)
            return None
        
        available = account['cash'] - account['margin_used']
        invest = available * (percentage / 100)
        quantity = (invest * leverage) / current_price
        
        # 计算止盈止损
        profit_target = current_price * 1.08
        stop_loss = current_price * 0.95
        
        print(f"  → {self.name} 开仓: {symbol} {quantity:.4f} @{current_price} {leverage}x", flush=True)
        
        result = self.engine.open_position(
            self.trader_id, symbol, 'long', quantity, current_price, leverage,
            profit_target=profit_target, stop_loss=stop_loss,
            invalidation_condition=f"价格跌破 ${stop_loss:.2f}",
            confidence=0.6, risk_usd=invest * 0.05,
            reason=decision.get('reason', '')
        )
        
        if result.get('success'):
            print(f"  ✓ {self.name} 开仓成功！", flush=True)
            # 创建止损止盈单
            self.order_mgr.create_stop_loss(self.trader_id, symbol, stop_loss)
            self.order_mgr.create_take_profit(self.trader_id, symbol, profit_target)
            
            # 保存对话
            chat = {
                'timestamp': time.time(),
                'datetime': time.strftime('%m/%d %H:%M:%S'),
                'trader': self.name,
                'model': self.model,
                'analysis': decision['analysis'],
                'total_value': account['total_value'],
                'profit_loss_percent': account['profit_loss_percent'],
                'cash': account['cash'],
                'positions': symbol
            }
            self.chat_history.append(chat)
        
        return result
    
    def _execute_decision(self, decision, indicators, account, positions):
        """执行AI决策（支持多币种格式）"""
        if not decision:
            return None
        
        # 处理多币种格式: {"analysis": "...", "decisions": {"BTC": {...}, "ETH": {...}}}
        if 'decisions' in decision and isinstance(decision['decisions'], dict):
            print(f"  → {self.name} 检测到多币种决策，共{len(decision['decisions'])}个币种", flush=True)
            results = []
            for symbol, trade_data in decision['decisions'].items():
                # 构造交易对象
                trade = {
                    'symbol': symbol,
                    'action': trade_data.get('signal', 'hold'),
                    'leverage': trade_data.get('leverage', 10),
                    'percentage': trade_data.get('percentage', 20),
                    'confidence': trade_data.get('confidence', 0.7),
                    'stop_loss': trade_data.get('stop_loss', 0),
                    'profit_target': trade_data.get('profit_target', 0),
                    'invalidation_condition': trade_data.get('invalidation_condition', ''),
                    'risk_usd': trade_data.get('risk_usd', 0),
                    'reason': decision.get('analysis', '')[:200]  # 使用总体分析作为reason
                }
                result = self._execute_single_trade(trade, indicators, account, positions)
                if result:
                    results.append(result)
            return results if results else None
        
        # 单个交易格式（向后兼容）
        return self._execute_single_trade(decision, indicators, account, positions)
    
    def _execute_single_trade(self, trade, indicators, account, positions):
        """执行单个交易"""
        action = trade.get('action', 'hold').lower()
        symbol = trade.get('symbol', 'BTC')
        
        # 转换交易对格式：BTCUSDT -> BTC, SOLUSDT -> SOL
        if symbol.endswith('USDT'):
            symbol = symbol[:-4]
        
        if action == 'hold':
            return None
        
        # 获取当前价格
        if symbol not in indicators:
            print(f"  ⚠ {self.name} symbol {symbol} 不在indicators中", flush=True)
            return None
        
        current_price = indicators[symbol]['current_price']
        
        if action in ['buy', 'long']:
            # 开多仓
            leverage = trade.get('leverage', 10)
            percentage = trade.get('percentage', 20)
            confidence = trade.get('confidence', 0.7)
            
            available = account['cash'] - account['margin_used']
            invest = available * (percentage / 100)
            quantity = (invest * leverage) / current_price
            
            # 使用AI提供的止盈止损，或使用默认值
            profit_target = trade.get('profit_target', 0)
            stop_loss = trade.get('stop_loss', 0)
            if profit_target == 0:
                profit_target = current_price * 1.1
            if stop_loss == 0:
                stop_loss = current_price * 0.95
            
            invalidation = trade.get('invalidation_condition', '') or f"价格跌破 ${stop_loss:.2f}"
            risk_usd = trade.get('risk_usd', 0) or invest * 0.05
            
            print(f"  → {self.name} 准备开多: {symbol} {leverage}x (止盈:{profit_target:.2f}, 止损:{stop_loss:.2f})", flush=True)
            
            result = self.engine.open_position(
                self.trader_id, symbol, 'long', quantity, current_price, leverage,
                profit_target=profit_target, stop_loss=stop_loss,
                invalidation_condition=invalidation,
                confidence=confidence, risk_usd=risk_usd,
                reason=trade.get('reason', '')
            )
            
            if result.get('success'):
                print(f"  ✓ {self.name} 开多成功！", flush=True)
                # 创建止损止盈单
                self.order_mgr.create_stop_loss(self.trader_id, symbol, stop_loss)
                self.order_mgr.create_take_profit(self.trader_id, symbol, profit_target)
            
            return result
        
        elif action in ['sell_short', 'short']:
            # 开空仓
            leverage = trade.get('leverage', 10)
            percentage = trade.get('percentage', 20)
            confidence = trade.get('confidence', 0.7)
            
            available = account['cash'] - account['margin_used']
            invest = available * (percentage / 100)
            quantity = (invest * leverage) / current_price
            
            # 使用AI提供的止盈止损，或使用默认值（空仓反向）
            profit_target = trade.get('profit_target', 0)
            stop_loss = trade.get('stop_loss', 0)
            if profit_target == 0:
                profit_target = current_price * 0.9   # 价格下跌10%止盈
            if stop_loss == 0:
                stop_loss = current_price * 1.05      # 价格上涨5%止损
            
            invalidation = trade.get('invalidation_condition', '') or f"价格突破 ${stop_loss:.2f}"
            risk_usd = trade.get('risk_usd', 0) or invest * 0.05
            
            print(f"  → {self.name} 准备开空: {symbol} {leverage}x (止盈:{profit_target:.2f}, 止损:{stop_loss:.2f})", flush=True)
            
            result = self.engine.open_position(
                self.trader_id, symbol, 'short', quantity, current_price, leverage,
                profit_target=profit_target, stop_loss=stop_loss,
                invalidation_condition=invalidation,
                confidence=confidence, risk_usd=risk_usd,
                reason=trade.get('reason', '')
            )
            
            if result.get('success'):
                print(f"  ✓ {self.name} 开空成功！", flush=True)
                # 创建止损止盈单
                self.order_mgr.create_stop_loss(self.trader_id, symbol, stop_loss)
                self.order_mgr.create_take_profit(self.trader_id, symbol, profit_target)
            
            return result
        
        elif action == 'close' and symbol in positions:
            # 平仓
            print(f"  → {self.name} 准备平仓: {symbol}", flush=True)
            return self.engine.close_position(self.trader_id, symbol, current_price, 
                                            reason=trade.get('reason', ''))
        
        return None
    
    def _save_chat(self, decision, account, positions, prompt=""):
        """保存AI对话 - 包含完整的输入输出"""
        if not decision:
            return
        
        analysis = decision.get('analysis', '分析中...')
        
        positions_text = ""
        for symbol in positions.keys():
            positions_text += f"{symbol} "
        
        # 添加当前持仓数量到decisions（nof1.ai格式）
        if 'decisions' in decision and isinstance(decision['decisions'], dict):
            for symbol in decision['decisions'].keys():
                if symbol in positions:
                    decision['decisions'][symbol]['quantity'] = positions[symbol].get('quantity', 0)
                else:
                    decision['decisions'][symbol]['quantity'] = 0
        
        # 保存完整的对话上下文
        chat = {
            'timestamp': time.time(),
            'datetime': time.strftime('%m/%d %H:%M:%S'),
            'trader': self.name,
            'model': self.model,
            'analysis': analysis,  # AI的分析（输出）
            'user_prompt': prompt,  # 给AI的完整prompt（输入）
            'trading_decision': decision,  # AI的完整决策
            'total_value': account['total_value'],
            'profit_loss_percent': account['profit_loss_percent'],
            'cash': account['cash'],
            'positions': positions_text.strip()
        }
        
        self.chat_history.append(chat)
        if len(self.chat_history) > 30:
            self.chat_history = self.chat_history[-30:]
        
        print(f"💬 {self.name}: {analysis[:80]}...", flush=True)

