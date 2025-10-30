"""
订单管理系统
监控止损/止盈订单
"""

class OrderManager:
    """订单管理器"""
    
    def __init__(self, leverage_engine):
        self.engine = leverage_engine
        self.stop_orders = {}  # {order_id: order_obj}
        self.limit_orders = {}
        self.order_id_counter = 1
        
    def create_stop_loss(self, trader_id, symbol, trigger_price, reason="止损"):
        """创建止损单"""
        order_id = self.order_id_counter
        self.order_id_counter += 1
        
        self.stop_orders[order_id] = {
            'id': order_id,
            'trader_id': trader_id,
            'symbol': symbol,
            'type': 'stop_loss',
            'trigger_price': trigger_price,
            'reason': reason,
            'active': True
        }
        
        return order_id
    
    def create_take_profit(self, trader_id, symbol, trigger_price, reason="止盈"):
        """创建止盈单"""
        order_id = self.order_id_counter
        self.order_id_counter += 1
        
        self.limit_orders[order_id] = {
            'id': order_id,
            'trader_id': trader_id,
            'symbol': symbol,
            'type': 'take_profit',
            'trigger_price': trigger_price,
            'reason': reason,
            'active': True
        }
        
        return order_id
    
    def check_orders(self, current_prices):
        """检查所有订单是否触发"""
        triggered = []
        
        for order_id, order in list(self.stop_orders.items()):
            if not order['active']:
                continue
            
            symbol = order['symbol']
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            trader_id = order['trader_id']
            
            # 检查持仓方向
            positions = self.engine.get_positions(trader_id)
            if symbol not in positions:
                order['active'] = False
                continue
            
            position = positions[symbol]
            
            # 止损触发条件
            if position['side'] == 'long' and current_price <= order['trigger_price']:
                result = self.engine.close_position(trader_id, symbol, current_price, order['reason'])
                if result['success']:
                    triggered.append(order)
                order['active'] = False
            elif position['side'] == 'short' and current_price >= order['trigger_price']:
                result = self.engine.close_position(trader_id, symbol, current_price, order['reason'])
                if result['success']:
                    triggered.append(order)
                order['active'] = False
        
        # 检查止盈单
        for order_id, order in list(self.limit_orders.items()):
            if not order['active']:
                continue
            
            symbol = order['symbol']
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            trader_id = order['trader_id']
            
            positions = self.engine.get_positions(trader_id)
            if symbol not in positions:
                order['active'] = False
                continue
            
            position = positions[symbol]
            
            # 止盈触发条件
            if position['side'] == 'long' and current_price >= order['trigger_price']:
                result = self.engine.close_position(trader_id, symbol, current_price, order['reason'])
                if result['success']:
                    triggered.append(order)
                order['active'] = False
            elif position['side'] == 'short' and current_price <= order['trigger_price']:
                result = self.engine.close_position(trader_id, symbol, current_price, order['reason'])
                if result['success']:
                    triggered.append(order)
                order['active'] = False
        
        return triggered



