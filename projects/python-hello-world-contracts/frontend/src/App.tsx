import React, { useState, useEffect } from 'react';
import './App.css';
import { algosdk } from 'algosdk';
import axios from 'axios';

interface AlgorandAccount {
  address: string;
  privateKey: string;
}

interface AccountInfo {
  address: string;
  balance: number;
  hasAccess: boolean;
}

interface WeatherData {
  city: string;
  country: string;
  temperature: number;
  feels_like: number;
  humidity: number;
  description: string;
  wind_speed: number;
}

interface WeatherResponse {
  success: boolean;
  data: WeatherData;
  token_info: {
    remaining_time_seconds: number;
    expires_at: string;
  };
}

const ALGOD_SERVER = 'http://localhost:4001';
const ALGOD_TOKEN = 'a'.repeat(64);
const BACKEND_URL = 'http://localhost:8000';
const MINIMUM_BALANCE = 5; // 5 ALGO minimum for access

function App() {
  const [account, setAccount] = useState<AlgorandAccount | null>(null);
  const [accountInfo, setAccountInfo] = useState<AccountInfo | null>(null);
  const [weatherData, setWeatherData] = useState<WeatherResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [city, setCity] = useState('London');
  const [drainAccount, setDrainAccount] = useState<AlgorandAccount | null>(null);

  const algodClient = new algosdk.Algodv2(ALGOD_TOKEN, ALGOD_SERVER, '');

  const generateAccount = () => {
    const account = algosdk.generateAccount();
    const newAccount = {
      address: account.addr,
      privateKey: Buffer.from(account.sk).toString('base64')
    };
    setAccount(newAccount);
    setAccountInfo(null);
    setWeatherData(null);
    setError(null);
  };

  const loadLocalnetAccount = async () => {
    try {
      const kmd = new algosdk.Kmd('a'.repeat(64), 'http://localhost:4002', '');
      const wallets = await kmd.listWallets();
      const unencryptedWallet = wallets.wallets.find(w => w.name === 'unencrypted-default-wallet');
      
      if (unencryptedWallet) {
        const walletHandle = await kmd.initWalletHandle(unencryptedWallet.id, '');
        const addresses = await kmd.listKeys(walletHandle.wallet_handle_token);
        
        if (addresses.addresses.length > 0) {
          const address = addresses.addresses[0];
          const keyResponse = await kmd.exportKey(walletHandle.wallet_handle_token, '', address);
          
          const newAccount = {
            address: address,
            privateKey: Buffer.from(keyResponse.private_key).toString('base64')
          };
          setAccount(newAccount);
          setAccountInfo(null);
          setWeatherData(null);
          setError(null);
        }
      }
    } catch (err) {
      setError(`Failed to load LocalNet account: ${err}`);
    }
  };

  const refreshAccountInfo = async () => {
    if (!account) return;

    try {
      setLoading(true);
      const info = await algodClient.accountInformation(account.address).do();
      const balanceInAlgo = info.amount / 1_000_000;
      
      setAccountInfo({
        address: account.address,
        balance: balanceInAlgo,
        hasAccess: balanceInAlgo >= MINIMUM_BALANCE
      });
    } catch (err) {
      setError(`Failed to get account info: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const drainAccountFunds = async () => {
    if (!account || !accountInfo) return;

    try {
      setLoading(true);
      
      // Create drain account if it doesn't exist
      if (!drainAccount) {
        const newDrainAccount = algosdk.generateAccount();
        const drainAcct = {
          address: newDrainAccount.addr,
          privateKey: Buffer.from(newDrainAccount.sk).toString('base64')
        };
        setDrainAccount(drainAcct);
      }

      const currentDrainAccount = drainAccount || {
        address: algosdk.generateAccount().addr,
        privateKey: Buffer.from(algosdk.generateAccount().sk).toString('base64')
      };

      // Leave only 2 ALGO (below 5 ALGO threshold)
      const amountToDrain = Math.floor((accountInfo.balance - 2.1) * 1_000_000);
      
      if (amountToDrain > 0) {
        const params = await algodClient.getTransactionParams().do();
        
        const txn = algosdk.makePaymentTxnWithSuggestedParams(
          account.address,
          currentDrainAccount.address,
          amountToDrain,
          undefined,
          undefined,
          params
        );

        const privateKeyUint8 = new Uint8Array(Buffer.from(account.privateKey, 'base64'));
        const signedTxn = txn.signTxn(privateKeyUint8);
        
        await algodClient.sendRawTransaction(signedTxn).do();
        
        // Wait for confirmation
        await algosdk.waitForConfirmation(algodClient, txn.txID(), 4);
        
        await refreshAccountInfo();
        setError(null);
      }
    } catch (err) {
      setError(`Failed to drain account: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const fundAccount = async () => {
    if (!account || !drainAccount) return;

    try {
      setLoading(true);
      
      // Get drain account info to see how much we can transfer back
      const drainInfo = await algodClient.accountInformation(drainAccount.address).do();
      const drainBalance = drainInfo.amount / 1_000_000;
      
      if (drainBalance > 0.1) {
        const params = await algodClient.getTransactionParams().do();
        
        // Transfer most funds back (leave some for fees)
        const amountToReturn = Math.floor((drainBalance - 0.1) * 1_000_000);
        
        const txn = algosdk.makePaymentTxnWithSuggestedParams(
          drainAccount.address,
          account.address,
          amountToReturn,
          undefined,
          undefined,
          params
        );

        const privateKeyUint8 = new Uint8Array(Buffer.from(drainAccount.privateKey, 'base64'));
        const signedTxn = txn.signTxn(privateKeyUint8);
        
        await algodClient.sendRawTransaction(signedTxn).do();
        
        // Wait for confirmation
        await algosdk.waitForConfirmation(algodClient, txn.txID(), 4);
        
        await refreshAccountInfo();
        setError(null);
      } else {
        setError('Drain account has insufficient balance to return funds');
      }
    } catch (err) {
      setError(`Failed to fund account: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchWeatherData = async () => {
    if (!account || !accountInfo) return;

    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get<WeatherResponse>(`${BACKEND_URL}/weather`, {
        params: {
          city: city,
          wallet: account.address
        }
      });

      setWeatherData(response.data);
    } catch (err: any) {
      if (err.response?.status === 403) {
        setError(`Access denied: ${err.response.data.detail || 'Insufficient balance'}`);
      } else {
        setError(`Failed to fetch weather data: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (account) {
      refreshAccountInfo();
    }
  }, [account]);

  return (
    <div className="App">
      <header className="App-header">
        <h1>🌤️ Weather Marketplace Demo</h1>
        <p>Token-gated weather data access on Algorand</p>
      </header>

      <main className="App-main">
        {/* Account Management Section */}
        <section className="account-section">
          <h2>Account Management</h2>
          
          {!account ? (
            <div className="account-controls">
              <button onClick={generateAccount} className="primary-button">
                Generate New Account
              </button>
              <button onClick={loadLocalnetAccount} className="secondary-button">
                Load LocalNet Account
              </button>
            </div>
          ) : (
            <div className="account-info">
              <div className="address-display">
                <strong>Address:</strong>
                <code>{account.address.slice(0, 8)}...{account.address.slice(-8)}</code>
              </div>
              
              {accountInfo && (
                <div className="balance-info">
                  <div className={`balance ${accountInfo.hasAccess ? 'sufficient' : 'insufficient'}`}>
                    <strong>Balance:</strong> {accountInfo.balance.toFixed(2)} ALGO
                  </div>
                  <div className="access-status">
                    <strong>Access:</strong> 
                    <span className={accountInfo.hasAccess ? 'granted' : 'denied'}>
                      {accountInfo.hasAccess ? '✅ Granted' : '❌ Denied (Need 5+ ALGO)'}
                    </span>
                  </div>
                </div>
              )}

              <div className="account-actions">
                <button onClick={refreshAccountInfo} disabled={loading} className="secondary-button">
                  Refresh Balance
                </button>
                <button onClick={drainAccountFunds} disabled={loading} className="danger-button">
                  Drain Account (Test)
                </button>
                <button onClick={fundAccount} disabled={loading || !drainAccount} className="success-button">
                  Fund Account Back
                </button>
                <button onClick={() => setAccount(null)} className="secondary-button">
                  Switch Account
                </button>
              </div>
            </div>
          )}
        </section>

        {/* Weather Data Section */}
        {account && accountInfo && (
          <section className="weather-section">
            <h2>Weather Data Access</h2>
            
            <div className="weather-controls">
              <div className="city-input">
                <label htmlFor="city">City:</label>
                <input
                  type="text"
                  id="city"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  placeholder="Enter city name"
                />
              </div>
              
              <button 
                onClick={fetchWeatherData} 
                disabled={loading || !accountInfo.hasAccess}
                className="primary-button"
              >
                {loading ? 'Loading...' : 'Get Weather Data'}
              </button>
            </div>

            {weatherData && (
              <div className="weather-display">
                <h3>Weather for {weatherData.data.city}, {weatherData.data.country}</h3>
                <div className="weather-grid">
                  <div className="weather-item">
                    <strong>Temperature:</strong> {weatherData.data.temperature}°C
                  </div>
                  <div className="weather-item">
                    <strong>Feels like:</strong> {weatherData.data.feels_like}°C
                  </div>
                  <div className="weather-item">
                    <strong>Humidity:</strong> {weatherData.data.humidity}%
                  </div>
                  <div className="weather-item">
                    <strong>Description:</strong> {weatherData.data.description}
                  </div>
                  <div className="weather-item">
                    <strong>Wind Speed:</strong> {weatherData.data.wind_speed} m/s
                  </div>
                </div>
                
                <div className="token-info">
                  <strong>Token expires in:</strong> {weatherData.token_info.remaining_time_seconds}s
                </div>
              </div>
            )}
          </section>
        )}

        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {loading && <div className="loading">Loading...</div>}
      </main>
    </div>
  );
}

export default App;
