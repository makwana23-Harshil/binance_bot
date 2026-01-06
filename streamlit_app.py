import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.binance_client import BinanceFuturesClient
from src.market_orders import MarketOrder
from src.limit_orders import LimitOrder
from src.advanced.stop_limit import StopLimitOrder
from src.advanced.oco import OCOOrder
from src.advanced.twap import TWAPStrategy
from src.advanced.grid import GridStrategy
from src.logger import TradingLogger
from src.validator import OrderValidator

# Page config
st.set_page_config(
    page_title="Binance Futures Trading Bot",
    page_icon="📈",
    layout="wide"
)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'client' not in st.session_state:
    st.session_state.client = None
if 'orders' not in st.session_state:
    st.session_state.orders = []
if 'balance' not in st.session_state:
    st.session_state.balance = 0

# Initialize logger
logger = TradingLogger()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .order-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 5px solid #1E88E5;
    }
    .success-message {
        color: #4CAF50;
        font-weight: bold;
    }
    .error-message {
        color: #F44336;
        font-weight: bold;
    }
    .balance-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">📈 Binance Futures Trading Bot</h1>', unsafe_allow_html=True)

# Sidebar for API Configuration
with st.sidebar:
    st.header("🔐 API Configuration")
    
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("API Secret", type="password")
    
    if st.button("Connect to Binance"):
        try:
            client = BinanceFuturesClient(api_key, api_secret)
            account_info = client.get_account_info()
            
            if account_info:
                st.session_state.client = client
                st.session_state.logged_in = True
                st.session_state.balance = account_info.get('totalWalletBalance', 0)
                st.success("✅ Successfully connected!")
                logger.log("SYSTEM", "User connected to Binance API")
            else:
                st.error("Failed to connect. Check API credentials.")
        except Exception as e:
            st.error(f"Connection failed: {str(e)}")
            logger.log("ERROR", f"Connection failed: {str(e)}")
    
    if st.session_state.logged_in:
        st.markdown("---")
        st.header("📊 Account Info")
        
        # Display balance
        st.markdown(f"""
        <div class="balance-card">
            <h3>💰 Total Balance</h3>
            <h2>${st.session_state.balance:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Refresh button
        if st.button("Refresh Balance"):
            try:
                account_info = st.session_state.client.get_account_info()
                st.session_state.balance = account_info.get('totalWalletBalance', 0)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to refresh: {str(e)}")
        
        st.markdown("---")
        st.header("📋 Order History")
        
        # Display recent orders
        if st.session_state.orders:
            df_orders = pd.DataFrame(st.session_state.orders[-5:])
            st.dataframe(df_orders[['symbol', 'side', 'type', 'quantity', 'status', 'timestamp']])
        
        # View logs button
        if st.button("View Logs"):
            try:
                with open('bot.log', 'r') as f:
                    logs = f.read()
                st.text_area("Trading Logs", logs, height=300)
            except:
                st.warning("No logs available yet")

# Main Content Area
if st.session_state.logged_in:
    # Create tabs for different order types
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Market Orders", 
        "🎯 Limit Orders", 
        "🛑 Stop-Limit", 
        "🔄 OCO Orders", 
        "⏱️ TWAP", 
        "📊 Grid Trading"
    ])
    
    # Tab 1: Market Orders
    with tab1:
        st.header("Market Orders")
        
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.text_input("Symbol (e.g., BTCUSDT)", value="BTCUSDT", key="market_symbol")
            side = st.selectbox("Side", ["BUY", "SELL"], key="market_side")
            quantity = st.number_input("Quantity", min_value=0.001, value=0.01, step=0.001, key="market_qty")
            
            if st.button("Place Market Order", key="market_btn"):
                try:
                    # Validate inputs
                    validator = OrderValidator()
                    if validator.validate_market_order(symbol, quantity):
                        market_order = MarketOrder(st.session_state.client)
                        result = market_order.place_order(
                            symbol=symbol,
                            side=side,
                            quantity=quantity
                        )
                        
                        if result['status'] == 'FILLED':
                            st.session_state.orders.append({
                                **result,
                                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            st.success(f"✅ Market order placed successfully!")
                            st.json(result)
                            logger.log("ORDER", f"Market {side} {quantity} {symbol}: {result}")
                        else:
                            st.error(f"Order failed: {result.get('msg', 'Unknown error')}")
                    else:
                        st.error("Validation failed. Check your inputs.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    logger.log("ERROR", f"Market order failed: {str(e)}")
        
        with col2:
            st.markdown("""
            ### ℹ️ About Market Orders
            
            **Market orders** are executed immediately at the best available current price.
            
            **Features:**
            - Instant execution
            - No price guarantee
            - Best for quick entries/exits
            - Subject to slippage
            
            **Use when:**
            - Speed is critical
            - Trading liquid markets
            - Accepting current market price
            """)
    
    # Tab 2: Limit Orders
    with tab2:
        st.header("Limit Orders")
        
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.text_input("Symbol (e.g., BTCUSDT)", value="BTCUSDT", key="limit_symbol")
            side = st.selectbox("Side", ["BUY", "SELL"], key="limit_side")
            quantity = st.number_input("Quantity", min_value=0.001, value=0.01, step=0.001, key="limit_qty")
            price = st.number_input("Price", min_value=0.01, value=50000.0, step=1.0, key="limit_price")
            
            if st.button("Place Limit Order", key="limit_btn"):
                try:
                    validator = OrderValidator()
                    if validator.validate_limit_order(symbol, quantity, price):
                        limit_order = LimitOrder(st.session_state.client)
                        result = limit_order.place_order(
                            symbol=symbol,
                            side=side,
                            quantity=quantity,
                            price=price
                        )
                        
                        if result['status'] == 'NEW':
                            st.session_state.orders.append({
                                **result,
                                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            st.success(f"✅ Limit order placed successfully!")
                            st.json(result)
                            logger.log("ORDER", f"Limit {side} {quantity} {symbol} @ {price}: {result}")
                        else:
                            st.error(f"Order failed: {result.get('msg', 'Unknown error')}")
                    else:
                        st.error("Validation failed. Check your inputs.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    logger.log("ERROR", f"Limit order failed: {str(e)}")
        
        with col2:
            # Get current price
            try:
                ticker = st.session_state.client.get_ticker(symbol)
                current_price = float(ticker['lastPrice'])
                st.metric("Current Price", f"${current_price:,.2f}")
                
                # Price comparison
                if 'price' in locals():
                    diff_percent = ((price - current_price) / current_price) * 100
                    st.metric("Price Difference", f"{diff_percent:.2f}%")
            except:
                st.info("Enter a valid symbol to see price data")
            
            st.markdown("""
            ### ℹ️ About Limit Orders
            
            **Limit orders** execute only at your specified price or better.
            
            **Features:**
            - Price control
            - No slippage
            - May not fill immediately
            - Good for specific price targets
            
            **Use when:**
            - You have a target price
            - Willing to wait for execution
            - Avoiding slippage
            """)
    
    # Tab 3: Stop-Limit Orders
    with tab3:
        st.header("Stop-Limit Orders")
        
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.text_input("Symbol", value="BTCUSDT", key="stop_symbol")
            side = st.selectbox("Side", ["BUY", "SELL"], key="stop_side")
            quantity = st.number_input("Quantity", min_value=0.001, value=0.01, step=0.001, key="stop_qty")
            stop_price = st.number_input("Stop Price", min_value=0.01, value=52000.0, step=1.0, key="stop_price")
            limit_price = st.number_input("Limit Price", min_value=0.01, value=51950.0, step=1.0, key="limit_price2")
            
            if st.button("Place Stop-Limit Order", key="stop_btn"):
                try:
                    validator = OrderValidator()
                    if validator.validate_stop_limit_order(symbol, quantity, stop_price, limit_price):
                        stop_limit = StopLimitOrder(st.session_state.client)
                        result = stop_limit.place_order(
                            symbol=symbol,
                            side=side,
                            quantity=quantity,
                            stop_price=stop_price,
                            limit_price=limit_price
                        )
                        
                        if result['status'] == 'NEW':
                            st.session_state.orders.append({
                                **result,
                                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            st.success(f"✅ Stop-Limit order placed successfully!")
                            st.json(result)
                            logger.log("ORDER", f"Stop-Limit {side} {quantity} {symbol}: {result}")
                        else:
                            st.error(f"Order failed: {result.get('msg', 'Unknown error')}")
                    else:
                        st.error("Validation failed. Check your inputs.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    logger.log("ERROR", f"Stop-Limit order failed: {str(e)}")
        
        with col2:
            st.markdown("""
            ### ℹ️ About Stop-Limit Orders
            
            **Stop-Limit orders** combine stop and limit orders.
            
            **How it works:**
            1. When stop price is reached → becomes a limit order
            2. Executes at limit price or better
            
            **Features:**
            - Risk management
            - Price protection
            - Two-stage execution
            
            **Common use:**
            - Stop losses with price limits
            - Breakout entries
            - Risk-controlled exits
            """)
    
    # Tab 4: OCO Orders
    with tab4:
        st.header("OCO (One-Cancels-the-Other) Orders")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            symbol = st.text_input("Symbol", value="BTCUSDT", key="oco_symbol")
            side = st.selectbox("Side", ["BUY", "SELL"], key="oco_side")
            quantity = st.number_input("Quantity", min_value=0.001, value=0.01, step=0.001, key="oco_qty")
            
            st.subheader("Take Profit Order")
            take_profit_price = st.number_input("Take Profit Price", min_value=0.01, value=53000.0, step=1.0)
            
            st.subheader("Stop Loss Order")
            stop_loss_price = st.number_input("Stop Loss Price", min_value=0.01, value=49000.0, step=1.0)
            stop_limit_price = st.number_input("Stop Limit Price", min_value=0.01, value=48950.0, step=1.0)
            
            if st.button("Place OCO Order", key="oco_btn"):
                try:
                    oco_order = OCOOrder(st.session_state.client)
                    result = oco_order.place_order(
                        symbol=symbol,
                        side=side,
                        quantity=quantity,
                        price=take_profit_price,
                        stop_price=stop_loss_price,
                        stop_limit_price=stop_limit_price
                    )
                    
                    if result:
                        st.success(f"✅ OCO order placed successfully!")
                        st.json(result)
                        logger.log("ORDER", f"OCO {side} {quantity} {symbol}: {result}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    logger.log("ERROR", f"OCO order failed: {str(e)}")
        
        with col2:
            st.markdown("""
            ### ℹ️ About OCO Orders
            
            **OCO orders** place two orders simultaneously:
            
            1. **Take Profit** (limit order)
            2. **Stop Loss** (stop-limit order)
            
            **Features:**
            - Automatic risk management
            - Two orders, one cancels other
            - Set and forget strategy
            
            **Perfect for:**
            - Position management
            - Risk-reward optimization
            - Automated exit strategy
            """)
    
    # Tab 5: TWAP Strategy
    with tab5:
        st.header("TWAP (Time-Weighted Average Price)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.text_input("Symbol", value="BTCUSDT", key="twap_symbol")
            side = st.selectbox("Side", ["BUY", "SELL"], key="twap_side")
            total_quantity = st.number_input("Total Quantity", min_value=0.01, value=0.1, step=0.01)
            duration_hours = st.slider("Duration (hours)", 1, 24, 4)
            chunks = st.slider("Number of Chunks", 2, 100, 10)
            
            if st.button("Start TWAP Strategy", key="twap_btn"):
                try:
                    twap = TWAPStrategy(st.session_state.client)
                    result = twap.execute(
                        symbol=symbol,
                        side=side,
                        total_quantity=total_quantity,
                        duration_hours=duration_hours,
                        chunks=chunks
                    )
                    
                    if result:
                        st.success(f"✅ TWAP strategy started!")
                        
                        # Display execution plan
                        df_plan = pd.DataFrame(result['execution_plan'])
                        st.dataframe(df_plan)
                        
                        # Progress bar
                        progress_bar = st.progress(0)
                        
                        # Simulate execution (in real app, this would be async)
                        for i in range(chunks):
                            time.sleep(0.1)  # Simulate delay
                            progress_bar.progress((i + 1) / chunks)
                        
                        st.success("Strategy completed!")
                        logger.log("STRATEGY", f"TWAP {side} {total_quantity} {symbol}: {result}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    logger.log("ERROR", f"TWAP failed: {str(e)}")
        
        with col2:
            st.markdown("""
            ### ℹ️ About TWAP
            
            **TWAP** splits large orders into smaller chunks over time.
            
            **Benefits:**
            - Reduces market impact
            - Averages entry/exit price
            - Avoids price manipulation
            
            **How it works:**
            1. Divide total quantity into N chunks
            2. Execute chunks at regular intervals
            3. Achieve average market price
            
            **Ideal for:**
            - Large orders
            - Illiquid markets
            - Minimizing slippage
            """)
            
            # TWAP calculation example
            if 'total_quantity' in locals() and 'chunks' in locals():
                chunk_size = total_quantity / chunks
                st.metric("Chunk Size", f"{chunk_size:.4f}")
                interval = duration_hours * 60 / chunks
                st.metric("Interval (min)", f"{interval:.1f}")
    
    # Tab 6: Grid Trading
    with tab6:
        st.header("Grid Trading Strategy")
        
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.text_input("Symbol", value="BTCUSDT", key="grid_symbol")
            grid_type = st.selectbox("Grid Type", ["Arithmetic", "Geometric"])
            
            st.subheader("Price Range")
            lower_price = st.number_input("Lower Price", min_value=0.01, value=48000.0, step=1.0)
            upper_price = st.number_input("Upper Price", min_value=0.01, value=52000.0, step=1.0)
            
            st.subheader("Grid Settings")
            grid_lines = st.slider("Number of Grid Lines", 2, 50, 10)
            order_qty = st.number_input("Order Quantity per Grid", min_value=0.001, value=0.005, step=0.001)
            
            if st.button("Start Grid Trading", key="grid_btn"):
                try:
                    grid = GridStrategy(st.session_state.client)
                    result = grid.setup_grid(
                        symbol=symbol,
                        lower_price=lower_price,
                        upper_price=upper_price,
                        grid_lines=grid_lines,
                        order_qty=order_qty,
                        grid_type=grid_type
                    )
                    
                    if result:
                        st.success(f"✅ Grid strategy set up!")
                        
                        # Display grid levels
                        df_grid = pd.DataFrame(result['grid_levels'])
                        st.dataframe(df_grid)
                        
                        # Visualization
                        fig = go.Figure()
                        
                        # Add price range
                        fig.add_shape(
                            type="rect",
                            x0=0, x1=1,
                            y0=lower_price, y1=upper_price,
                            fillcolor="lightblue",
                            opacity=0.2,
                            line_width=0
                        )
                        
                        # Add grid lines
                        for level in result['grid_levels']:
                            fig.add_hline(
                                y=level['price'],
                                line_dash="dot",
                                line_color="gray",
                                opacity=0.5
                            )
                        
                        # Add buy/sell markers
                        buy_levels = [level['price'] for level in result['grid_levels'] if level['side'] == 'BUY']
                        sell_levels = [level['price'] for level in result['grid_levels'] if level['side'] == 'SELL']
                        
                        fig.add_trace(go.Scatter(
                            x=[0.5] * len(buy_levels),
                            y=buy_levels,
                            mode='markers',
                            marker=dict(symbol='triangle-up', size=15, color='green'),
                            name='Buy Levels'
                        ))
                        
                        fig.add_trace(go.Scatter(
                            x=[0.5] * len(sell_levels),
                            y=sell_levels,
                            mode='markers',
                            marker=dict(symbol='triangle-down', size=15, color='red'),
                            name='Sell Levels'
                        ))
                        
                        fig.update_layout(
                            title="Grid Trading Levels",
                            yaxis_title="Price",
                            showlegend=True,
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        logger.log("STRATEGY", f"Grid {symbol} {lower_price}-{upper_price}: {result}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    logger.log("ERROR", f"Grid setup failed: {str(e)}")
        
        with col2:
            st.markdown("""
            ### ℹ️ About Grid Trading
            
            **Grid trading** places multiple buy/sell orders within a price range.
            
            **Strategy:**
            - Buy low, sell high automatically
            - Profits from volatility
            - Continuous trading within range
            
            **How it works:**
            1. Define price range
            2. Place limit orders at grid levels
            3. Automatically execute when prices hit levels
            
            **Best for:**
            - Range-bound markets
            - High volatility
            - Automated profit-taking
            """)
            
            # Grid stats
            if 'grid_lines' in locals() and 'lower_price' in locals() and 'upper_price' in locals():
                price_range = upper_price - lower_price
                grid_spacing = price_range / (grid_lines - 1)
                st.metric("Price Range", f"${price_range:,.2f}")
                st.metric("Grid Spacing", f"${grid_spacing:,.2f}")
                
                estimated_profit = grid_spacing * order_qty * (grid_lines - 1)
                st.metric("Estimated Profit per Cycle", f"${estimated_profit:.2f}")

else:
    # Login prompt
    st.info("👈 Please configure your API credentials in the sidebar to start trading.")
    
    # Features overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 📊 Basic Orders
        - Market Orders
        - Limit Orders
        - Real-time validation
        """)
    
    with col2:
        st.markdown("""
        ### 🚀 Advanced Orders
        - Stop-Limit Orders
        - OCO Orders
        - TWAP Strategy
        - Grid Trading
        """)
    
    with col3:
        st.markdown("""
        ### 🔒 Security Features
        - Secure API handling
        - Input validation
        - Comprehensive logging
        - Error handling
        """)
    
    # Instructions
    st.markdown("---")
    st.markdown("""
    ### 📋 Getting Started
    
    1. **Get API Keys** from Binance:
       - Go to Binance → API Management
       - Create new API key with Futures permission
       - Save your API Key and Secret
    
    2. **Configure in sidebar**:
       - Enter API credentials
       - Click "Connect to Binance"
    
    3. **Start trading**:
       - Choose order type from tabs
       - Configure parameters
       - Place orders securely
    
    ⚠️ **Note**: This is a demo application. Use at your own risk with small amounts first.
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: gray;">
        <p>Binance Futures Trading Bot • Made with Streamlit • For Educational Purposes</p>
        <p>⚠️ Trading involves risk. Past performance doesn't guarantee future results.</p>
    </div>
    """,
    unsafe_allow_html=True
)
