# pyright: reportMissingModuleSource=false
from algopy import ARC4Contract, String, UInt64
from algopy.arc4 import abimethod, UInt64 as ARC4UInt64, Bool


class WeatherMarketplace(ARC4Contract):
    """
    Simplified smart contract for tokenized weather API access demo.
    
    This contract manages basic state for weather access tokens.
    For the MVP demo, we'll use a simplified approach.
    """
    
    def __init__(self) -> None:
        # Token price in microAlgos (10 ALGO = 10,000,000 microAlgos)
        self.token_price = UInt64(10_000_000)
        
        # Weather access token ASA ID (set after ASA creation outside contract)
        self.weather_asa_id = UInt64(0)
        
        # Token validity duration in seconds (1 hour = 3600 seconds)
        self.token_duration = UInt64(3600)
        
        # Total tokens sold counter
        self.total_tokens_sold = UInt64(0)
        
        # Contract is active flag
        self.is_active = Bool(True)

    @abimethod()
    def get_token_price(self) -> ARC4UInt64:
        """
        Get the current token price.
        
        Returns:
            Token price in microAlgos
        """
        return ARC4UInt64(self.token_price)

    @abimethod()
    def get_weather_asa_id(self) -> ARC4UInt64:
        """
        Get the weather ASA ID.
        
        Returns:
            The weather token ASA ID
        """
        return ARC4UInt64(self.weather_asa_id)

    @abimethod()
    def set_weather_asa_id(self, asa_id: ARC4UInt64) -> None:
        """
        Set the weather ASA ID (admin only for demo).
        
        Args:
            asa_id: The ASA ID to set
        """
        self.weather_asa_id = asa_id.native

    @abimethod()
    def get_token_duration(self) -> ARC4UInt64:
        """
        Get the token validity duration.
        
        Returns:
            Duration in seconds
        """
        return ARC4UInt64(self.token_duration)

    @abimethod()
    def record_token_sale(self) -> ARC4UInt64:
        """
        Record a token sale (simplified for demo).
        
        Returns:
            Updated total sales count
        """
        self.total_tokens_sold += 1
        return ARC4UInt64(self.total_tokens_sold)

    @abimethod()
    def get_total_sales(self) -> ARC4UInt64:
        """
        Get total token sales count.
        
        Returns:
            Total number of tokens sold
        """
        return ARC4UInt64(self.total_tokens_sold)

    @abimethod()
    def is_contract_active(self) -> Bool:
        """
        Check if the contract is active.
        
        Returns:
            True if contract is active
        """
        return self.is_active

    @abimethod()
    def get_contract_info(self) -> String:
        """
        Get basic contract information as JSON string.
        
        Returns:
            JSON string with contract info
        """
        return String("WeatherMarketplace v1.0 - Tokenized Weather API Access")