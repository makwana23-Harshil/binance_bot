import re
from typing import Tuple, Optional


class OrderValidator:
    """Input validation for trading orders"""
    
    # Binance Futures trading pairs pattern
    SYMBOL_PATTERN = r'^[A-Z]{3,10}(USDT|BUSD|BTC|ETH)$'
    
    # Minimum order quantities (Binance Futures requirements)
    MIN_QUANTITIES = {
        'BTCUSDT': 0.001,
        'ETHUSDT': 0.01,
        'BNBUSDT': 0.1,
        'ADAUSDT': 1,
        'XRPUSDT': 1,
        'DEFAULT': 0.001
    }
    
    # Price precision by symbol
    PRICE_PRECISIONS = {
        'BTCUSDT': 2,
        'ETHUSDT': 2,
        'BNBUSDT': 3,
        'ADAUSDT': 5,
        'XRPUSDT': 4,
        'DEFAULT': 2
    }
    
    def __init__(self):
        self.errors = []
    
    def validate_symbol(self, symbol: str) -> Tuple[bool, Optional[str]]:
        """Validate trading symbol"""
        symbol = symbol.upper().strip()
        
        if not symbol:
            return False, "Symbol cannot be empty"
        
        if not re.match(self.SYMBOL_PATTERN, symbol):
            return False, f"Invalid symbol format: {symbol}. Expected format like BTCUSDT, ETHUSDT"
        
        return True, symbol
    
    def validate_quantity(self, symbol: str, quantity: float) -> Tuple[bool, Optional[str]]:
        """Validate order quantity"""
        symbol = symbol.upper().strip()
        
        if quantity <= 0:
            return False, "Quantity must be greater than 0"
        
        min_qty = self.MIN_QUANTITIES.get(symbol, self.MIN_QUANTITIES['DEFAULT'])
        
        if quantity < min_qty:
            return False, f"Minimum quantity for {symbol} is {min_qty}"
        
        # Check if quantity has too many decimal places
        if len(str(quantity).split('.')[-1]) > 8:
            return False, "Quantity cannot have more than 8 decimal places"
        
        return True, f"Quantity {quantity} is valid"
    
    def validate_price(self, symbol: str, price: float) -> Tuple[bool, Optional[str]]:
        """Validate price"""
        symbol = symbol.upper().strip()
        
        if price <= 0:
            return False, "Price must be greater than 0"
        
        precision = self.PRICE_PRECISIONS.get(symbol, self.PRICE_PRECISIONS['DEFAULT'])
        
        # Check price precision
        price_str = str(price)
        if '.' in price_str:
            decimals = len(price_str.split('.')[-1])
            if decimals > precision:
                return False, f"Price precision for {symbol} is {precision} decimal places"
        
        return True, f"Price {price} is valid"
    
    def validate_market_order(self, symbol: str, quantity: float) -> bool:
        """Validate market order inputs"""
        self.errors = []
        
        # Validate symbol
        symbol_valid, symbol_msg = self.validate_symbol(symbol)
        if not symbol_valid:
            self.errors.append(symbol_msg)
        
        # Validate quantity
        quantity_valid, quantity_msg = self.validate_quantity(symbol, quantity)
        if not quantity_valid:
            self.errors.append(quantity_msg)
        
        return len(self.errors) == 0
    
    def validate_limit_order(self, symbol: str, quantity: float, price: float) -> bool:
        """Validate limit order inputs"""
        self.errors = []
        
        # Validate symbol
        symbol_valid, symbol_msg = self.validate_symbol(symbol)
        if not symbol_valid:
            self.errors.append(symbol_msg)
        
        # Validate quantity
        quantity_valid, quantity_msg = self.validate_quantity(symbol, quantity)
        if not quantity_valid:
            self.errors.append(quantity_msg)
        
        # Validate price
        price_valid, price_msg = self.validate_price(symbol, price)
        if not price_valid:
            self.errors.append(price_msg)
        
        return len(self.errors) == 0
    
    def validate_stop_limit_order(self, symbol: str, quantity: float, 
                                 stop_price: float, limit_price: float) -> bool:
        """Validate stop-limit order inputs"""
        self.errors = []
        
        # Validate symbol
        symbol_valid, symbol_msg = self.validate_symbol(symbol)
        if not symbol_valid:
            self.errors.append(symbol_msg)
        
        # Validate quantity
        quantity_valid, quantity_msg = self.validate_quantity(symbol, quantity)
        if not quantity_valid:
            self.errors.append(quantity_msg)
        
        # Validate stop price
        stop_valid, stop_msg = self.validate_price(symbol, stop_price)
        if not stop_valid:
            self.errors.append(stop_msg)
        
        # Validate limit price
        limit_valid, limit_msg = self.validate_price(symbol, limit_price)
        if not limit_valid:
            self.errors.append(limit_msg)
        
        # Validate price relationship
        if stop_valid and limit_valid:
            # For BUY stop-limit: stop_price > limit_price
            # For SELL stop-limit: stop_price < limit_price
            # This will be validated in the order placement logic
        return len(self.errors) == 0
    
    def get_errors(self) -> list:
        """Get validation errors"""
        return self.errors
    
    def get_symbol_info(self, symbol: str) -> dict:
        """Get symbol information including min quantity and price precision"""
        symbol = symbol.upper().strip()
        
        return {
            'symbol': symbol,
            'min_quantity': self.MIN_QUANTITIES.get(symbol, self.MIN_QUANTITIES['DEFAULT']),
            'price_precision': self.PRICE_PRECISIONS.get(symbol, self.PRICE_PRECISIONS['DEFAULT']),
            'is_valid': bool(re.match(self.SYMBOL_PATTERN, symbol))
        }
