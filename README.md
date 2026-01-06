# 📈 Binance Futures Trading Bot

A comprehensive CLI and Web-based trading bot for Binance USDT-M Futures with support for multiple order types and strategies.

## ✨ Features

### 📊 Basic Orders
- **Market Orders** - Instant execution at best available price
- **Limit Orders** - Execution at specific price or better

### 🚀 Advanced Orders (Bonus Features)
- **Stop-Limit Orders** - Combine stop and limit orders
- **OCO Orders** - One-Cancels-the-Other (Take Profit + Stop Loss)
- **TWAP Strategy** - Time-Weighted Average Price execution
- **Grid Trading** - Automated buy-low/sell-high within range

### 🔒 Security & Validation
- Input validation for all parameters
- Structured logging with timestamps
- Error handling and reporting
- Secure API key management

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.8 or higher
- Binance Futures account with API key
- Git

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/binance-bot.git
cd binance-bot

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Binance API credentials
