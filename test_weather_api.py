import requests

# Test OpenWeatherMap API
API_KEY = '17bf4de614fd7c4add7635a6d64b7d06'
location = 'Mumbai'

url = f'http://api.openweathermap.org/data/2.5/weather?q={location}&appid={API_KEY}&units=metric'

print(f"Testing API with URL: {url}")
print("=" * 60)

try:
    response = requests.get(url, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ API is working!")
        print(f"Location: {data['name']}")
        print(f"Temperature: {data['main']['temp']}°C")
        print(f"Humidity: {data['main']['humidity']}%")
        print(f"Rainfall: {data.get('rain', {}).get('1h', 0)} mm")
        print(f"\nFull response:")
        import json
        print(json.dumps(data, indent=2))
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Exception occurred: {str(e)}")
