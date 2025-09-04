"""
AI Agent Simulation Script for Tokenized Weather API Access

This script simulates an AI agent that:
1. Attempts to access weather data
2. Automatically purchases tokens when access is denied
3. Retries requests with valid tokens
4. Optionally resells unused tokens
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, Optional, Tuple

import requests
from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class WeatherAgent:
    """AI Agent that autonomously purchases and uses weather API access tokens."""
    
    def __init__(
        self,
        agent_mnemonic: Optional[str] = None,
        backend_url: str = "http://localhost:8000",
        algod_server: str = "http://localhost:4001",
        algod_token: str = "a" * 64,
        marketplace_app_id: int = 0,
        weather_asa_id: int = 0,
    ):
        """
        Initialize the Weather Agent.
        
        Args:
            agent_mnemonic: Wallet mnemonic (generates new if None)
            backend_url: MCP backend server URL
            algod_server: Algorand node URL
            algod_token: Algorand node token
            marketplace_app_id: Smart contract app ID
            weather_asa_id: Weather token ASA ID
        """
        
        # Initialize wallet
        if agent_mnemonic:
            self.mnemonic = agent_mnemonic
            self.private_key = mnemonic.to_private_key(agent_mnemonic)
        else:
            self.private_key, self.mnemonic = account.generate_account()
        
        self.address = account.address_from_private_key(self.private_key)
        
        if not agent_mnemonic:
            logger.info(f"Generated new wallet: {self.address}")
            logger.info(f"Mnemonic: {self.mnemonic}")
        
        # Initialize clients
        self.backend_url = backend_url
        self.algod_client = algod.AlgodClient(algod_token, algod_server)
        
        # Contract information
        self.marketplace_app_id = marketplace_app_id
        self.weather_asa_id = weather_asa_id
        
        # Agent state
        self.balance_algos = 0
        self.owned_tokens = []
        self.request_count = 0
        self.successful_requests = 0
        self.tokens_purchased = 0
        
        # Load initial state
        self._update_account_info()
    
    def get_address(self) -> str:
        """Get the agent's wallet address."""
        return self.address
    
    def _update_account_info(self) -> None:
        """Update account balance and token information."""
        try:
            account_info = self.algod_client.account_info(self.address)
            self.balance_algos = account_info["amount"] / 1_000_000  # Convert microAlgos to Algos
            
            # Update owned tokens
            assets = account_info.get("assets", [])
            self.owned_tokens = [
                asset for asset in assets
                if asset["asset-id"] == self.weather_asa_id and asset["amount"] > 0
            ]
            
            logger.info(f"Account balance: {self.balance_algos:.2f} ALGO")
            logger.info(f"Weather tokens owned: {len(self.owned_tokens)}")
            
        except Exception as e:
            logger.error(f"Error updating account info: {e}")
    
    def has_valid_token(self) -> bool:
        """Check if the agent owns a valid weather access token."""
        return len(self.owned_tokens) > 0
    
    def get_weather(self, city: str) -> Optional[Dict]:
        """
        Attempt to get weather data for a city.
        
        Args:
            city: City name to get weather for
            
        Returns:
            Weather data if successful, None if failed
        """
        self.request_count += 1
        
        try:
            response = requests.get(
                f"{self.backend_url}/weather",
                params={"city": city, "wallet": self.address},
                timeout=30
            )
            
            if response.status_code == 200:
                self.successful_requests += 1
                data = response.json()
                logger.info(f"Weather data retrieved for {city}: {data['data']['temperature']}°C")
                return data
            
            elif response.status_code == 403:
                # Token required - this is expected behavior
                error_data = response.json()
                logger.info(f"Access denied: {error_data.get('error', {}).get('message', 'Unknown error')}")
                return None
            
            else:
                logger.error(f"Unexpected response: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting weather data: {e}")
            return None
    
    def purchase_weather_token(self) -> bool:
        """
        Simulate purchasing a weather access token by sending ALGO to a demo address.
        For MVP demo: Send some ALGO to demonstrate "token purchase"
        
        Returns:
            True if purchase successful, False otherwise
        """
        
        if self.balance_algos < 1.1:  # Need 1 ALGO + fees for demo
            logger.error(f"Insufficient balance: {self.balance_algos:.2f} ALGO (need 1.1 ALGO)")
            return False
        
        try:
            # Get suggested parameters
            params = self.algod_client.suggested_params()
            
            # For demo: send 1 ALGO to a demo "marketplace" address (can be any address)
            # This simulates purchasing a token and reduces balance below 5 ALGO threshold
            demo_marketplace_address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"  # Example address
            
            # Create payment transaction to simulate token purchase
            payment_txn = transaction.PaymentTxn(
                sender=self.address,
                sp=params,
                receiver=demo_marketplace_address,
                amt=1_000_000,  # 1 ALGO in microAlgos (demo amount)
                note=b"Demo weather token purchase"
            )
            
            # Sign transaction
            signed_txn = payment_txn.sign(self.private_key)
            
            # Submit transaction
            txid = self.algod_client.send_transaction(signed_txn)
            
            # Wait for confirmation
            confirmed_txn = transaction.wait_for_confirmation(self.algod_client, txid, 4)
            
            if confirmed_txn["confirmed-round"] > 0:
                self.tokens_purchased += 1
                logger.info(f"✅ Successfully simulated weather token purchase! TxID: {txid}")
                logger.info("💡 Demo: Reduced balance to simulate token purchase")
                
                # Update account info
                time.sleep(1)  # Wait for transaction to be processed
                self._update_account_info()
                return True
            else:
                logger.error("Transaction not confirmed")
                return False
                
        except Exception as e:
            logger.error(f"Error purchasing token: {e}")
            return False
    
    def _get_app_address(self, app_id: int) -> str:
        """Get the address of a smart contract application."""
        return account.encode_address(account.decode_address("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"))
    
    def fund_wallet_for_demo(self) -> bool:
        """
        Request funding from LocalNet dispenser for demo purposes.
        """
        try:
            # For LocalNet demo, we can fund the wallet using dispenser
            logger.info("🪙 Requesting demo funding from LocalNet dispenser...")
            
            # This is a simplified version - in reality you'd call the dispenser
            # For now, we'll just log this action
            logger.info(f"💰 Demo wallet {self.address[:8]}... would be funded with test ALGOs")
            return True
            
        except Exception as e:
            logger.error(f"Error funding wallet: {e}")
            return False
    
    def autonomous_weather_request(self, city: str, max_attempts: int = 3) -> Optional[Dict]:
        """
        Autonomously request weather data, purchasing tokens as needed.
        
        Args:
            city: City name
            max_attempts: Maximum purchase attempts
            
        Returns:
            Weather data if successful
        """
        logger.info(f"Autonomous weather request for {city}")
        
        # Update account state
        self._update_account_info()
        
        # Try to get weather data
        weather_data = self.get_weather(city)
        
        if weather_data:
            return weather_data
        
        # No valid token - attempt to purchase one
        logger.info("No valid token found, attempting to purchase...")
        
        for attempt in range(max_attempts):
            logger.info(f"Purchase attempt {attempt + 1}/{max_attempts}")
            
            # Purchase token (demo version)
            if self.purchase_weather_token():
                logger.info("Token purchased successfully, retrying weather request...")
                
                # Wait a moment for the transaction to be processed
                time.sleep(2)
                
                # Retry weather request
                weather_data = self.get_weather(city)
                if weather_data:
                    return weather_data
                else:
                    logger.warning("Weather request failed despite having token")
            else:
                logger.warning(f"Failed to purchase token (attempt {attempt + 1})")
                
            # Wait before next attempt
            if attempt < max_attempts - 1:
                time.sleep(5)
        
        logger.error(f"Failed to get weather data for {city} after {max_attempts} attempts")
        return None
    
    def print_stats(self) -> None:
        """Print agent statistics."""
        print("\n" + "="*50)
        print("WEATHER AGENT STATISTICS")
        print("="*50)
        print(f"Wallet Address: {self.address}")
        print(f"Balance: {self.balance_algos:.6f} ALGO")
        print(f"Weather Tokens Owned: {len(self.owned_tokens)}")
        print(f"Total Requests: {self.request_count}")
        print(f"Successful Requests: {self.successful_requests}")
        print(f"Tokens Purchased: {self.tokens_purchased}")
        print(f"Success Rate: {(self.successful_requests/self.request_count*100):.1f}%" if self.request_count > 0 else "N/A")
        print("="*50)
    
    def run_demo(self, cities: list = None) -> None:
        """
        Run a demonstration of the agent's capabilities.
        
        Args:
            cities: List of cities to get weather for
        """
        if cities is None:
            cities = ["Berlin", "New York", "Tokyo", "London", "Sydney"]
        
        logger.info("Starting Weather Agent Demo")
        logger.info(f"Testing cities: {cities}")
        
        for i, city in enumerate(cities, 1):
            logger.info(f"\n--- Request {i}/{len(cities)}: {city} ---")
            
            result = self.autonomous_weather_request(city)
            
            if result:
                temp = result['data']['temperature']
                desc = result['data']['description']
                logger.info(f"✅ {city}: {temp}°C, {desc}")
            else:
                logger.error(f"❌ Failed to get weather for {city}")
            
            # Wait between requests
            if i < len(cities):
                time.sleep(3)
        
        # Print final statistics
        self.print_stats()


def main():
    """Main function to run the agent demo."""
    
    # Load configuration from environment
    agent_mnemonic = os.getenv("AGENT_WALLET_MNEMONIC")
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    algod_server = os.getenv("ALGOD_SERVER", "http://localhost:4001")
    algod_token = os.getenv("ALGOD_TOKEN", "a" * 64)
    marketplace_app_id = int(os.getenv("MARKETPLACE_APP_ID", "0"))
    weather_asa_id = int(os.getenv("WEATHER_ASA_ID", "0"))
    
    # Create and run agent
    agent = WeatherAgent(
        agent_mnemonic=agent_mnemonic,
        backend_url=backend_url,
        algod_server=algod_server,
        algod_token=algod_token,
        marketplace_app_id=marketplace_app_id,
        weather_asa_id=weather_asa_id,
    )
    
    # Run demo
    agent.run_demo()


if __name__ == "__main__":
    main()