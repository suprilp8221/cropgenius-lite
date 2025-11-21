# 🌤️ Weather API Setup Instructions

## How to Get Your Free OpenWeatherMap API Key

### Step 1: Sign Up
1. Go to [https://openweathermap.org/api](https://openweathermap.org/api)
2. Click on **"Sign Up"** (or **"Sign In"** if you already have an account)
3. Fill in your details:
   - Email address
   - Username
   - Password
4. Verify your email address

### Step 2: Get API Key
1. After logging in, go to your profile (click on your username)
2. Navigate to **"API keys"** tab
3. You'll see a default API key already created
4. Or create a new one by entering a name and clicking **"Generate"**
5. **Copy your API key** (it looks like: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`)

### Step 3: Add API Key to Your Project
1. Open `app.py` file
2. Find this line (around line 17):
   ```python
   OPENWEATHER_API_KEY = 'YOUR_API_KEY_HERE'
   ```
3. Replace `YOUR_API_KEY_HERE` with your actual API key:
   ```python
   OPENWEATHER_API_KEY = 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6'
   ```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Run the Application
```bash
python app.py
```

## 📝 Important Notes

- **Free Tier Limits**: 
  - 1,000 API calls per day
  - 60 calls per minute
  - Sufficient for testing and small-scale use

- **API Activation**: 
  - New API keys may take 10-15 minutes to activate
  - If you get "Invalid API key" error, wait a bit and try again

- **Security**: 
  - Never commit your API key to public repositories
  - Consider using environment variables for production:
    ```python
    import os
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', 'YOUR_API_KEY_HERE')
    ```

## 🧪 Testing the Feature

1. Run your Flask application
2. Navigate to the home page
3. In the **"Auto-Fill Weather Data"** section:
   - Enter a city name (e.g., "Mumbai", "Delhi", "Pune")
   - Click **"Get Weather"** button
4. Temperature, Humidity, and Rainfall fields will auto-populate
5. Fill in remaining fields (N, P, K, pH)
6. Click **"Predict Crop"**

## 🔧 Troubleshooting

### Error: "Location not found"
- Check spelling of city name
- Try using larger cities
- Use English names (e.g., "Mumbai" not "मुंबई")

### Error: "Invalid API key"
- Verify you copied the API key correctly
- Wait 10-15 minutes after generating new key
- Check if you're logged into OpenWeatherMap

### Error: "Weather service timeout"
- Check your internet connection
- Try again after a few seconds
- OpenWeatherMap servers might be busy

## 🌍 Supported Locations

You can use:
- City names: "Mumbai", "Delhi", "Bangalore"
- City + State: "Pune, Maharashtra"
- City + Country: "Mumbai, India"

## 📊 Weather Data Provided

- **Temperature**: Current temperature in Celsius (°C)
- **Humidity**: Current humidity percentage (%)
- **Rainfall**: Recent rainfall in millimeters (mm)
  - If no recent rain detected, defaults to 0 or estimated value

---

**Need Help?** Check [OpenWeatherMap Documentation](https://openweathermap.org/current)
