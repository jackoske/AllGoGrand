# Technical Specification: Tokenized API Access Demo (OpenWeather + Algorand)

## 1. Overview

This project demonstrates how API access can be tokenized as Algorand Standard Assets (ASAs) and consumed by AI agents. The system uses real OpenWeather API data, gated by blockchain token ownership, creating a marketplace for API access rights.

## 2. System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   AI Agent      │◄──►│  Algorand        │◄──►│   Marketplace       │
│   (Python)      │    │  LocalNet        │    │   Smart Contract    │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
         │                                                   │
         │                                                   │
         ▼              Token Validation                     ▼
┌─────────────────┐    via Algorand SDK       ┌─────────────────────┐
│  MCP API Server │◄─────────────────────────►│  Token Registry     │
│  (FastAPI)      │                           │  (On-chain State)   │
│  + OpenWeather  │                           └─────────────────────┘
└─────────────────┘
```

## 3. Core Components

### 3.1 Smart Contract Layer
- **Technology**: Beaker (Python SDK for Algorand)
- **Contract Type**: ARC-4 compliant smart contract
- **Functions**:
  - `create_weather_token()`: Mints new weather access tokens
  - `buy_token()`: Purchases a token for ALGO
  - `validate_access()`: Checks token ownership for API access
  - `list_for_resale()`: Lists unused tokens for secondary market
  
### 3.2 Token Design
- **Asset Type**: Algorand Standard Asset (ASA)
- **Token Properties**:
  - Name: "OpenWeather Access Token"
  - Symbol: "OWAT"
  - Unit: 1 token = 1 hour of API access
  - Expiry: 1 hour from mint time
  - Total Supply: Configurable (e.g., 1000 tokens)

### 3.3 MCP Backend Server
- **Technology**: FastAPI (Python 3.12+)
- **Port**: 8000
- **Endpoints**:
  ```
  GET /weather?city={city}&wallet={address}
  GET /health
  GET /tokens/{wallet_address}
  ```
- **Middleware**: Token validation via Algorand SDK
- **External API**: OpenWeather API integration

### 3.4 AI Agent
- **Technology**: Python 3.12+ with Algorand SDK
- **Wallet**: Local wallet with test ALGO balance
- **Behavior**:
  1. Attempt API call
  2. If denied → purchase token
  3. Retry API call
  4. Optionally resell unused tokens

## 4. Data Flow

### 4.1 Initial Setup
1. Deploy marketplace contract to LocalNet
2. Create initial supply of weather access tokens
3. Fund agent wallet with test ALGOs
4. Start MCP backend server

### 4.2 Agent Request Cycle
1. **Weather Request**: Agent calls `/weather?city=Berlin&wallet={address}`
2. **Token Validation**: 
   - Backend queries Algorand network
   - Checks if wallet owns valid (non-expired) weather token
3. **API Call**: If valid → call OpenWeather API, return data
4. **Purchase Flow**: If invalid → agent buys token from marketplace
5. **Retry**: Agent retries weather request with valid token

### 4.3 Token Economics
- **Initial Price**: 10 ALGO per token
- **Duration**: 1 hour validity
- **Resale**: Tokens can be listed for secondary market
- **Expiry**: Automatic invalidation after 1 hour

## 5. Technical Stack

### 5.1 Blockchain
- **Network**: Algorand LocalNet (Docker-based)
- **SDK**: py-algorand-sdk
- **Smart Contract Framework**: Beaker
- **Standards**: ARC-4, ARC-56 for metadata

### 5.2 Backend
- **Framework**: FastAPI
- **Dependencies**:
  - `fastapi`
  - `uvicorn`
  - `py-algorand-sdk`
  - `requests` (OpenWeather API)
  - `pydantic`
  - `python-dotenv`

### 5.3 AI Agent
- **Dependencies**:
  - `py-algorand-sdk`
  - `requests`
  - `python-dotenv`

## 6. Environment Variables

```env
# OpenWeather API
OPENWEATHER_API_KEY=your_api_key_here

# Algorand LocalNet
ALGOD_SERVER=http://localhost:4001
ALGOD_TOKEN=your_token_here
INDEXER_SERVER=http://localhost:8980
INDEXER_TOKEN=your_token_here

# Contract
MARKETPLACE_APP_ID=123456
WEATHER_TOKEN_ASA_ID=789012

# Agent Configuration
AGENT_WALLET_MNEMONIC=your_mnemonic_here
AGENT_INITIAL_ALGO_BALANCE=1000
```

## 7. API Specifications

### 7.1 Weather Endpoint
```http
GET /weather?city={city}&wallet={wallet_address}

Response (Success - 200):
{
  "city": "Berlin",
  "temperature": 22.5,
  "humidity": 65,
  "description": "partly cloudy",
  "token_used": "789012",
  "remaining_time": 2850
}

Response (Unauthorized - 403):
{
  "error": "No valid weather access token found",
  "marketplace_contract": "123456",
  "token_price": "10 ALGO"
}
```

### 7.2 Token Info Endpoint
```http
GET /tokens/{wallet_address}

Response (200):
{
  "wallet": "ABC123...",
  "tokens": [
    {
      "asset_id": "789012",
      "expiry": "2024-12-01T15:30:00Z",
      "remaining_time": 2850,
      "valid": true
    }
  ]
}
```

## 8. Security Considerations

### 8.1 Token Security
- Tokens are non-transferable after first use (optional)
- Expiry timestamp stored on-chain
- Smart contract validates token ownership atomically

### 8.2 API Security
- OpenWeather API key stored server-side only
- Rate limiting on backend endpoints
- Wallet address validation

### 8.3 Smart Contract Security
- Input validation for all parameters
- Overflow protection for ALGO amounts
- Access control for admin functions

## 9. Testing Strategy

### 9.1 Unit Tests
- Smart contract function testing
- Backend API endpoint testing
- Agent purchase/validation logic

### 9.2 Integration Tests
- End-to-end workflow testing
- LocalNet deployment testing
- Token expiry handling

### 9.3 Load Testing
- Multiple simultaneous agent requests
- Marketplace scalability testing

## 10. Deployment Instructions

### 10.1 Prerequisites
```bash
# Install AlgoKit
curl -L https://github.com/algorandfoundation/algokit-cli/releases/latest/download/algokit-linux.tar.gz | tar -xz
sudo mv algokit /usr/local/bin/

# Start LocalNet
algokit localnet start

# Install dependencies
cd projects/python-hello-world-contracts
poetry install
```

### 10.2 Smart Contract Deployment
```bash
# Build and deploy contracts
algokit project run build
algokit project deploy localnet
```

### 10.3 Backend Server
```bash
# Start MCP server
cd backend/
python -m uvicorn main:app --reload --port 8000
```

### 10.4 Agent Simulation
```bash
# Run AI agent
cd agent/
python agent.py
```

## 11. Future Enhancements

### 11.1 Multi-API Support
- Weather + Air Quality + UV Index
- Different pricing tiers for different APIs
- Bundle deals for multiple API access

### 11.2 Advanced Token Mechanics
- Usage-based tokens (10 calls per token)
- Subscription model (monthly access)
- Dynamic pricing based on demand

### 11.3 Frontend Dashboard
- React-based marketplace UI
- Real-time token trading
- Analytics and usage metrics