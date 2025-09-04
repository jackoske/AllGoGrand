import React, { useState } from 'react';
import './App.css';
import axios from 'axios';

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

const BACKEND_URL = 'http://localhost:8000';

function SimpleApp() {
  const [walletAddress, setWalletAddress] = useState('');
  const [weatherData, setWeatherData] = useState<WeatherResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [city, setCity] = useState('London');

  const fetchWeatherData = async () => {
    if (!walletAddress.trim()) {
      setError('Please enter a wallet address');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get<WeatherResponse>(`${BACKEND_URL}/weather`, {
        params: {
          city: city,
          wallet: walletAddress
        }
      });

      setWeatherData(response.data);
    } catch (err: any) {
      if (err.response?.status === 403) {
        setError(`Access denied: ${err.response.data.detail || 'Insufficient balance (need 5+ ALGO)'}`);
      } else {
        setError(`Failed to fetch weather data: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const clearData = () => {
    setWeatherData(null);
    setError(null);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🌤️ Weather Marketplace Demo</h1>
        <p>Token-gated weather data access on Algorand</p>
        <p><small>Simplified version - Enter a wallet address manually</small></p>
      </header>

      <main className="App-main">
        {/* Wallet Input Section */}
        <section className="account-section">
          <h2>Wallet Address</h2>
          <div className="account-info">
            <div className="address-display">
              <label htmlFor="wallet">Enter Algorand wallet address:</label>
              <input
                type="text"
                id="wallet"
                value={walletAddress}
                onChange={(e) => setWalletAddress(e.target.value)}
                placeholder="e.g., 7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  margin: '0.5rem 0',
                  border: '2px solid #e9ecef',
                  borderRadius: '8px',
                  fontSize: '0.9rem',
                  fontFamily: 'Monaco, Consolas, monospace'
                }}
              />
            </div>
            
            <div className="account-actions">
              <button onClick={clearData} className="secondary-button">
                Clear Data
              </button>
            </div>
          </div>
        </section>

        {/* Weather Data Section */}
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
              disabled={loading || !walletAddress.trim()}
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

        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {loading && <div className="loading">Loading...</div>}

        {/* Instructions */}
        <section className="account-section">
          <h2>Instructions</h2>
          <div style={{ textAlign: 'left', maxWidth: '600px', margin: '0 auto' }}>
            <h3>To test the demo:</h3>
            <ol>
              <li><strong>Start LocalNet & Backend:</strong>
                <ul>
                  <li>Run: <code>cd ../../scripts && python setup_demo.py</code></li>
                  <li>Run: <code>cd ../backend && python main.py</code></li>
                </ul>
              </li>
              <li><strong>Get a wallet address:</strong>
                <ul>
                  <li><strong>Rich account (&gt;5 ALGO):</strong> Try <code>7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q</code></li>
                  <li><strong>Poor account (&lt;5 ALGO):</strong> Try <code>GD64YIY3TWGDMCNPP553DZPPR6LDUSFQOIJVFDPPXWEG3FVOJCCDBBHU5A</code></li>
                </ul>
              </li>
              <li><strong>Test Access:</strong>
                <ul>
                  <li>Rich accounts should get weather data ✅</li>
                  <li>Poor accounts should get "Access Denied" ❌</li>
                </ul>
              </li>
            </ol>
            <p><strong>Note:</strong> These are LocalNet test addresses. The backend checks if the wallet has ≥5 ALGO balance.</p>
          </div>
        </section>
      </main>
    </div>
  );
}

export default SimpleApp;