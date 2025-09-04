#!/usr/bin/env python3
"""
Fund demo wallet with test ALGOs from LocalNet dispenser.
"""

import os
import sys
from pathlib import Path
from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk import transaction
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fund_wallet(agent_address: str, amount_algos: int = 10) -> bool:
    """
    Fund a wallet with test ALGOs from LocalNet dispenser.
    
    Args:
        agent_address: Wallet address to fund
        amount_algos: Amount in ALGOs to send
        
    Returns:
        True if successful
    """
    try:
        # Connect to LocalNet
        algod_client = algod.AlgodClient("a" * 64, "http://localhost:4001")
        
        # Use LocalNet dispenser account (well-known funded account)
        dispenser_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon art"
        dispenser_private_key = mnemonic.to_private_key(dispenser_mnemonic)
        dispenser_address = account.address_from_private_key(dispenser_private_key)
        
        logger.info(f"Funding {agent_address} with {amount_algos} ALGO from dispenser")
        
        # Get suggested parameters
        params = algod_client.suggested_params()
        
        # Create payment transaction
        payment_txn = transaction.PaymentTxn(
            sender=dispenser_address,
            sp=params,
            receiver=agent_address,
            amt=amount_algos * 1_000_000,  # Convert to microAlgos
            note=b"Demo wallet funding"
        )
        
        # Sign transaction
        signed_txn = payment_txn.sign(dispenser_private_key)
        
        # Send transaction
        txid = algod_client.send_transaction(signed_txn)
        
        # Wait for confirmation
        confirmed_txn = transaction.wait_for_confirmation(algod_client, txid, 4)
        
        if confirmed_txn["confirmed-round"] > 0:
            logger.info(f"✅ Successfully funded wallet! TxID: {txid}")
            
            # Check new balance
            account_info = algod_client.account_info(agent_address)
            new_balance = account_info["amount"] / 1_000_000
            logger.info(f"💰 New wallet balance: {new_balance:.6f} ALGO")
            
            return True
        else:
            logger.error("Transaction not confirmed")
            return False
            
    except Exception as e:
        logger.error(f"Error funding wallet: {e}")
        return False


def main():
    """Main function to fund demo wallet."""
    if len(sys.argv) < 2:
        print("Usage: python fund_demo_wallet.py <wallet_address> [amount_algos]")
        print("Example: python fund_demo_wallet.py ABCD1234... 10")
        sys.exit(1)
    
    wallet_address = sys.argv[1]
    amount = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    logger.info(f"🚀 Funding demo wallet with {amount} ALGO")
    
    success = fund_wallet(wallet_address, amount)
    
    if success:
        logger.info("🎉 Demo wallet funding complete!")
    else:
        logger.error("❌ Demo wallet funding failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()