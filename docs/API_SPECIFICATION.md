# API Specification: Tokenized Weather Access

## Base URL
```
http://localhost:8000
```

## Authentication
All endpoints requiring token validation use wallet address authentication. The wallet address must own a valid OpenWeather access token.

## Endpoints

### 1. Weather Data Retrieval

#### `GET /weather`
Retrieves current weather data for a specified city, gated by token ownership.

**Parameters:**
- `city` (string, required): City name (e.g., "Berlin", "New York")
- `wallet` (string, required): Algorand wallet address (Base32 encoded)

**Example Request:**
```http
GET /weather?city=Berlin&wallet=ABCDEF123456789GHIJKLMNOPQRSTUVWXYZ234567890ABCDEFGHIJK
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "city": "Berlin",
    "country": "DE",
    "temperature": 22.5,
    "feels_like": 24.1,
    "humidity": 65,
    "pressure": 1013,
    "description": "partly cloudy",
    "wind_speed": 3.2,
    "wind_direction": 180,
    "visibility": 10000,
    "uv_index": 5
  },
  "token_info": {
    "token_id": "789012",
    "remaining_time_seconds": 2850,
    "expires_at": "2024-12-01T15:30:00Z"
  },
  "timestamp": "2024-12-01T14:25:00Z"
}
```

**Error Response (403 Forbidden):**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_TOKEN",
    "message": "No valid weather access token found for this wallet",
    "details": {
      "wallet_address": "ABCDEF...",
      "required_token_type": "OpenWeather Access Token",
      "marketplace_info": {
        "contract_id": "123456",
        "token_price_algo": 10,
        "purchase_endpoint": "/marketplace/buy"
      }
    }
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CITY",
    "message": "City not found or invalid city name",
    "details": {
      "provided_city": "InvalidCity123"
    }
  }
}
```

### 2. Token Information

#### `GET /tokens/{wallet_address}`
Retrieves information about tokens owned by a specific wallet.

**Parameters:**
- `wallet_address` (string, path): Algorand wallet address

**Example Request:**
```http
GET /tokens/ABCDEF123456789GHIJKLMNOPQRSTUVWXYZ234567890ABCDEFGHIJK
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "wallet_address": "ABCDEF123456789GHIJKLMNOPQRSTUVWXYZ234567890ABCDEFGHIJK",
  "tokens": [
    {
      "asset_id": "789012",
      "asset_name": "OpenWeather Access Token",
      "symbol": "OWAT",
      "balance": 1,
      "expires_at": "2024-12-01T15:30:00Z",
      "remaining_time_seconds": 2850,
      "status": "valid",
      "purchase_time": "2024-12-01T14:30:00Z",
      "total_uses": 0,
      "max_uses": 1
    }
  ],
  "summary": {
    "total_tokens": 1,
    "valid_tokens": 1,
    "expired_tokens": 0
  }
}
```

### 3. Health Check

#### `GET /health`
System health and status information.

**Example Request:**
```http
GET /health
```

**Success Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "algorand_node": {
      "status": "connected",
      "network": "localnet",
      "last_round": 12345
    },
    "openweather_api": {
      "status": "available",
      "rate_limit_remaining": 950
    },
    "database": {
      "status": "connected",
      "pending_transactions": 0
    }
  },
  "contract_info": {
    "marketplace_app_id": "123456",
    "weather_token_asa_id": "789012"
  },
  "timestamp": "2024-12-01T14:25:00Z"
}
```

### 4. Marketplace Operations

#### `POST /marketplace/buy`
Purchases a weather access token through the smart contract.

**Request Body:**
```json
{
  "buyer_wallet": "ABCDEF123456789GHIJKLMNOPQRSTUVWXYZ234567890ABCDEFGHIJK",
  "payment_txn": "gqNzaWfEQE...",
  "quantity": 1
}
```

**Success Response (201 Created):**
```json
{
  "success": true,
  "transaction": {
    "txn_id": "ABC123DEF456...",
    "block": 12346,
    "token_id": "789013",
    "buyer": "ABCDEF123456789GHIJKLMNOPQRSTUVWXYZ234567890ABCDEFGHIJK",
    "price_paid_algo": 10,
    "expires_at": "2024-12-01T16:30:00Z"
  }
}
```

#### `GET /marketplace/list`
Lists available tokens for purchase.

**Query Parameters:**
- `limit` (integer, optional): Maximum number of results (default: 50)
- `sort` (string, optional): Sort by "price", "expiry", "created" (default: "created")

**Success Response (200 OK):**
```json
{
  "success": true,
  "tokens": [
    {
      "token_id": "789014",
      "price_algo": 10,
      "expires_at": "2024-12-01T17:00:00Z",
      "seller": "marketplace_contract",
      "created_at": "2024-12-01T14:00:00Z"
    }
  ],
  "pagination": {
    "total": 25,
    "limit": 50,
    "offset": 0
  }
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_TOKEN` | 403 | Wallet doesn't own valid access token |
| `TOKEN_EXPIRED` | 403 | Access token has expired |
| `INVALID_WALLET` | 400 | Wallet address format invalid |
| `INVALID_CITY` | 400 | City name not found or invalid |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `OPENWEATHER_ERROR` | 502 | OpenWeather API unavailable |
| `BLOCKCHAIN_ERROR` | 502 | Algorand network issue |
| `INSUFFICIENT_FUNDS` | 402 | Not enough ALGO for purchase |

## Rate Limits

- **Weather API**: 100 requests per hour per wallet
- **Token Info**: 1000 requests per hour per IP
- **Health Check**: No limit
- **Marketplace**: 10 purchases per hour per wallet

## WebSocket Support (Future)

### `WS /ws/weather-updates`
Real-time weather updates for token holders (planned feature).

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/weather-updates?wallet=ABC123...');
```

**Message Format:**
```json
{
  "type": "weather_update",
  "city": "Berlin",
  "data": {
    "temperature": 23.1,
    "timestamp": "2024-12-01T14:30:00Z"
  }
}
```

## SDK Examples

### Python SDK Usage
```python
import requests

# Get weather data
response = requests.get(
    "http://localhost:8000/weather",
    params={
        "city": "Berlin",
        "wallet": "ABCDEF123456789GHIJKLMNOPQRSTUVWXYZ234567890ABCDEFGHIJK"
    }
)

if response.status_code == 200:
    weather_data = response.json()
    print(f"Temperature: {weather_data['data']['temperature']}°C")
elif response.status_code == 403:
    error_info = response.json()
    print(f"Need to buy token: {error_info['error']['details']['marketplace_info']}")
```

### JavaScript/Node.js Example
```javascript
const axios = require('axios');

async function getWeather(city, walletAddress) {
  try {
    const response = await axios.get('http://localhost:8000/weather', {
      params: { city, wallet: walletAddress }
    });
    return response.data;
  } catch (error) {
    if (error.response?.status === 403) {
      console.log('Need to purchase access token');
      return error.response.data;
    }
    throw error;
  }
}
```

## Postman Collection

A complete Postman collection is available at `/docs/postman_collection.json` for testing all endpoints.