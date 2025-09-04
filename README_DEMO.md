# Tokenized Weather API Demo

This project demonstrates how API access can be tokenized using Algorand blockchain technology. AI agents can autonomously purchase and use blockchain tokens to access weather data, creating a new paradigm for API monetization.

## 🎯 What This Demo Shows

- **Tokenized API Access**: Weather data access controlled by blockchain tokens
- **AI Agent Autonomy**: Agents automatically purchase tokens when needed
- **Real Data Integration**: Uses live OpenWeather API data
- **Smart Contract Marketplace**: Decentralized token distribution
- **MCP-style Backend**: Server proxy with blockchain validation

## 🏗️ Architecture

```
AI Agent ←→ MCP Backend ←→ OpenWeather API
    ↕            ↕
Algorand LocalNet ←→ Smart Contract
```

- **AI Agent**: Python script that autonomously buys and uses tokens
- **MCP Backend**: FastAPI server with token validation
- **Smart Contract**: AlgoPy contract managing token marketplace
- **OpenWeather API**: Live weather data source

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker
- AlgoKit CLI 2.0+
- **No API keys required!** (Uses free Open-Meteo API by default)

### Setup

1. **Run the automated setup**:
   ```bash
   python scripts/setup_demo.py
   ```

2. **Run the demo** (no additional setup needed!):
   ```bash
   ./scripts/run_demo.sh
   ```

## 📋 Manual Setup (Alternative)

If you prefer manual setup:

### 1. Start LocalNet
```bash
algokit localnet start
```

### 2. Deploy Smart Contract
```bash
cd projects/python-hello-world-contracts
poetry install
algokit project run build
algokit project deploy localnet
```

### 3. Setup Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# No API key needed for Open-Meteo! 
python main.py
```

### 4. Setup Agent
```bash
cd agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python agent.py
```

## 🔧 Configuration

### Backend Configuration (`backend/.env`)
```env
# Weather API Provider (open-meteo is free with no limits!)
WEATHER_API_PROVIDER=open-meteo

# Algorand Configuration  
ALGOD_SERVER=http://localhost:4001
ALGOD_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
INDEXER_SERVER=http://localhost:8980
INDEXER_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
MARKETPLACE_APP_ID=1
WEATHER_ASA_ID=2

# Optional: Other weather providers
# WEATHER_API_PROVIDER=openweather
# OPENWEATHER_API_KEY=your_key_here
# WEATHER_API_PROVIDER=weatherapi  
# WEATHERAPI_KEY=your_key_here
```

### Agent Configuration (`agent/.env`)
```env
BACKEND_URL=http://localhost:8000
ALGOD_SERVER=http://localhost:4001
ALGOD_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
MARKETPLACE_APP_ID=1
WEATHER_ASA_ID=2
```

## 🎮 Demo Workflow

1. **Initial State**: Agent has no weather tokens
2. **First Request**: Agent tries to get weather data → **403 Forbidden**
3. **Token Purchase**: Agent automatically buys weather access token for 10 ALGO
4. **Retry Request**: Agent tries again → **200 Success** with weather data
5. **Repeat**: Agent continues with different cities using purchased tokens

## 📊 Expected Output

```
🤖 Starting Weather Agent Demo
Testing cities: ['Berlin', 'New York', 'Tokyo', 'London', 'Sydney']

--- Request 1/5: Berlin ---
❌ Access denied: No valid weather access token found for this wallet
💰 Purchasing weather access token...
✅ Successfully purchased weather token! TxID: ABC123...
✅ Berlin: 22.5°C, partly cloudy

--- Request 2/5: New York ---
✅ New York: 18.1°C, clear sky

...

==================================================
WEATHER AGENT STATISTICS
==================================================
Wallet Address: ABCD1234...
Balance: 990.000000 ALGO
Weather Tokens Owned: 1
Total Requests: 5
Successful Requests: 5
Tokens Purchased: 1
Success Rate: 100.0%
==================================================
```

## 🏗️ Smart Contract Details

### WeatherMarketplace Contract
- **Language**: AlgoPy (Python for Algorand)
- **Features**: 
  - ASA creation for weather tokens
  - Token purchase with ALGO payment
  - Access validation
  - Admin functions

### Token Economics
- **Price**: 10 ALGO per token
- **Duration**: 1 hour (configurable)
- **Type**: ASA (Algorand Standard Asset)
- **Symbol**: OWAT (OpenWeather Access Token)

## 🔍 API Endpoints

### Backend Server (Port 8000)
- `GET /health` - System health check
- `GET /weather?city=Berlin&wallet=ADDR123` - Get weather (token required)
- `GET /tokens/{wallet_address}` - View owned tokens

### Smart Contract Methods
- `create_weather_asa()` - Create the weather token ASA
- `buy_weather_token()` - Purchase a weather token
- `validate_token_access()` - Check token ownership
- `get_token_info()` - Get contract information

## 🧪 Testing

### Unit Tests
```bash
cd projects/python-hello-world-contracts
poetry run pytest

cd backend
./venv/bin/python -m pytest

cd agent
./venv/bin/python -m pytest
```

### Integration Tests
```bash
# Start all services first
./scripts/run_demo.sh

# Run integration tests
python tests/test_integration.py
```

## 🛠️ Troubleshooting

### Common Issues

1. **"LocalNet not running"**
   ```bash
   algokit localnet reset
   algokit localnet start
   ```

2. **"Weather API error"**
   - Default Open-Meteo should work without configuration
   - If using other providers, check API keys in `backend/.env`

3. **"Smart contract not found"**
   - Redeploy contracts: `algokit project deploy localnet`
   - Update app IDs in environment files

4. **"Agent insufficient balance"**
   - Fund the agent wallet with LocalNet ALGOs
   - Use AlgoKit dispenser or LocalNet faucet

### Logs
- Backend: `backend/backend.log`
- Agent: Console output
- LocalNet: `algokit localnet logs`

## 🔮 Future Enhancements

### Implemented in Technical Spec
- Multi-API support (Weather + Air Quality + UV)
- Usage-based tokens (N calls per token)
- Secondary market for token trading
- Subscription model options
- Real-time WebSocket updates

### Frontend Dashboard
- React-based marketplace UI
- Token portfolio management
- Usage analytics and charts
- Real-time trading interface

## 📚 Documentation

- [Technical Specification](docs/TECHNICAL_SPECIFICATION.md)
- [API Documentation](docs/API_SPECIFICATION.md)
- [Architecture Guide](docs/ARCHITECTURE.md)
- [Smart Contract Code](projects/python-hello-world-contracts/smart_contracts/weather_marketplace/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is for demonstration purposes. Check individual components for their specific licenses.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the documentation in `/docs`
3. Open an issue with detailed error logs

---

**Happy tokenizing! 🎉**