# 🌤️ Weather Marketplace Frontend

A React-based frontend for the tokenized weather API demo on Algorand. This frontend provides a user-friendly interface to demonstrate token-gated access to weather data.

## Features

### 🔐 Account Management
- **Generate Account**: Create new Algorand accounts for testing
- **Load LocalNet Account**: Connect to pre-funded LocalNet accounts 
- **Balance Display**: Real-time ALGO balance monitoring
- **Access Status**: Clear indication of API access eligibility (5+ ALGO required)

### 💰 Fund Management
- **Drain Account**: Reduce balance below 5 ALGO threshold to test rejection
- **Fund Account**: Restore balance above threshold to regain access
- **Transaction Handling**: Full Algorand transaction lifecycle with confirmations

### 🌍 Weather Data Access
- **City Selection**: Choose any city for weather data
- **Token-Gated Requests**: API access controlled by account balance
- **Weather Display**: Temperature, humidity, wind speed, and more
- **Token Expiry**: Live countdown of API access token

## Prerequisites

1. **LocalNet Running**: 
   ```bash
   cd /home/gengar/Documents/research/algorand/aaaa/python-fullstack/scripts
   python setup_demo.py
   ```

2. **Backend Server Running**:
   ```bash
   cd ../../backend
   ./venv/bin/python main.py
   ```

## Quick Start

1. **Install Dependencies** (already done):
   ```bash
   cd frontend
   npm install
   ```

2. **Start the Frontend**:
   ```bash
   npm start
   ```

3. **Open Browser**: Navigate to `http://localhost:3000`

## Usage Flow

### Initial Setup
1. Click "Generate New Account" or "Load LocalNet Account"
2. Wait for balance to load (LocalNet accounts come pre-funded)

### Testing Rejection Scenario
1. Click "Drain Account (Test)" to reduce balance below 5 ALGO
2. Try to fetch weather data - should receive "Access Denied" error
3. Observe the red "❌ Denied" access status

### Testing Success Scenario  
1. Click "Fund Account Back" to restore balance above 5 ALGO
2. Enter a city name (default: London)
3. Click "Get Weather Data" to retrieve weather information
4. View detailed weather display with token expiry information

## Technical Details

### Architecture
- **Frontend**: React + TypeScript
- **Blockchain**: Algorand SDK for account management and transactions
- **API**: Axios for backend communication
- **Styling**: Custom CSS with glass morphism design

### Key Components
- **Account Management**: Generate/load accounts, balance tracking
- **Transaction Handling**: Payment transactions for fund management
- **API Integration**: Weather data requests with wallet authentication
- **Error Handling**: Comprehensive error messages and loading states

### Security Features
- **Client-side Key Management**: Private keys handled securely in memory
- **Balance Verification**: Real-time balance checking before API calls
- **Transaction Confirmation**: Waits for blockchain confirmation
- **Token Expiry**: Time-limited API access tokens

## API Integration

The frontend communicates with the backend at `http://localhost:8000`:

- **GET /weather**: Retrieve weather data for a city
  - Query params: `city` (string), `wallet` (Algorand address)
  - Returns: Weather data + token information
  - Requires: 5+ ALGO balance in wallet

- **GET /health**: Backend health check

## Configuration

Key constants in `App.tsx`:
```typescript
const ALGOD_SERVER = 'http://localhost:4001';      // LocalNet Algod
const BACKEND_URL = 'http://localhost:8000';       // Backend API  
const MINIMUM_BALANCE = 5;                         // 5 ALGO minimum
```

## Troubleshooting

### Common Issues

1. **"Failed to load LocalNet account"**
   - Ensure LocalNet is running: `algokit localnet status`
   - Check KMD is accessible at `http://localhost:4002`

2. **"Cannot connect to backend"**  
   - Start backend server: `cd ../../backend && ./venv/bin/python main.py`
   - Verify backend is running at `http://localhost:8000/health`

3. **"Access denied" with sufficient balance**
   - Refresh account balance
   - Check backend logs for detailed error information
   - Ensure balance is exactly 5.00+ ALGO

4. **Transaction failures**
   - Check account has sufficient balance for transaction fees
   - Verify LocalNet is processing transactions
   - Try refreshing the page and reconnecting account

### Development Mode

To run in development mode with hot reloading:
```bash
npm start
```

The app will automatically open at `http://localhost:3000` and reload on changes.

## Demo Scenarios

### Scenario 1: New User Experience
1. Generate new account (starts with 0 ALGO)
2. Try weather request → Access denied
3. Need to fund account first

### Scenario 2: LocalNet User Experience  
1. Load LocalNet account (pre-funded ~1000 ALGO)
2. Weather request succeeds immediately
3. Can test drain/fund cycle

### Scenario 3: Balance Testing
1. Start with funded account
2. Drain to ~2 ALGO → Access denied
3. Fund back to ~1000 ALGO → Access granted

This frontend provides a complete demonstration of blockchain-gated API access, showing both the user experience and technical implementation of token-based authentication.