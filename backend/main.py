"""
MCP Backend Server for Tokenized Weather API Access

This FastAPI server acts as a proxy between AI agents and the OpenWeather API,
with access control based on Algorand blockchain token ownership.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import requests
from algosdk import account, encoding
from algosdk.v2client import algod, indexer
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Tokenized Weather API",
    description="AI Agent Weather API with Blockchain Token Gating",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
WEATHER_API_PROVIDER = os.getenv("WEATHER_API_PROVIDER", "open-meteo")  # Default to free API
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY", "")
ALGOD_SERVER = os.getenv("ALGOD_SERVER", "http://localhost:4001")
ALGOD_TOKEN = os.getenv("ALGOD_TOKEN", "a" * 64)
INDEXER_SERVER = os.getenv("INDEXER_SERVER", "http://localhost:8980")
INDEXER_TOKEN = os.getenv("INDEXER_TOKEN", "a" * 64)
WEATHER_ASA_ID = int(os.getenv("WEATHER_ASA_ID", "0"))
MARKETPLACE_APP_ID = int(os.getenv("MARKETPLACE_APP_ID", "0"))

# Algorand clients
algod_client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_SERVER)
indexer_client = indexer.IndexerClient(INDEXER_TOKEN, INDEXER_SERVER)

# Weather API URLs
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1"
WEATHERAPI_BASE_URL = "https://api.weatherapi.com/v1"


# Pydantic models
class WeatherData(BaseModel):
    city: str
    country: str
    temperature: float
    feels_like: float
    humidity: int
    pressure: float  # Changed from int to float
    description: str
    wind_speed: float
    wind_direction: int
    visibility: int
    uv_index: Optional[int] = None


class TokenInfo(BaseModel):
    token_id: str
    remaining_time_seconds: int
    expires_at: str


class WeatherResponse(BaseModel):
    success: bool
    data: WeatherData
    token_info: TokenInfo
    timestamp: str


class TokenDetails(BaseModel):
    asset_id: str
    asset_name: str
    symbol: str
    balance: int
    expires_at: Optional[str] = None
    remaining_time_seconds: Optional[int] = None
    status: str
    purchase_time: Optional[str] = None
    total_uses: int = 0
    max_uses: int = 1


class TokensResponse(BaseModel):
    success: bool
    wallet_address: str
    tokens: List[TokenDetails]
    summary: Dict[str, int]


class ErrorResponse(BaseModel):
    success: bool = False
    error: Dict


class HealthResponse(BaseModel):
    status: str
    version: str
    services: Dict
    contract_info: Dict
    timestamp: str


# Dependency functions
async def get_algod_client() -> algod.AlgodClient:
    """Get Algorand client dependency."""
    return algod_client


async def get_indexer_client() -> indexer.IndexerClient:
    """Get Algorand indexer client dependency."""
    return indexer_client


# Utility functions
def validate_wallet_address(wallet: str) -> bool:
    """Validate Algorand wallet address format."""
    try:
        encoding.encode_address(encoding.decode_address(wallet))
        return True
    except Exception:
        return False


async def check_token_ownership(wallet: str) -> bool:
    """
    Check if a wallet owns a valid weather access token.
    For MVP demo, we'll simulate token ownership based on wallet balance.
    
    Args:
        wallet: Algorand wallet address
        
    Returns:
        True if wallet owns valid token
    """
    try:
        # For demo purposes: if wallet has > 5 ALGO, consider it has a token
        # In production, this would check actual ASA ownership
        account_info = algod_client.account_info(wallet)
        balance_algos = account_info["amount"] / 1_000_000
        
        # Demo logic: if balance < 5 ALGO, they need to "buy" a token
        # if balance >= 5 ALGO, they "have" a token
        has_token = balance_algos >= 5.0
        
        logger.info(f"Wallet {wallet[:8]}... balance: {balance_algos:.2f} ALGO, has_token: {has_token}")
        return has_token
    
    except Exception as e:
        logger.error(f"Error checking token ownership: {e}")
        return False


async def get_weather_from_open_meteo(city: str) -> Dict:
    """
    Fetch weather data from Open-Meteo API (free, no API key required).
    
    Args:
        city: City name
        
    Returns:
        Weather data dictionary
    """
    try:
        # First get coordinates for the city
        geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
        geocode_params = {"name": city, "count": 1, "language": "en", "format": "json"}
        
        geocode_response = requests.get(geocode_url, params=geocode_params, timeout=10)
        geocode_response.raise_for_status()
        geocode_data = geocode_response.json()
        
        if not geocode_data.get("results"):
            raise HTTPException(status_code=404, detail=f"City '{city}' not found")
        
        location = geocode_data["results"][0]
        lat, lon = location["latitude"], location["longitude"]
        
        # Get weather data
        weather_url = f"{OPEN_METEO_BASE_URL}/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,wind_direction_10m,surface_pressure",
            "timezone": "auto"
        }
        
        weather_response = requests.get(weather_url, params=weather_params, timeout=10)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        
        # Transform to standard format
        current = weather_data["current"]
        return {
            "name": location["name"],
            "sys": {"country": location.get("country_code", "")},
            "main": {
                "temp": current["temperature_2m"],
                "feels_like": current["temperature_2m"],  # Simplified
                "humidity": current["relative_humidity_2m"],
                "pressure": current.get("surface_pressure", 1013)
            },
            "weather": [{
                "description": _weather_code_to_description(current["weather_code"])
            }],
            "wind": {
                "speed": current["wind_speed_10m"],
                "deg": current["wind_direction_10m"]
            },
            "visibility": 10000  # Default value
        }
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Open-Meteo API error: {e}")
        raise HTTPException(status_code=502, detail="Weather service unavailable")


async def get_weather_from_openweather(city: str) -> Dict:
    """
    Fetch weather data from OpenWeather API.
    
    Args:
        city: City name
        
    Returns:
        Weather data dictionary
    """
    if not OPENWEATHER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenWeather API key not configured")
    
    try:
        # Current weather endpoint
        url = f"{OPENWEATHER_BASE_URL}/weather"
        params = {
            "q": city,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"OpenWeather API error: {e}")
        raise HTTPException(status_code=502, detail="Weather service unavailable")


async def get_weather_from_weatherapi(city: str) -> Dict:
    """
    Fetch weather data from WeatherAPI.com.
    
    Args:
        city: City name
        
    Returns:
        Weather data dictionary
    """
    if not WEATHERAPI_KEY:
        raise HTTPException(status_code=500, detail="WeatherAPI key not configured")
    
    try:
        url = f"{WEATHERAPI_BASE_URL}/current.json"
        params = {
            "key": WEATHERAPI_KEY,
            "q": city,
            "aqi": "no"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Transform to standard format
        location = data["location"]
        current = data["current"]
        
        return {
            "name": location["name"],
            "sys": {"country": location["country"]},
            "main": {
                "temp": current["temp_c"],
                "feels_like": current["feelslike_c"],
                "humidity": current["humidity"],
                "pressure": current["pressure_mb"]
            },
            "weather": [{
                "description": current["condition"]["text"].lower()
            }],
            "wind": {
                "speed": current["wind_kph"] / 3.6,  # Convert to m/s
                "deg": current["wind_degree"]
            },
            "visibility": current["vis_km"] * 1000  # Convert to meters
        }
    
    except requests.exceptions.RequestException as e:
        logger.error(f"WeatherAPI error: {e}")
        raise HTTPException(status_code=502, detail="Weather service unavailable")


def _weather_code_to_description(code: int) -> str:
    """Convert Open-Meteo weather code to description."""
    codes = {
        0: "clear sky",
        1: "mainly clear",
        2: "partly cloudy",
        3: "overcast",
        45: "fog",
        48: "depositing rime fog",
        51: "light drizzle",
        53: "moderate drizzle", 
        55: "dense drizzle",
        61: "slight rain",
        63: "moderate rain",
        65: "heavy rain",
        71: "slight snow",
        73: "moderate snow",
        75: "heavy snow",
        95: "thunderstorm",
    }
    return codes.get(code, "unknown")


async def get_weather_data(city: str) -> Dict:
    """
    Get weather data using the configured provider.
    
    Args:
        city: City name
        
    Returns:
        Weather data dictionary
    """
    if WEATHER_API_PROVIDER == "open-meteo":
        return await get_weather_from_open_meteo(city)
    elif WEATHER_API_PROVIDER == "openweather":
        return await get_weather_from_openweather(city)
    elif WEATHER_API_PROVIDER == "weatherapi":
        return await get_weather_from_weatherapi(city)
    else:
        logger.warning(f"Unknown weather provider: {WEATHER_API_PROVIDER}, falling back to Open-Meteo")
        return await get_weather_from_open_meteo(city)


def format_weather_data(raw_data: Dict, city: str) -> WeatherData:
    """
    Format OpenWeather API response into our standard format.
    
    Args:
        raw_data: Raw OpenWeather API response
        city: City name
        
    Returns:
        Formatted weather data
    """
    main = raw_data.get("main", {})
    weather = raw_data.get("weather", [{}])[0]
    wind = raw_data.get("wind", {})
    sys = raw_data.get("sys", {})
    
    return WeatherData(
        city=raw_data.get("name", city),
        country=sys.get("country", ""),
        temperature=main.get("temp", 0.0),
        feels_like=main.get("feels_like", 0.0),
        humidity=main.get("humidity", 0),
        pressure=main.get("pressure", 0),
        description=weather.get("description", ""),
        wind_speed=wind.get("speed", 0.0),
        wind_direction=wind.get("deg", 0),
        visibility=raw_data.get("visibility", 0),
        uv_index=None  # Would need separate UV API call
    )


# API Routes
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with basic info."""
    return {
        "service": "Tokenized Weather API",
        "version": "1.0.0",
        "description": "AI Agent Weather API with Blockchain Token Gating",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check(
    algod: algod.AlgodClient = Depends(get_algod_client),
    indexer: indexer.IndexerClient = Depends(get_indexer_client)
):
    """Health check endpoint."""
    
    # Check Algorand node status
    algorand_status = "connected"
    last_round = 0
    try:
        status = algod.status()
        last_round = status["last-round"]
    except Exception:
        algorand_status = "disconnected"
    
    # Check weather API status
    weather_api_status = "available"
    if WEATHER_API_PROVIDER == "openweather" and not OPENWEATHER_API_KEY:
        weather_api_status = "not_configured"
    elif WEATHER_API_PROVIDER == "weatherapi" and not WEATHERAPI_KEY:
        weather_api_status = "not_configured"
    
    rate_limit = 10000 if WEATHER_API_PROVIDER == "open-meteo" else 1000
    
    # Check indexer status
    indexer_status = "connected"
    try:
        indexer.health()
    except Exception:
        indexer_status = "disconnected"
    
    return HealthResponse(
        status="healthy" if algorand_status == "connected" else "degraded",
        version="1.0.0",
        services={
            "algorand_node": {
                "status": algorand_status,
                "network": "localnet",
                "last_round": last_round
            },
"weather_api": {
                "status": weather_api_status,
                "rate_limit_remaining": rate_limit,
                "provider": WEATHER_API_PROVIDER
            },
            "indexer": {
                "status": indexer_status,
                "pending_transactions": 0
            }
        },
        contract_info={
            "marketplace_app_id": str(MARKETPLACE_APP_ID),
            "weather_token_asa_id": str(WEATHER_ASA_ID)
        },
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


@app.get("/weather", response_model=WeatherResponse)
async def get_weather(
    city: str = Query(..., description="City name"),
    wallet: str = Query(..., description="Algorand wallet address")
):
    """
    Get weather data for a city, gated by token ownership.
    
    Args:
        city: City name to get weather for
        wallet: Algorand wallet address that must own access token
        
    Returns:
        Weather data if token is valid
        
    Raises:
        403: If no valid token found
        400: If invalid parameters
    """
    
    # Validate wallet address
    if not validate_wallet_address(wallet):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_WALLET",
                    "message": "Invalid wallet address format"
                }
            }
        )
    
    # Check token ownership
    has_valid_token = await check_token_ownership(wallet)
    
    if not has_valid_token:
        raise HTTPException(
            status_code=403,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_TOKEN",
                    "message": "No valid weather access token found for this wallet",
                    "details": {
                        "wallet_address": wallet,
                        "required_token_type": "OpenWeather Access Token",
                        "marketplace_info": {
                            "contract_id": str(MARKETPLACE_APP_ID),
                            "token_price_algo": 10,
                            "purchase_endpoint": "/marketplace/buy"
                        }
                    }
                }
            }
        )
    
    # Fetch weather data
    try:
        raw_weather = await get_weather_data(city)
        weather_data = format_weather_data(raw_weather, city)
        
        # Create response
        return WeatherResponse(
            success=True,
            data=weather_data,
            token_info=TokenInfo(
                token_id=str(WEATHER_ASA_ID),
                remaining_time_seconds=3600,  # Simplified: 1 hour remaining
                expires_at=(datetime.utcnow().replace(microsecond=0).isoformat() + "Z")
            ),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_weather: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/tokens/{wallet_address}", response_model=TokensResponse)
async def get_wallet_tokens(wallet_address: str):
    """
    Get information about tokens owned by a wallet.
    
    Args:
        wallet_address: Algorand wallet address
        
    Returns:
        List of tokens owned by the wallet
    """
    
    # Validate wallet address
    if not validate_wallet_address(wallet_address):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_WALLET",
                    "message": "Invalid wallet address format"
                }
            }
        )
    
    try:
        # Get account info
        account_info = algod_client.account_info(wallet_address)
        assets = account_info.get("assets", [])
        
        tokens = []
        valid_tokens = 0
        
        for asset in assets:
            if asset["asset-id"] == WEATHER_ASA_ID and asset["amount"] > 0:
                tokens.append(TokenDetails(
                    asset_id=str(asset["asset-id"]),
                    asset_name="OpenWeather Access Token",
                    symbol="OWAT",
                    balance=asset["amount"],
                    expires_at=(datetime.utcnow().replace(microsecond=0).isoformat() + "Z"),
                    remaining_time_seconds=3600,  # Simplified
                    status="valid",
                    purchase_time=None,  # Would need transaction history
                    total_uses=0,
                    max_uses=1
                ))
                valid_tokens += 1
        
        return TokensResponse(
            success=True,
            wallet_address=wallet_address,
            tokens=tokens,
            summary={
                "total_tokens": len(tokens),
                "valid_tokens": valid_tokens,
                "expired_tokens": 0
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting wallet tokens: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving token information")


# Error handlers
from fastapi.responses import JSONResponse

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with proper error format."""
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    else:
        return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})


if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )