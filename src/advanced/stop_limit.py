from ..binance_client import BinanceFuturesClient
from ..logger import TradingLogger
from typing import Dict


class StopLimitOrder:
    """Stop-Limit order implementation"""
    
    def __init__(self, client: BinanceFuturesClient):
        self.client = client
        self.logger = TradingLogger()
    
    def place_order(self, symbol: str, side: str, quantity: float,
                   stop_price: float, limit_price: float,
                   reduce_only: bool = False) -> Dict:
        """
        Place a stop-limit order
        
        Args:
            symbol: Trading pair
            side: BUY or SELL
            quantity: Order quantity
            stop_price: Stop price (triggers the limit order)
            limit_price: Limit price (execution price)
            reduce_only: Only reduce position
        
        Returns:
            Order response
        """
        try:
            self.logger.log("STOP_LIMIT", 
                          f"Placing {side} stop-limit: {quantity} {symbol} "
                          f"stop@{stop_price} limit@{limit_price}")
            
            # Determine order side based on stop price logic
            # For stop-loss: SELL stop below current price, BUY stop above current price
            # For take-profit: Opposite logic
            
            order_params = {
                'symbol': symbol.upper(),
                'side': side.upper(),
                'type': 'STOP',
                'quantity': round(quantity, 8),
                'price': str(round(limit_price, 2)),
                'stopPrice': str(round(stop_price, 2)),
                'timeInForce': 'GTC',
                'reduceOnly': reduce_only,
                'workingType': 'MARK_PRICE',  # Use mark price for triggering
                'priceProtect': 'TRUE',  # Protect against slippage
                'newOrderRespType': 'RESULT'
            }
            
            response = self.client.new_order(**order_params)
            
            if 'orderId' in response:
                self.logger.log("SUCCESS", f"Stop-limit order placed: {response}")
            else:
                self.logger.log("ERROR", f"Stop-limit order failed: {response}")
            
            return response
            
        except Exception as e:
            error_msg = f"Error placing stop-limit order: {str(e)}"
            self.logger.log("ERROR", error_msg)
            return {'error': error_msg, 'status': 'ERROR'}
    
    def place_trailing_stop(self, symbol: str, side: str, quantity: float,
                           activation_price: float, callback_rate: float = 1.0) -> Dict:
        """
        Place a trailing stop order
        
        Args:
            symbol: Trading pair
            side: BUY or SELL
            quantity: Order quantity
            activation_price: Price to activate trailing stop
            callback_rate: Percentage callback rate
        
        Returns:
            Order response
        """
        try:
            self.logger.log("TRAILING_STOP", 
                          f"Placing trailing stop: {quantity} {symbol} "
                          f"activate@{activation_price} callback@{callback_rate}%")
            
            order_params = {
                'symbol': symbol.upper(),
                'side': side.upper(),
                'type': 'TRAILING_STOP_MARKET',
                'quantity': round(quantity, 8),
                'activationPrice': str(round(activation_price, 2)),
                'callbackRate': str(callback_rate),
                'reduceOnly': True,
                'newOrderRespType': 'RESULT'
            }
            
            response = self.client.new_order(**order_params)
            return response
            
        except Exception as e:
            error_msg = f"Error placing trailing stop: {str(e)}"
            self.logger.log("ERROR", error_msg)
            return {'error': error_msg, 'status': 'ERROR'}
