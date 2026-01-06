
from .binance_client import BinanceFuturesClient
from .logger import TradingLogger
from typing import Dict, Optional


class MarketOrder:
    """Market order implementation"""
    
    def __init__(self, client: BinanceFuturesClient):
        self.client = client
        self.logger = TradingLogger()
    
    def place_order(self, symbol: str, side: str, quantity: float, 
                   reduce_only: bool = False) -> Dict:
        """
        Place a market order
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            side: BUY or SELL
            quantity: Order quantity
            reduce_only: Only reduce position, don't increase
        
        Returns:
            Order response from Binance
        """
        try:
            self.logger.log("MARKET_ORDER", f"Placing {side} market order for {quantity} {symbol}")
            
            order_params = {
                'symbol': symbol.upper(),
                'side': side.upper(),
                'type': 'MARKET',
                'quantity': round(quantity, 8),
                'reduceOnly': reduce_only,
                'newOrderRespType': 'RESULT'  # Get full order response
            }
            
            # Remove None values
            order_params = {k: v for k, v in order_params.items() if v is not None}
            
            response = self.client.new_order(**order_params)
            
            if 'orderId' in response:
                self.logger.log("SUCCESS", f"Market order placed: {response}")
            else:
                self.logger.log("ERROR", f"Market order failed: {response}")
            
            return response
            
        except Exception as e:
            error_msg = f"Error placing market order: {str(e)}"
            self.logger.log("ERROR", error_msg)
            return {'error': error_msg, 'status': 'ERROR'}
    
    def close_position(self, symbol: str, side: str = None, 
                      quantity: float = None) -> Dict:
        """
        Close a position with market order
        
        Args:
            symbol: Trading pair
            side: Current position side (optional, auto-detected)
            quantity: Quantity to close (optional, close all)
        
        Returns:
            Order response
        """
        try:
            # Get current position
            positions = self.client.get_position_info(symbol)
            position = next((p for p in positions if p['symbol'] == symbol), None)
            
            if not position or float(position['positionAmt']) == 0:
                return {'error': 'No position to close', 'status': 'ERROR'}
            
            pos_amount = float(position['positionAmt'])
            pos_side = 'SELL' if pos_amount > 0 else 'BUY'
            close_side = 'SELL' if pos_side == 'BUY' else 'BUY'
            
            close_qty = abs(pos_amount) if quantity is None else min(abs(pos_amount), quantity)
            
            self.logger.log("CLOSE_POSITION", 
                          f"Closing {close_qty} {symbol} position with market order")
            
            return self.place_order(
                symbol=symbol,
                side=close_side,
                quantity=close_qty,
                reduce_only=True
            )
            
        except Exception as e:
            error_msg = f"Error closing position: {str(e)}"
            self.logger.log("ERROR", error_msg)
            return {'error': error_msg, 'status': 'ERROR'}
