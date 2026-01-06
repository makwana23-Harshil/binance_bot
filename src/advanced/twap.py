import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List
from ..binance_client import BinanceFuturesClient
from ..logger import TradingLogger
from ..market_orders import MarketOrder


class TWAPStrategy:
    """Time-Weighted Average Price strategy implementation"""
    
    def __init__(self, client: BinanceFuturesClient):
        self.client = client
        self.logger = TradingLogger()
        self.market_order = MarketOrder(client)
        self.running_strategies = {}
    
    def execute(self, symbol: str, side: str, total_quantity: float,
               duration_hours: float, chunks: int = 10) -> Dict:
        """
        Execute TWAP strategy
        
        Args:
            symbol: Trading pair
            side: BUY or SELL
            total_quantity: Total quantity to trade
            duration_hours: Strategy duration in hours
            chunks: Number of chunks to split into
        
        Returns:
            Strategy execution plan
        """
        try:
            chunk_qty = total_quantity / chunks
            interval_seconds = (duration_hours * 3600) / chunks
            
            self.logger.log("TWAP", 
                          f"Starting TWAP: {side} {total_quantity} {symbol} "
                          f"over {duration_hours}h in {chunks} chunks")
            
            execution_plan = []
            
            for i in range(chunks):
                execution_time = datetime.now() + timedelta(seconds=i * interval_seconds)
                execution_plan.append({
                    'chunk': i + 1,
                    'quantity': chunk_qty,
                    'scheduled_time': execution_time.strftime("%Y-%m-%d %H:%M:%S"),
                    'status': 'PENDING'
                })
            
            # Start execution in background thread
            strategy_id = f"twap_{symbol}_{int(time.time())}"
            
            thread = threading.Thread(
                target=self._execute_twap_background,
                args=(strategy_id, symbol, side, chunk_qty, chunks, interval_seconds)
            )
            thread.daemon = True
            thread.start()
            
            self.running_strategies[strategy_id] = {
                'symbol': symbol,
                'side': side,
                'total_quantity': total_quantity,
                'chunks_completed': 0,
                'start_time': datetime.now(),
                'status': 'RUNNING'
            }
            
            return {
                'strategy_id': strategy_id,
                'symbol': symbol,
                'side': side,
                'total_quantity': total_quantity,
                'chunk_quantity': chunk_qty,
                'chunks': chunks,
                'interval_seconds': interval_seconds,
                'execution_plan': execution_plan,
                'status': 'STARTED'
            }
            
        except Exception as e:
            error_msg = f"Error starting TWAP strategy: {str(e)}"
            self.logger.log("ERROR", error_msg)
            return {'error': error_msg, 'status': 'ERROR'}
    
    def _execute_twap_background(self, strategy_id: str, symbol: str, side: str,
                                chunk_qty: float, chunks: int, interval_seconds: float):
        """Execute TWAP in background thread"""
        try:
            for i in range(chunks):
                time.sleep(interval_seconds)
                
                self.logger.log("TWAP_EXEC", 
                              f"Executing chunk {i+1}/{chunks} for {strategy_id}")
                
                # Place market order for this chunk
                result = self.market_order.place_order(
                    symbol=symbol,
                    side=side,
                    quantity=chunk_qty
                )
                
                if strategy_id in self.running_strategies:
                    self.running_strategies[strategy_id]['chunks_completed'] = i + 1
                
                self.logger.log("TWAP_RESULT", 
                              f"Chunk {i+1} result: {result.get('status', 'UNKNOWN')}")
            
            # Mark strategy as completed
            if strategy_id in self.running_strategies:
                self.running_strategies[strategy_id]['status'] = 'COMPLETED'
                self.running_strategies[strategy_id]['end_time'] = datetime.now()
                
                self.logger.log("TWAP", f"Strategy {strategy_id} completed successfully")
            
        except Exception as e:
            self.logger.log("ERROR", f"TWAP execution error: {str(e)}")
            if strategy_id in self.running_strategies:
                self.running_strategies[strategy_id]['status'] = 'ERROR'
                self.running_strategies[strategy_id]['error'] = str(e)
    
    def get_strategy_status(self, strategy_id: str) -> Dict:
        """Get status of a running TWAP strategy"""
        return self.running_strategies.get(strategy_id, {})
    
    def cancel_strategy(self, strategy_id: str) -> bool:
        """Cancel a running TWAP strategy"""
        try:
            if strategy_id in self.running_strategies:
                self.running_strategies[strategy_id]['status'] = 'CANCELLED'
                self.running_strategies[strategy_id]['end_time'] = datetime.now()
                self.logger.log("TWAP", f"Strategy {strategy_id} cancelled")
                return True
            return False
        except Exception as e:
            self.logger.log("ERROR", f"Error cancelling strategy: {str(e)}")
            return False
