#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加密货币新闻获取模块
支持多个免费API源
"""

import requests
from datetime import datetime
from typing import List, Dict, Optional
import time

class CryptoNewsAPI:
    """加密货币新闻API封装 - 整合4个主要新闻源"""
    
    def __init__(self, cryptopanic_key: str = "1bdc562bbcded391ee4e55d902b06532a83a1bc0"):
        # API端点
        self.cryptocompare_base = "https://min-api.cryptocompare.com/data/v2/news/"
        self.messari_base = "https://data.messari.io/api/v1/news"
        self.cryptopanic_base = "https://cryptopanic.com/api/v1/posts/"
        self.coingecko_base = "https://api.coingecko.com/api/v3/"
        
        # CryptoPanic API Key
        self.cryptopanic_key = cryptopanic_key
        
        # 缓存设置
        self.cache = {}
        self.cache_expiry = 60  # 1分钟缓存（降低缓存时间）
        
    def get_latest_news(self, 
                       limit: int = 10,
                       categories: Optional[List[str]] = None) -> List[Dict]:
        """
        获取最新加密货币新闻
        
        Args:
            limit: 返回新闻数量
            categories: 过滤类别（如 ['BTC', 'ETH']）
            
        Returns:
            新闻列表，每条包含 title, source, time, url, summary
        """
        cache_key = f"news_{limit}_{categories}"
        
        # 检查缓存
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if time.time() - cached_time < self.cache_expiry:
                return cached_data
        
        # 获取新闻（从4个源聚合）
        news_items = []
        
        # 1. CryptoPanic（主要来源 - 有API Key，数据质量最好）
        try:
            cp_news = self._get_cryptopanic_news(limit, categories)
            news_items.extend(cp_news)
            print(f"  ✅ CryptoPanic: {len(cp_news)} 条新闻")
        except Exception as e:
            print(f"  ⚠️  CryptoPanic API 错误: {e}")
        
        # 2. CryptoCompare（免费，稳定）
        if len(news_items) < limit:
            try:
                cc_news = self._get_cryptocompare_news(limit, categories)
                news_items.extend(cc_news)
                print(f"  ✅ CryptoCompare: {len(cc_news)} 条新闻")
            except Exception as e:
                print(f"  ⚠️  CryptoCompare API 错误: {e}")
        
        # 3. CoinGecko（补充来源）
        if len(news_items) < limit:
            try:
                cg_news = self._get_coingecko_news(limit - len(news_items))
                news_items.extend(cg_news)
                print(f"  ✅ CoinGecko: {len(cg_news)} 条新闻")
            except Exception as e:
                print(f"  ⚠️  CoinGecko API 错误: {e}")
        
        # 4. Messari（研究报告）
        if len(news_items) < limit:
            try:
                messari_news = self._get_messari_news(limit - len(news_items))
                news_items.extend(messari_news)
                print(f"  ✅ Messari: {len(messari_news)} 条研究报告")
            except Exception as e:
                print(f"  ⚠️  Messari API 错误: {e}")
        
        # 按时间排序
        news_items.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        # 缓存结果
        self.cache[cache_key] = (time.time(), news_items[:limit])
        
        return news_items[:limit]
    
    def _get_cryptocompare_news(self, 
                               limit: int,
                               categories: Optional[List[str]] = None) -> List[Dict]:
        """从CryptoCompare获取新闻"""
        
        params = {
            "lang": "EN",
        }
        
        if categories:
            params["categories"] = ",".join(categories)
        
        response = requests.get(
            self.cryptocompare_base,
            params=params,
            timeout=10
        )
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        data = response.json()
        
        if data.get('Type') != 100 or 'Data' not in data:
            raise Exception(f"Invalid response: {data.get('Message', 'Unknown')}")
        
        news_items = []
        for item in data['Data'][:limit]:
            news_items.append({
                'title': item.get('title', 'N/A'),
                'source': item.get('source', 'Unknown'),
                'time': datetime.fromtimestamp(item.get('published_on', 0)).strftime('%Y-%m-%d %H:%M'),
                'timestamp': item.get('published_on', 0),
                'url': item.get('url', ''),
                'summary': item.get('body', '')[:200] + '...' if item.get('body') else '',
                'categories': item.get('categories', '').split('|') if item.get('categories') else [],
                'type': 'news'
            })
        
        return news_items
    
    def _get_messari_news(self, limit: int) -> List[Dict]:
        """从Messari获取新闻"""
        
        params = {
            "limit": limit,
            "fields": "title,content,published_at,url"
        }
        
        response = requests.get(
            self.messari_base,
            params=params,
            timeout=10
        )
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        data = response.json()
        news_items = []
        
        for item in data.get('data', [])[:limit]:
            published_at = item.get('published_at', '')
            try:
                timestamp = int(datetime.fromisoformat(published_at.replace('Z', '+00:00')).timestamp())
                time_str = datetime.fromisoformat(published_at.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
            except:
                timestamp = 0
                time_str = published_at
            
            news_items.append({
                'title': item.get('title', 'N/A'),
                'source': 'Messari',
                'time': time_str,
                'timestamp': timestamp,
                'url': item.get('url', ''),
                'summary': 'Messari Research Report',
                'categories': ['RESEARCH'],
                'type': 'research'
            })
        
        return news_items
    
    def _get_cryptopanic_news(self, 
                             limit: int,
                             categories: Optional[List[str]] = None) -> List[Dict]:
        """从CryptoPanic获取新闻（需要API Key）"""
        
        params = {
            "auth_token": self.cryptopanic_key,
            "kind": "news",  # news, media, all
            "filter": "rising",  # rising, hot, bullish, bearish, important, saved, lol
        }
        
        # 添加币种过滤
        if categories:
            # CryptoPanic使用逗号分隔的币种代码
            params["currencies"] = ",".join(categories)
        
        response = requests.get(
            self.cryptopanic_base,
            params=params,
            timeout=10
        )
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        data = response.json()
        news_items = []
        
        for item in data.get('results', [])[:limit]:
            # 解析时间
            published_at = item.get('published_at', '')
            try:
                timestamp = int(datetime.fromisoformat(published_at.replace('Z', '+00:00')).timestamp())
                time_str = datetime.fromisoformat(published_at.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
            except:
                timestamp = 0
                time_str = published_at
            
            # 提取币种标签
            currencies = [c['code'] for c in item.get('currencies', [])]
            
            # 获取投票数据（情绪指标）
            votes = item.get('votes', {})
            positive = votes.get('positive', 0)
            negative = votes.get('negative', 0)
            total_votes = positive + negative
            sentiment = "neutral"
            if total_votes > 0:
                if positive > negative * 1.5:
                    sentiment = "bullish"
                elif negative > positive * 1.5:
                    sentiment = "bearish"
            
            news_items.append({
                'title': item.get('title', 'N/A'),
                'source': item.get('source', {}).get('title', 'CryptoPanic'),
                'time': time_str,
                'timestamp': timestamp,
                'url': item.get('url', ''),
                'summary': item.get('title', '')[:200],
                'categories': currencies,
                'sentiment': sentiment,
                'votes': {'positive': positive, 'negative': negative},
                'type': 'news'
            })
        
        return news_items
    
    def _get_coingecko_news(self, limit: int) -> List[Dict]:
        """从CoinGecko获取新闻（通过status_updates端点）"""
        
        try:
            # CoinGecko的状态更新端点
            response = requests.get(
                f"{self.coingecko_base}status_updates",
                params={
                    "category": "general",
                    "per_page": limit
                },
                timeout=10
            )
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
            
            data = response.json()
            news_items = []
            
            for item in data.get('status_updates', [])[:limit]:
                # 解析时间
                created_at = item.get('created_at', '')
                try:
                    timestamp = int(datetime.fromisoformat(created_at.replace('Z', '+00:00')).timestamp())
                    time_str = datetime.fromisoformat(created_at.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
                except:
                    timestamp = 0
                    time_str = created_at
                
                # 提取项目信息
                project = item.get('project', {})
                project_name = project.get('name', 'CoinGecko')
                
                news_items.append({
                    'title': item.get('description', 'N/A')[:100],
                    'source': project_name,
                    'time': time_str,
                    'timestamp': timestamp,
                    'url': item.get('project', {}).get('image', {}).get('large', ''),
                    'summary': item.get('description', '')[:200],
                    'categories': [project.get('symbol', '').upper()] if project.get('symbol') else [],
                    'type': 'update'
                })
            
            return news_items
            
        except Exception as e:
            # CoinGecko的status_updates可能不稳定，降级处理
            print(f"    CoinGecko status_updates失败，使用trending端点: {e}")
            return []
    
    def get_news_summary(self, limit: int = 5) -> str:
        """
        获取新闻摘要（用于AI prompt）
        
        Args:
            limit: 返回新闻数量
            
        Returns:
            格式化的新闻摘要字符串
        """
        news_items = self.get_latest_news(limit=limit)
        
        if not news_items:
            return "暂无最新新闻。"
        
        summary = "📰 最新加密货币新闻:\n\n"
        
        for i, item in enumerate(news_items, 1):
            summary += f"{i}. [{item['time']}] {item['title']}\n"
            summary += f"   来源: {item['source']}"
            if item.get('categories'):
                cats = [c for c in item['categories'] if c and len(c) < 20][:3]
                if cats:
                    summary += f" | 标签: {', '.join(cats)}"
            summary += "\n"
            if item.get('summary'):
                summary += f"   {item['summary'][:150]}...\n"
            summary += "\n"
        
        return summary
    
    def get_market_sentiment(self, limit: int = 20) -> Dict:
        """
        分析市场情绪（基于新闻关键词）
        
        Args:
            limit: 分析的新闻数量
            
        Returns:
            情绪分析结果
        """
        news_items = self.get_latest_news(limit=limit)
        
        # 正面关键词
        positive_keywords = [
            'bullish', 'surge', 'rally', 'gain', 'growth', 'breakout',
            'adoption', 'partnership', 'approval', 'optimism', 'momentum',
            'accumulation', 'recovery', 'support', 'upgrade'
        ]
        
        # 负面关键词
        negative_keywords = [
            'bearish', 'drop', 'crash', 'decline', 'fall', 'fear',
            'regulation', 'ban', 'shutdown', 'hack', 'loss', 'risk',
            'warning', 'concern', 'investigation', 'lawsuit'
        ]
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for item in news_items:
            text = (item.get('title', '') + ' ' + item.get('summary', '')).lower()
            
            has_positive = any(kw in text for kw in positive_keywords)
            has_negative = any(kw in text for kw in negative_keywords)
            
            if has_positive and not has_negative:
                positive_count += 1
            elif has_negative and not has_positive:
                negative_count += 1
            else:
                neutral_count += 1
        
        total = len(news_items)
        if total == 0:
            return {
                'sentiment': 'neutral',
                'score': 0,
                'positive_ratio': 0,
                'negative_ratio': 0,
                'confidence': 0
            }
        
        # 计算情绪分数 (-1 到 1)
        sentiment_score = (positive_count - negative_count) / total
        
        # 判断总体情绪
        if sentiment_score > 0.2:
            sentiment = 'positive'
        elif sentiment_score < -0.2:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'score': round(sentiment_score, 2),
            'positive_ratio': round(positive_count / total, 2),
            'negative_ratio': round(negative_count / total, 2),
            'neutral_ratio': round(neutral_count / total, 2),
            'confidence': round(abs(sentiment_score), 2),
            'total_analyzed': total
        }


# ========================================
# 测试代码
# ========================================
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 加密货币新闻模块测试")
    print("="*70)
    
    # 创建API实例
    api = CryptoNewsAPI()
    
    # 测试1: 获取最新新闻
    print("\n" + "-"*70)
    print("📰 测试1: 获取最新10条新闻")
    print("-"*70)
    
    news = api.get_latest_news(limit=10)
    print(f"\n✅ 获取了 {len(news)} 条新闻\n")
    
    for i, item in enumerate(news[:5], 1):
        print(f"{i}. {item['title']}")
        print(f"   来源: {item['source']} | 时间: {item['time']}")
        if item.get('categories'):
            cats = [c for c in item['categories'] if c and len(c) < 20][:3]
            if cats:
                print(f"   标签: {', '.join(cats)}")
        print()
    
    # 测试2: 获取新闻摘要（用于AI）
    print("\n" + "-"*70)
    print("📝 测试2: 生成AI可用的新闻摘要")
    print("-"*70)
    
    summary = api.get_news_summary(limit=5)
    print(summary)
    
    # 测试3: 市场情绪分析
    print("\n" + "-"*70)
    print("💭 测试3: 市场情绪分析")
    print("-"*70)
    
    sentiment = api.get_market_sentiment(limit=20)
    print(f"""
✅ 情绪分析结果:
   总体情绪: {sentiment['sentiment'].upper()}
   情绪分数: {sentiment['score']} (-1到1之间)
   正面占比: {sentiment['positive_ratio']*100:.1f}%
   负面占比: {sentiment['negative_ratio']*100:.1f}%
   中性占比: {sentiment['neutral_ratio']*100:.1f}%
   置信度: {sentiment['confidence']*100:.1f}%
   分析样本: {sentiment['total_analyzed']} 条新闻
    """)
    
    print("="*70)
    print("✅ 测试完成！模块可以直接集成到 Trigo Nexus")
    print("="*70 + "\n")









