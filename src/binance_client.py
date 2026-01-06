import hmac
import hashlib
import requests
import json
from typing import Dict, Optional, List
from urllib.parse import urlencode
import time


class BinanceFuturesClient:
    """Binance USDT-M Futures API client"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = False):
        self.api_key = api_key
        self.api_secret = api_secret
        
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"
        else:
            self.base_url = "https://fapi.binance.com"
        
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': api_key
        })
    
    def _generate_signature(self, data: Dict) -> str:
        """Generate HMAC SHA256 signature"""
        query_string = urlencode(data)
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _request(self, method: str, endpoint: str, signed: bool = False, **kwargs) -> Dict:
        """Make HTTP request to Binance API"""
        url = f"{self.base_url}{endpoint}"
        
        if signed:
            kwargs['timestamp'] = int(time.time() * 1000)
            kwargs['signature'] = self._generate_signature(kwargs)
        
        if method == 'GET':
            response = self.session.get(url, params=kwargs)
        elif method == 'POST':
            response = self.session.post(url, data=kwargs)
        elif method == 'DELETE':
            response = self.session.delete(url, params=kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    def get_account_info(self) -> Dict:
        """Get account information"""
        try:
            return self._request('GET', '/fapi/v2/account', signed=True)
        except Exception as e:
            print(f"Error getting account info: {e}")
            return {}
    
    def get_ticker(self, symbol: str) -> Dict:
        """Get symbol ticker price"""
        try:
            response = self._request('GET', '/fapi/v1/ticker/24hr', symbol=symbol)
            return response
        except Exception as e:
            print(f"Error getting ticker for {symbol}: {e}")
            return {}
    
    def get_order_book(self, symbol: str, limit: int = 10) -> Dict:
        """Get order book depth"""
        try:
            return self._request('GET', '/fapi/v1/depth', symbol=symbol, limit=limit)
        except Exception as e:
            print(f"Error getting order book: {e}")
            return {}
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get all open orders"""
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol
            return self._request('GET', '/fapi/v1/openOrders', signed=True, **params)
        except Exception as e:
            print(f"Error getting open orders: {e}")
            return []
    
    def get_position_info(self, symbol: str = None) -> List[Dict]:
        """Get position information"""
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol
            return self._request('GET', '/fapi/v2/positionRisk', signed=True, **params)
        except Exception as e:
            print(f"Error getting position info: {e}")
            return []
    
    def new_order(self, **kwargs) -> Dict:
        """Place a new order"""
        try:
            return self._request('POST', '/fapi/v1/order', signed=True, **kwargs)
        except Exception as e:
            print(f"Error placing order: {e}")
            return {'error': str(e)}
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """Cancel an existing order"""
        try:
            return self._request('DELETE', '/fapi/v1/order', signed=True, 
                               symbol=symbol, orderId=order_id)
        except Exception as e:
            print(f"Error canceling order: {e}")
            return {'error': str(e)}
    
    def new_oco_order(self, **kwargs) -> Dict:
        """Place OCO order"""
        try:
            return self._request('POST', '/fapi/v1/order/oco', signed=True, **kwargs)
        except Exception as e:
            print(f"Error placing OCO order: {e}")
            return {'error': str(e)}
    
    def get_oco_orders(self, **kwargs) -> List[Dict]:
        """Get OCO orders"""
        try:
            return self._request('GET', '/fapi/v1/allOrderList', signed=True, **kwargs)
        except Exception as e:
            print(f"Error getting OCO orders: {e}")
            return []
