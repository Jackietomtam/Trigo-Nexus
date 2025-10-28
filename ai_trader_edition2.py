#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Edition 2: AI交易员（在Edition 1基础上添加新闻）
- 使用Edition 1完全相同的prompt结构
- 仅在有新闻时添加过去3分钟的原始新闻数据（不做AI分析）
"""

import json
import re
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config import DASHSCOPE_API_KEY, DASHSCOPE_DEEPSEEK_API_KEY
from crypto_news import CryptoNewsAPI

# 直接继承Edition 1的AITraderV2类
from ai_trader_v2 import AITraderV2

class AITraderEdition2(AITraderV2):
    """Edition 2 AI交易员 - 继承Edition 1并添加新闻"""
    
    def __init__(self, model_id, name, model, strategy, account, leverage_engine, kline_data, order_manager):
        # 调用父类初始化
        super().__init__(
            trader_id=model_id,
            name=name,
            strategy=strategy,
            model=model,
            leverage_engine=leverage_engine,
            kline_data=kline_data,
            order_manager=order_manager
        )
        
        # Edition 2特有：新闻API
        self.news_api = CryptoNewsAPI()
        self.news_cache = {
            'data': None,
            'timestamp': 0,
            'expiry': 60  # 1分钟缓存（降低缓存时间，确保新闻更新）
        }
        
        print(f"  ✅ {self.name} 初始化完成 [Edition 2 - With News]")
    
    def _get_recent_news(self, minutes: int = 3) -> Optional[str]:
        """
        获取最近N分钟的原始新闻（不做任何AI分析）
        默认3分钟窗口，确保新闻实时性
            
        Returns:
            格式化的原始新闻列表，如果没有新闻返回None
        """
        now = time.time()
        
        # 检查缓存（1分钟缓存，确保新闻及时更新）
        if (self.news_cache['data'] is not None and 
            now - self.news_cache['timestamp'] < self.news_cache['expiry']):
            # 即使返回缓存，也要重新计算时间窗口
            cached_data = self.news_cache['data']
            if cached_data:
                return cached_data
        
        try:
            # 获取最新新闻
            news_items = self.news_api.get_latest_news(limit=20)
            
            if not news_items:
                self.news_cache['data'] = None
                self.news_cache['timestamp'] = now
                return None
            
            # 过滤最近N分钟的新闻
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            recent_news = []
            
            for item in news_items:
                try:
                    # 解析新闻时间
                    news_time_str = item.get('time', '')
                    news_time = datetime.strptime(news_time_str, '%Y-%m-%d %H:%M')
                    
                    if news_time >= cutoff_time:
                        recent_news.append(item)
                except Exception:
                    continue
            
            # 如果没有最近N分钟的新闻，显示最新的5条（4个API源，总能找到）
            if not recent_news:
                recent_news = news_items[:5]  # 至少显示最新的5条新闻
            
            # 格式化原始新闻列表（使用Edition 1的英文风格）
            summary = f"\n\nRECENT NEWS (Past {minutes} Minutes)\n\n"
            summary += f"Total news items: {len(recent_news)}\n\n"
            
            for i, item in enumerate(recent_news[:10], 1):  # 最多10条
                summary += f"{i}. [{item['time']}] {item['title']}\n"
                summary += f"   Source: {item['source']}"
                
                # 添加相关币种标签
                categories = item.get('categories', [])
                crypto_tags = [c for c in categories if c in ['BTC', 'ETH', 'SOL', 'BNB', 'DOGE', 'XRP']]
                if crypto_tags:
                    summary += f" | Related: {', '.join(crypto_tags)}"
                summary += "\n"
            
            # 更新缓存
            self.news_cache['data'] = summary
            self.news_cache['timestamp'] = now
            
            return summary
        except Exception as e:
            print(f"  ⚠️  获取新闻失败: {e}")
            self.news_cache['data'] = None
            self.news_cache['timestamp'] = now
            return None
    
    def _build_detailed_prompt(self, account, positions, indicators):
        """
        构建prompt - 使用Edition 1的完整结构，仅在有新闻时添加新闻部分
        """
        # 调用父类的prompt构建方法（Edition 1的完整prompt）
        base_prompt = super()._build_detailed_prompt(account, positions, indicators)
        
        # 尝试获取最近3分钟的新闻（4个API源，确保覆盖率）
        recent_news = self._get_recent_news(minutes=3)
        
        # 如果有新闻，在Sharpe Ratio之前插入新闻部分
        if recent_news:
            print(f"  📰 [{self.name}] 新闻已整合到prompt中（{len(recent_news)} 字符）", flush=True)
            # 在prompt中找到Sharpe Ratio的位置，在之前插入新闻
            sharpe_pos = base_prompt.find('\nSharpe Ratio:')
            if sharpe_pos > 0:
                # 在Sharpe Ratio之前插入新闻
                enhanced_prompt = base_prompt[:sharpe_pos] + recent_news + base_prompt[sharpe_pos:]
                print(f"  📰 [{self.name}] Prompt长度: {len(base_prompt)} -> {len(enhanced_prompt)}", flush=True)
                return enhanced_prompt
        else:
            print(f"  ℹ️  [{self.name}] 最近3分钟无新闻，使用Edition 1 prompt", flush=True)
        
        # 如果没有新闻，直接返回Edition 1的prompt
        return base_prompt
    
    def make_decision(self, prices=None, indicators=None):
        """
        做出交易决策 - Edition 2返回原始AI决策（dict格式）
        
        Edition 2的交易循环会自己处理交易执行，所以这里只返回AI的原始决策
        """
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
                print(f"  ⚠ {self.name} 技术指标不足，跳过决策", flush=True)
                return None
            
            # 生成详细的prompt（使用Edition 2的方法，会自动添加新闻）
            print(f"  → {self.name} 构建prompt...", flush=True)
            prompt = self._build_detailed_prompt(account, positions, all_indicators)
            print(f"  → {self.name} prompt长度: {len(prompt)}", flush=True)
            
            # 调用AI
            print(f"  → {self.name} 调用AI模型: {self.model}...", flush=True)
            decision = self._call_ai(prompt)
            
            # 保存对话（包含prompt）
            self._save_chat(decision, account, positions, prompt)
            
            # Edition 2直接返回原始AI决策（dict格式），不调用_execute_decision
            # 交易执行由Edition 2的交易循环负责
            return decision
            
        except Exception as e:
            print(f"  ✗ {self.name} 决策错误: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return None
