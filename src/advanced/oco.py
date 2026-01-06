from ..binance_client import BinanceFuturesClient
from ..logger import TradingLogger
from typing import Dict, List, Tuple


class OCOOrder:
    """One-Cancels-the-Other order implementation"""
    
    def __init__(self, client: BinanceFuturesClient):
        self.client = client
        self.logger = TradingLogger()
    
    def place_order(self, symbol: str, side: str, quantity: float,
                   price: float, stop_price: float, stop_limit_price: float = None,
                   limit_iceberg_qty: float = None, stop_iceberg_qty: float = None) -> Dict:
        """
        Place an OCO order (take-profit + stop-loss)
        
        Args:
            symbol: Trading pair
            side: BUY or SELL (for the take-profit order)
            quantity: Order quantity for both legs
            price: Take-profit limit price
            stop_price: Stop-loss trigger price
            stop_limit_price: Stop-loss limit price (if None, uses stop_price)
            limit_iceberg_qty: Iceberg quantity for limit order
            stop_iceberg_qty: Iceberg quantity for stop order
        
        Returns:
            OCO order response
        """
        try:
            self.logger.log("OCO_ORDER", 
                          f"Placing OCO: {quantity} {symbol} "
                          f"TP@{price} SL@{stop_price}")
            
            # Determine opposite side for stop-loss
            stop_side = 'SELL' if side == 'BUY' else 'BUY'
            
            # If stop_limit_price not provided, use stop_price
            if stop_limit_price is None:
                stop_limit_price = stop_price
            
            order_params = {
                'symbol': symbol.upper(),
                'side': side.upper(),
                'quantity': round(quantity, 8),
                'price': str(round(price, 2)),
                'stopPrice': str(round(stop_price, 2)),
                'stopLimitPrice': str(round(stop_limit_price, 2)),
                'stopLimitTimeInForce': 'GTC',
                'listClientOrderId': f"oco_{int(time.time() * 1000)}",
                'limitClientOrderId': f"limit_{int(time.time() * 1000)}",
                'stopClientOrderId': f"stop_{int(time.time() * 1000)}"
            }
            
            # Add optional parameters
            if limit_iceberg_qty:
                order_params['limitIcebergQty'] = str(round(limit_iceberg_qty, 8))
            if stop_iceberg_qty:
                order_params['stopIcebergQty'] = str(round(stop_iceberg_qty, 8))
            
            response = self.client.new_oco_order(**order_params)
            
            if 'orderListId' in response:
                self.logger.log("SUCCESS", f"OCO order placed: {response}")
                
                # Log individual orders
                for order in response.get('orders', []):
                    self.logger.log("OCO_DETAIL", f"Order: {order}")
            else:
                self.logger.log("ERROR", f"OCO order failed: {response}")
            
            return response
            
        except Exception as e:
            error_msg = f"Error placing OCO order: {str(e)}"
            self.logger.log("ERROR", error_msg)
            return {'error': error_msg, 'status': 'ERROR'}
    
    def get_oco_orders(self, symbol: str = None, from_id: int = None,
                      limit: int = 10) -> List[Dict]:
        """
        Get OCO orders
        
        Args:
            symbol: Filter by symbol
            from_id: Start from this orderListId
            limit: Number of orders to return
        
        Returns:
            List of OCO orders
        """
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol.upper()
            if from_id:
                params['fromId'] = from_id
            if limit:
                params['limit'] = limit
            
            return self.client.get_oco_orders(**params)
            
        except Exception as e:
            error_msg = f"Error getting OCO orders: {str(e)}"
            self.logger.log("ERROR", error_msg)
            return []
