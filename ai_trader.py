"""
AI 交易代理
使用 OpenRouter API 进行交易决策
"""

import requests
import json
import random
import time
import datetime
from config import OPENROUTER_API_KEY

class AITrader:
    def __init__(self, trader_id, name, strategy, model, personality, trading_engine, market_data):
        self.trader_id = trader_id
        self.name = name
        self.strategy = strategy
        self.model = model  # 每个AI使用不同的模型
        self.personality = personality
        self.trading_engine = trading_engine
        self.market_data = market_data
        self.last_decision_time = 0
        self.decision_cooldown = 30  # 决策冷却时间（秒）
        self.chat_history = []  # AI的思考和对话历史
        
    def make_trading_decision(self):
        """使用 AI 做出交易决策，生成详细的思考过程"""
        try:
            # 获取当前市场数据
            current_prices = self.market_data.get_all_prices()
            account = self.trading_engine.get_account(self.trader_id)
            
            if not account or not current_prices:
                return None
            
            # 准备市场情况摘要
            market_summary = self._prepare_market_summary(current_prices, account)
            
            # 调用 AI 获取决策和详细分析
            print(f"    调用AI模型: {self.model}", flush=True)
            decision, analysis = self._get_ai_decision_with_analysis(market_summary, current_prices, account)
            print(f"    AI返回决策: {decision.get('action') if decision else 'None'}", flush=True)
            
            # 保存AI的分析到聊天历史
            if analysis:
                self._add_analysis_to_chat(analysis, account, current_prices)
            
            if decision:
                # 执行决策
                return self._execute_decision(decision, current_prices)
            
            return None
            
        except Exception as e:
            print(f"AI {self.name} 决策错误: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return None
    
    def _prepare_market_summary(self, prices, account):
        """准备市场情况摘要"""
        summary = f"""
策略类型: {self.strategy}
账户余额: ${account['balance']:.2f}
总资产价值: ${account['total_value']:.2f}
盈亏: ${account['profit_loss']:.2f} ({account['profit_loss_percent']:.2f}%)

当前持仓:
"""
        if account['positions']:
            for symbol, amount in account['positions'].items():
                if symbol in prices:
                    value = amount * prices[symbol]
                    summary += f"- {symbol}: {amount:.6f} (价值: ${value:.2f})\n"
        else:
            summary += "无持仓\n"
        
        summary += "\n当前市场价格:\n"
        for symbol, price in prices.items():
            change = self.market_data.get_price_change(symbol)
            summary += f"- {symbol}: ${price:.2f} ({change:+.2f}%)\n"
        
        return summary
    
    def _get_ai_decision_with_analysis(self, market_summary, current_prices, account):
        """调用 AI 获取决策和详细分析"""
        try:
            # 构建详细的分析请求
            system_prompt = self._get_strategy_prompt()
            user_prompt = f"""
作为 {self.name}，请分析当前市场情况并做出交易决策。

{market_summary}

请提供：
1. 你的详细市场分析和想法（用第一人称，像在对话一样）
2. 你的交易决策

格式要求：
第一部分：用2-3句话详细说明你的分析，包括：
- 你的总体表现（盈亏百分比）
- 当前持仓状态
- 市场观察和决策理由

第二部分：在新行开始，用JSON格式提供决策：
{{
    "action": "buy" / "sell" / "hold",
    "symbol": "币种符号",
    "percentage": 10-30,
    "reason": "简短理由"
}}

例如：
My portfolio is up 25% with $12,500 in value. I'm holding BTC and ETH positions, both showing positive momentum. The market looks bullish, so I'm maintaining my current positions.
{{"action": "hold", "symbol": "BTC", "percentage": 0, "reason": "Maintaining positions"}}
"""
            
            # 调用 OpenRouter API - 使用该AI特定的模型
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,  # 每个AI使用不同的模型
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.8,
                    "max_tokens": 300
                },
                timeout=15  # 减少超时时间
            )
            
            print(f"      API响应: {response.status_code}", flush=True)
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # 分离分析文本和JSON决策
                analysis_text = ""
                decision_json = ""
                
                # 尝试找到JSON部分
                if '{' in content:
                    parts = content.split('{', 1)
                    analysis_text = parts[0].strip()
                    decision_json = '{' + parts[1]
                    
                    # 清理JSON
                    if decision_json.startswith('```'):
                        decision_json = decision_json.split('\n', 1)[1]
                    if decision_json.endswith('```'):
                        decision_json = decision_json.rsplit('```', 1)[0]
                    
                    decision = json.loads(decision_json.strip())
                    return decision, analysis_text
                else:
                    # 没有找到JSON，使用简单策略
                    return self._simple_strategy_decision(market_summary), content
            else:
                print(f"API 错误: {response.status_code}")
                return self._simple_strategy_decision(market_summary), ""
                
        except Exception as e:
            print(f"AI 决策调用错误: {e}")
            return self._simple_strategy_decision(market_summary), ""
    
    def _add_analysis_to_chat(self, analysis, account, current_prices):
        """将AI的分析添加到聊天历史"""
        
        # 构建详细的分析消息
        positions_text = ""
        if account['positions']:
            for symbol, amount in account['positions'].items():
                if symbol in current_prices:
                    value = amount * current_prices[symbol]
                    positions_text += f"{symbol} "
        
        chat_message = {
            'timestamp': time.time(),
            'datetime': datetime.datetime.now().strftime('%m/%d %H:%M:%S'),
            'trader': self.name,
            'model': self.model,
            'analysis': analysis if analysis else f"My account is at ${account['total_value']:.2f} with {account['profit_loss_percent']:+.2f}% return. {'Holding positions in ' + positions_text if positions_text else 'No current positions.'}",
            'total_value': account['total_value'],
            'profit_loss_percent': account['profit_loss_percent'],
            'cash': account['balance'],
            'positions': positions_text.strip()
        }
        
        self.chat_history.append(chat_message)
        
        # 只保留最近30条
        if len(self.chat_history) > 30:
            self.chat_history = self.chat_history[-30:]
        
        print(f"💬 {self.name}: {analysis[:100] if analysis else 'Analyzing...'}")
    
    def _get_ai_decision(self, market_summary):
        """保留原方法以兼容"""
        decision, _ = self._get_ai_decision_with_analysis(market_summary, {}, {})
        return decision
    
    def _get_strategy_prompt(self):
        """根据策略类型返回系统提示"""
        base_prompt = f"""你是 {self.name}，{self.personality}

你的交易策略是：{self.strategy}

在做出决策时，你需要：
1. 分析当前市场状况
2. 根据你的策略特点进行判断
3. 在回答中包含你的思考过程
4. 表现出你独特的个性和风格

你的模型是：{self.model}"""

        strategy_details = {
            'aggressive': '作为激进型交易员，你追求高收益，愿意承担较高风险。倾向于频繁交易和大额投资。',
            'conservative': '作为保守型交易员，你注重风险控制和资本保护。偏好稳定币种，避免过度交易。',
            'scalping': '作为剥头皮交易员，你专注于小额频繁交易，从小幅价格波动中获利。',
            'momentum': '作为动量交易员，你追踪市场趋势，在上涨趋势中买入，下跌趋势中卖出。',
            'arbitrage': '作为套利交易员，你寻找不同币种之间的价格差异和机会。'
        }
        
        return base_prompt + "\n\n" + strategy_details.get(self.strategy, '')
    
    def _simple_strategy_decision(self, market_summary):
        """简单的后备策略"""
        actions = ['buy', 'sell', 'hold']
        symbols = ['BTC', 'ETH', 'SOL', 'BNB', 'DOGE', 'XRP']
        
        # 提高交易频率，便于实时展示
        if self.strategy == 'aggressive':
            action_weights = [0.5, 0.4, 0.1]
            percentage = random.randint(20, 35)
        elif self.strategy == 'conservative':
            action_weights = [0.35, 0.35, 0.3]
            percentage = random.randint(10, 20)
        else:  # scalping / momentum / arbitrage
            action_weights = [0.45, 0.45, 0.1]
            percentage = random.randint(15, 30)
        
        action = random.choices(actions, weights=action_weights)[0]
        
        return {
            'action': action,
            'symbol': random.choice(symbols),
            'percentage': percentage,
            'reason': f'{self.strategy} 策略自动决策'
        }
    
    def _execute_decision(self, decision, current_prices):
        """执行交易决策"""
        action = decision.get('action')
        symbol = decision.get('symbol')
        percentage = decision.get('percentage', 20)
        reason = decision.get('reason', '无')
        
        # 添加到聊天历史
        chat_message = {
            'timestamp': time.time(),
            'trader': self.name,
            'action': action,
            'symbol': symbol,
            'reason': reason,
            'percentage': percentage
        }
        self.chat_history.append(chat_message)
        
        # 只保留最近20条记录
        if len(self.chat_history) > 20:
            self.chat_history = self.chat_history[-20:]
        
        if action == 'hold':
            print(f"💬 {self.name}: 持有 - {reason}")
            return {
                'trader': self.name,
                'action': 'hold',
                'reason': reason
            }
        
        if symbol not in current_prices:
            return None
        
        price = current_prices[symbol]
        account = self.trading_engine.get_account(self.trader_id)
        
        if action == 'buy':
            # 计算购买金额
            available_balance = account['balance']
            invest_amount = available_balance * (percentage / 100)
            crypto_amount = invest_amount / price
            
            if crypto_amount > 0:
                result = self.trading_engine.execute_trade(
                    self.trader_id, symbol, 'buy', crypto_amount, price, reason
                )
                return result
        
        elif action == 'sell':
            # 计算卖出数量
            current_position = account['positions'].get(symbol, 0)
            sell_amount = current_position * (percentage / 100)
            
            if sell_amount > 0:
                result = self.trading_engine.execute_trade(
                    self.trader_id, symbol, 'sell', sell_amount, price, reason
                )
                return result
        
        return None

