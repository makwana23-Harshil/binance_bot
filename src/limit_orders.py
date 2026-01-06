
from .binance_client import BinanceFuturesClient
from .logger import TradingLogger
from typing import Dict, Optional


class LimitOrder:
    """Limit order implementation"""
    
    def __init__(self, client: BinanceFuturesClient):
        self.client = client
        self.logger = TradingLogger()
    
    def place_order(self, symbol: str, side: str, quantity: float, 
                   price: float, time_in_force: str = 'GTC',
                   reduce_only: bool = False) -> Dict:
        """
        Place a limit order
        
        Args:
            symbol: Trading pair
            side: BUY or SELL
            quantity: Order quantity
            price: Limit price
            time_in_force: GTC, IOC, FOK
            reduce_only: Only reduce position
        
        Returns:
            Order response
        """
        try:
            self.logger.log("LIMIT_ORDER", 
                          f"Placing {side} limit order for {quantity} {symbol} @ {price}")
            
            order_params = {
                'symbol': symbol.upper(),
                'side': side.upper(),
                'type': 'LIMIT',
                'quantity': round(quantity, 8),
                'price': str(round(price, 2)),
                'timeInForce': time_in_force,
                'reduceOnly': reduce_only,
                'newOrderRespType': 'RESULT'
            }
            
            response = self.client.new_order(**order_params)
            
            if 'orderId' in response:
                self.logger.log("SUCCESS", f"Limit order placed: {response}")
            else:
                self.logger.log("ERROR", f"Limit order failed: {response}")
            
            return response
            
        except Exception as e:
            error_msg = f"Error placing limit order: {str(e)}"
            self.logger.log("ERROR", error_msg)
            return {'error': error_msg, 'status': 'ERROR'}
    
    def place_limit_maker(self, symbol: str, side: str, quantity: float, 
                         price: float) -> Dict:
        """
        Place a limit maker order (post-only)
        
        Args:
            symbol: Trading pair
            side: BUY or SELL
            quantity: Order quantity
            price: Limit price
        
        Returns:
            Order response
        """
        try:
            self.logger.log("LIMIT_MAKER", 
                          f"Placing {side} limit maker order for {quantity} {symbol} @ {price}")
            
            order_params = {
                'symbol': symbol.upper(),
                'side': side.upper(),
                'type': 'LIMIT_MAKER',
                'quantity': round(quantity, 8),
                'price': str(round(price, 2)),
                'newOrderRespType': 'RESULT'
            }
            
            response = self.client.new_order(**order_params)
            return response
            
        except Exception as e:
            error_msg = f"Error placing limit maker order: {str(e)}"
            self.logger.log("ERROR", error_msg)
            return {'error': error_msg, 'status': 'ERROR'}
