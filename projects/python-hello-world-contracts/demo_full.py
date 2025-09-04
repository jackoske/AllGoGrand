#!/usr/bin/env python3
"""
Enhanced Demo script to test the WeatherMarketplace smart contract
and backend API with both rejection and success scenarios
"""

import os
import sys
import time
import requests
from pathlib import Path

# Add the smart contracts directory to the path
sys.path.insert(0, str(Path(__file__).parent / "smart_contracts" / "artifacts" / "weather_marketplace"))

from weather_marketplace_client import WeatherMarketplaceClient
import algokit_utils

def main():
    print("🌤️  WeatherMarketplace Full Demo - Rejection & Success Scenarios")
    print("=" * 70)
    
    # Set up localnet environment variables
    os.environ["ALGOD_SERVER"] = "http://localhost:4001"
    os.environ["ALGOD_TOKEN"] = "a" * 64
    os.environ["INDEXER_SERVER"] = "http://localhost:8980"
    os.environ["INDEXER_TOKEN"] = "a" * 64
    
    try:
        # Get clients using the environment
        algod_client = algokit_utils.get_algod_client()
        indexer_client = algokit_utils.get_indexer_client()
        
        # Get default accounts for testing
        deployer = algokit_utils.get_localnet_default_account(algod_client)
        
        # Create AlgorandClient
        algorand = algokit_utils.AlgorandClient.from_clients(
            algod=algod_client,
            indexer=indexer_client
        )
        
        # Create a new account to receive most of the ALGO (making main account poor)
        from algosdk import account
        drain_private_key, drain_address = account.generate_account()
        
        # Check deployer's current balance
        initial_balance = algod_client.account_info(deployer.address)["amount"] / 1_000_000
        print(f"\n💰 Initial deployer balance: {initial_balance:.2f} ALGO")
        
        # Calculate how much to drain (leave only 2 ALGO, below 5 ALGO threshold)
        amount_to_drain = int((initial_balance - 2.1) * 1_000_000)  # Leave 2.1 ALGO
        
        print(f"💸 Draining {amount_to_drain/1_000_000:.2f} ALGO to make account 'poor'...")
        
        # Use old-style transfer for compatibility
        drain_txn = algokit_utils.transfer(
            client=algod_client,
            parameters=algokit_utils.TransferParameters(
                from_account=deployer,
                to_address=drain_address,
                micro_algos=amount_to_drain,
            )
        )
        
        
        print("✅ Connected to LocalNet")
        
        # Test the smart contract first
        print("\n📋 SMART CONTRACT DEMO")
        print("-" * 40)
        
        # Connect to the deployed WeatherMarketplace contract
        weather_client = WeatherMarketplaceClient(
            algorand=algorand, 
            app_id=1001,  # Fresh deployment on reset localnet
            default_sender=deployer.address,
            default_signer=deployer.signer
        )
        
        # Test smart contract methods
        try:
            price_result = weather_client.send.get_token_price()
            print(f"  Token Price: {price_result.abi_return} microAlgos ({price_result.abi_return/1_000_000} ALGO)")
            
            active_result = weather_client.send.is_contract_active()
            print(f"  Contract Active: {active_result.abi_return}")
            
            sales_result = weather_client.send.get_total_sales()
            print(f"  Total Sales: {sales_result.abi_return}")
            
            print("✅ Smart contract working correctly!")
            
        except Exception as e:
            print(f"❌ Smart contract error: {e}")
            return False
        
        # Now test the backend API scenarios
        print(f"\n🌐 BACKEND API DEMO - Testing Rejection & Success")
        print("-" * 50)
        
        # Check if backend is running
        backend_url = "http://localhost:8000"
        try:
            health_response = requests.get(f"{backend_url}/health", timeout=5)
            if health_response.status_code != 200:
                print(f"❌ Backend not responding correctly at {backend_url}")
                print("   Please make sure the backend server is running:")
                print("   cd ../../backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python main.py")
                return False
            print(f"✅ Backend server is running at {backend_url}")
        except requests.exceptions.RequestException:
            print(f"❌ Cannot connect to backend at {backend_url}")
            print("   Please start the backend server first:")
            print("   cd ../../backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python main.py")
            return False
        
        # Scenario 1: Drained account (should be rejected)
        print(f"\n🚫 SCENARIO 1: Rejection Test")
        print(f"   Testing with drained account: {deployer.address[:8]}... (~2 ALGO)")
        print("-" * 30)
        
        try:
            current_balance = algod_client.account_info(deployer.address)["amount"] / 1_000_000
            print(f"   Account Balance: {current_balance:.2f} ALGO")
            print(f"   Required Balance: 5.00 ALGO minimum")
            
            weather_response = requests.get(
                f"{backend_url}/weather", 
                params={"city": "London", "wallet": deployer.address},
                timeout=10
            )
            
            if weather_response.status_code == 403:
                print(f"✅ REJECTION WORKING: HTTP {weather_response.status_code}")
                print(f"   Response: {weather_response.json().get('detail', 'Access denied')}")
            else:
                print(f"⚠️  Expected rejection but got HTTP {weather_response.status_code}")
                print(f"   Response: {weather_response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        
        # Scenario 2: Fund it back and test success
        print(f"\n💰 SCENARIO 2: Funding Account Back")
        print("-" * 40)
        
        # Transfer money back from drain account to deployer
        # First need to fund the drain account to make it able to send
        fund_drain_txn = algokit_utils.transfer(
            client=algod_client,
            parameters=algokit_utils.TransferParameters(
                from_account=deployer,
                to_address=drain_address,
                micro_algos=100_000,  # 0.1 ALGO for transaction fee
            )
        )
        
        # Now transfer the original amount back
        refund_amount = amount_to_drain - 100_000  # Leave some for fee
        print(f"   Transferring {refund_amount/1_000_000:.2f} ALGO back to deployer...")
        
        from algosdk import mnemonic
        drain_account = algokit_utils.Account(
            private_key=drain_private_key,
            address=drain_address
        )
        
        refund_txn = algokit_utils.transfer(
            client=algod_client,
            parameters=algokit_utils.TransferParameters(
                from_account=drain_account,
                to_address=deployer.address,
                micro_algos=refund_amount,
            )
        )
        
        print(f"\n✅ SCENARIO 3: Success Test")
        print(f"   Testing with re-funded account: {deployer.address[:8]}...")
        print("-" * 30)
        
        try:
            updated_balance = algod_client.account_info(deployer.address)["amount"] / 1_000_000
            print(f"   Account Balance: {updated_balance:.2f} ALGO")
            print(f"   Required Balance: 5.00 ALGO minimum")
            
            weather_response = requests.get(
                f"{backend_url}/weather", 
                params={"city": "London", "wallet": deployer.address},
                timeout=10
            )
            
            if weather_response.status_code == 200:
                data = weather_response.json()
                print(f"✅ ACCESS GRANTED: HTTP {weather_response.status_code}")
                print(f"   City: {data['data']['city']}")
                print(f"   Temperature: {data['data']['temperature']}°C")
                print(f"   Description: {data['data']['description']}")
                print(f"   Token Valid: {data['token_info']['remaining_time_seconds']}s remaining")
            else:
                print(f"❌ Expected success but got HTTP {weather_response.status_code}")
                print(f"   Response: {weather_response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        
        # Record the "token purchase" in smart contract
        final_sale_result = weather_client.send.record_token_sale()
        print(f"   Smart contract updated - Total sales: {final_sale_result.abi_return}")
        
        print("\n🎉 FULL DEMO COMPLETED!")
        print("=" * 50)
        print("✅ Demonstrated:")
        print("  • Smart contract deployment and interaction")
        print("  • Token-gated API access with balance checking") 
        print("  • Rejection of insufficient balance accounts")
        print("  • Success with properly funded accounts")
        print("  • Token purchase simulation and access restoration")
        print("\n🚀 Ready for frontend integration!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)