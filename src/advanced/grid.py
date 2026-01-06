import numpy as np
from typing import Dict, List
from ..binance_client import BinanceFuturesClient
from ..logger import TradingLogger
from ..limit_orders import LimitOrder


class GridStrategy:
    """Grid trading strategy implementation"""
    
    def __init__(self, client: BinanceFuturesClient):
        self.client = client
        self.logger = TradingLogger()
        self.limit_order = LimitOrder(client)
        self.active_grids = {}
    
    def setup_grid(self, symbol: str, lower_price: float, upper_price: float,
                  grid_lines: int, order_qty: float, grid_type: str = 'Arithmetic') -> Dict:
        """
        Setup grid trading strategy
        
        Args:
            symbol: Trading pair
            lower_price: Lower bound of grid
            upper_price: Upper bound of grid
            grid_lines: Number of grid lines
            order_qty: Quantity per order
            grid_type: 'Arithmetic' or 'Geometric'
        
        Returns:
            Grid setup details
        """
        try:
            # Calculate grid prices
            if grid_type.lower() == 'geometric':
                prices = np.geomspace(lower_price, upper_price, grid_lines)
            else:  # Arithmetic
                prices = np.linspace(lower_price, upper_price, grid_lines)
            
            grid_levels = []
            
            for i, price in enumerate(prices):
                if i % 2 == 0:
                    side = 'BUY'
                    order_type = 'BUY limit'
                else:
                    side = 'SELL'
                    order_type = 'SELL limit'
                
                grid_levels.append({
                    'level': i + 1,
                    'price': round(price, 2),
                    'side': side,
                    'type': order_type,
                    'quantity': order_qty,
                    'status': 'PENDING'
                })
            
            grid_id = f"grid_{symbol}_{int(time.time())}"
            
            self.active_grids[grid_id] = {
                'symbol': symbol,
                'lower_price': lower_price,
                'upper_price': upper_price,
                'grid_lines': grid_lines,
                'order_qty': order_qty,
                'grid_type': grid_type,
                'levels': grid_levels,
                'status': 'SETUP',
                'orders_placed': 0,
                'orders_filled': 0
            }
            
            self.logger.log("GRID", 
                          f"Grid setup: {symbol} {lower_price}-{upper_price} "
                          f"with {grid_lines} lines")
            
            # Place initial orders in background
            thread = threading.Thread(
                target=self._place_grid_orders,
                args=(grid_id,)
            )
            thread.daemon = True
            thread.start()
            
            return {
                'grid_id': grid_id,
                'symbol': symbol,
                'price_range': f"{lower_price}-{upper_price}",
                'grid_type': grid_type,
                'grid_lines': grid_lines,
                'order_qty': order_qty,
                'grid_levels': grid_levels,
                'status': 'INITIALIZED'
            }
            
        except Exception as e:
            error_msg = f"Error setting up grid: {str(e)}"
            self.logger.log("ERROR", error_msg)
            return {'error': error_msg, 'status': 'ERROR'}
    
    def _place_grid_orders(self, grid_id: str):
        """Place all grid orders"""
        try:
            grid = self.active_grids.get(grid_id)
            if not grid:
                return
            
            symbol = grid['symbol']
            
            for level in grid['levels']:
                try:
                    result = self.limit_order.place_order(
                        symbol=symbol,
                        side=level['side'],
                        quantity=level['quantity'],
                        price=level['price'],
                        time_in_force='GTC'
                    )
                    
                    if 'orderId' in result:
                        level['status'] = 'PLACED'
                        level['order_id'] = result['orderId']
                        grid['orders_placed'] += 1
                        
                        self.logger.log("GRID_ORDER", 
                                      f"Grid order placed: {level['side']} "
                                      f"{level['quantity']} @ {level['price']}")
                    else:
                        level['status'] = 'FAILED'
                        level['error'] = result.get('msg', 'Unknown error')
                
                except Exception as e:
                    level['status'] = 'ERROR'
                    level['error'] = str(e)
                    self.logger.log("ERROR", f"Grid order error: {str(e)}")
                
                # Small delay between orders
                time.sleep(0.1)
            
            grid['status'] = 'ACTIVE'
            self.active_grids[grid_id] = grid
            
            self.logger.log("GRID", f"Grid {grid_id} activated with {grid['orders_placed']} orders")
            
        except Exception as e:
            self.logger.log("ERROR", f"Error placing grid orders: {str(e)}")
    
    def monitor_grid(self, grid_id: str) -> Dict:
        """Monitor and update grid status"""
        try:
            grid = self.active_grids.get(grid_id)
            if not grid:
                return {'error': 'Grid not found', 'status': 'ERROR'}
            
            symbol = grid['symbol']
            
            # Get open orders
            open_orders = self.client.get_open_orders(symbol)
            open_order_ids = [str(order['orderId']) for order in open_orders]
            
            # Update grid status
            filled_orders = 0
            for level in grid['levels']:
                if 'order_id' in level:
                    if str(level['order_id']) in open_order_ids:
                        level['status'] = 'OPEN'
                    else:
                        level['status'] = 'FILLED'
                        filled_orders += 1
            
            grid['orders_filled'] = filled_orders
            self.active_grids[grid_id] = grid
            
            return {
                'grid_id': grid_id,
                'status': grid['status'],
                'orders_placed': grid['orders_placed'],
                'orders_filled': filled_orders,
                'completion': f"{(filled_orders / grid['orders_placed']) * 100:.1f}%" if grid['orders_placed'] > 0 else "0%",
                'levels': grid['levels']
            }
            
        except Exception as e:
            error_msg = f"Error monitoring grid: {str(e)}"
            self.logger.log("ERROR", error_msg)
            return {'error': error_msg, 'status': 'ERROR'}
    
    def close_grid(self, grid_id: str) -> Dict:
        """Close grid strategy and cancel all orders"""
        try:
            grid = self.active_grids.get(grid_id)
            if not grid:
                return {'error': 'Grid not found', 'status': 'ERROR'}
            
            symbol = grid['symbol']
            
            # Cancel all open orders for this symbol
            open_orders = self.client.get_open_orders(symbol)
            cancelled = 0
            
            for order in open_orders:
                try:
                    result = self.client.cancel_order(symbol, order['orderId'])
                    if 'orderId' in result:
                        cancelled += 1
                except:
                    pass
            
            grid['status'] = 'CLOSED'
            self.active_grids[grid_id] = grid
            
            self.logger.log("GRID", f"Grid {grid_id} closed, {cancelled} orders cancelled")
            
            return {
                'grid_id': grid_id,
                'status': 'CLOSED',
                'orders_cancelled': cancelled,
                'message': f'Grid closed successfully, {cancelled} orders cancelled'
            }
            
        except Exception as e:
            error_msg = f"Error closing grid: {str(e)}"
            self.logger.log("ERROR", error_msg)
            return {'error': error_msg, 'status': 'ERROR'}
