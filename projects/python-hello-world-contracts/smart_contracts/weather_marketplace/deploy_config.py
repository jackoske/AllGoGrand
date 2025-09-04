"""Simplified deployment configuration for Weather Marketplace smart contract."""

import logging
import sys
from pathlib import Path

# Add the artifacts directory to the path so we can import the generated client
artifacts_path = Path(__file__).parent.parent / "artifacts" / "weather_marketplace"
sys.path.insert(0, str(artifacts_path))

from weather_marketplace_client import WeatherMarketplaceFactory
import algokit_utils
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

logger = logging.getLogger(__name__)


def deploy(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    app_spec: algokit_utils.Arc56Contract,
    deployer: algokit_utils.Account,
    network: str = "localnet",
) -> None:
    """Deploy the Weather Marketplace smart contract.
    
    Args:
        algod_client: Algorand client
        indexer_client: Algorand indexer client  
        app_spec: Application specification (Arc56Contract)
        deployer: Deployer account
        network: Target network (localnet, testnet, mainnet)
    """
    
    logger.info(f"Deploying simplified Weather Marketplace to {network}")
    
    # Create AlgorandClient from the clients
    algorand_client = algokit_utils.AlgorandClient.from_clients(
        algod=algod_client,
        indexer=indexer_client,
    )
    
    # Use the generated factory for deployment
    app_factory = WeatherMarketplaceFactory(
        algorand_client,
        app_name="WeatherMarketplace",
        default_sender=deployer.address,
        default_signer=deployer.signer,
    )
    
    # Deploy the application
    app_client, deploy_response = app_factory.send.create.bare()
    
    logger.info(f"Weather Marketplace deployed with App ID: {app_client.app_id}")
    
    # Fund the contract with minimum balance if needed
    if network == "localnet":
        min_balance = 100_000  # 0.1 ALGO for minimum balance
        logger.info(f"Skipping funding - contract will be funded on first interaction")
        # Note: Contract funding can be done separately if needed
    
    # Log deployment summary
    logger.info("Deployment Summary:")
    logger.info(f"  App ID: {app_client.app_id}")
    logger.info(f"  App Address: {app_client.app_address}")
    logger.info(f"  Network: {network}")
    logger.info(f"  Deployer: {deployer.address}")
    
    # Test basic contract functionality
    try:
        result = app_client.get_contract_info()
        logger.info(f"  Contract Info: {result.return_value}")
        
        price_result = app_client.get_token_price()
        logger.info(f"  Token Price: {price_result.return_value} microAlgos")
        
    except Exception as e:
        logger.warning(f"Could not test contract methods: {e}")


if __name__ == "__main__":
    # This allows the deploy script to be run directly
    import os
    from algokit_utils import get_algod_client, get_indexer_client, get_localnet_default_account
    
    # Get network from environment or default to localnet
    network = os.getenv("NETWORK", "localnet")
    
    # Set up clients
    algod_client = get_algod_client()
    indexer_client = get_indexer_client()
    
    # Get deployer account
    if network == "localnet":
        deployer = get_localnet_default_account(algod_client)
    else:
        # For other networks, you'd need to set up the deployer account
        raise NotImplementedError(f"Deployer setup for {network} not implemented")
    
    # For this simplified version, we'll create a basic app spec
    # In production, this would be generated from the contract
    app_spec = algokit_utils.ApplicationSpecification(
        hints={},
        bare_call_config={},
        create_call_config={},
        update_call_config={},
        delete_call_config={},
        schema={},
        state={},
        source={},
    )
    
    # Deploy
    deploy(algod_client, indexer_client, app_spec, deployer, network)