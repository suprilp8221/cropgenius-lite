from flask import Flask, render_template, request, session, redirect, flash, jsonify
import sqlite3
import pickle
import numpy as np
import os
import requests
import bcrypt
from datetime import timedelta
# from tensorflow.keras.models import load_model
# from tensorflow.keras.preprocessing import image



app = Flask(__name__)
app.secret_key = 'your_very_secret_key_here'  # Change this in production
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# OpenWeatherMap API Configuration
# Get your free API key from: https://openweathermap.org/api
OPENWEATHER_API_KEY = '4376a58206d0931f720fdb84caa4e16b'  # Replace with your actual API key

# Load trained ML model
with open('crop_model.pkl', 'rb') as model_file:
    model = pickle.load(model_file)

# Function to fetch crop details from the database
def get_crop_info(crop_name):
    conn = sqlite3.connect("crop_info.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name, soil_type, growth_duration, diseases, best_fertilizers, COALESCE(yield_per_acre, 0) 
        FROM crops WHERE LOWER(name)=?
    """, (crop_name.lower(),))
    
    crop_data = cursor.fetchone()
    conn.close()

    if crop_data:
        return {
            "name": crop_data[0],
            "soil_type": crop_data[1],
            "growth_duration": crop_data[2],
            "diseases": crop_data[3],
            "best_fertilizers": crop_data[4],
            "yield_per_acre": crop_data[5]  # Ensuring no NULL values
        }
    return None

# Function to fetch crop cost details from the database
def get_crop_costs(crop_name):
    with sqlite3.connect("crop_info.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT seeds_cost, fertilizers_cost, water_cost, labor_cost, machinery_cost, pesticides_cost, transport_cost
            FROM crop_costs WHERE LOWER(crop_name) = ?
        """, (crop_name.lower(),))
        cost_data = cursor.fetchone()

    if cost_data:
        return {
            "seeds": cost_data[0],
            "fertilizers": cost_data[1],
            "water": cost_data[2],
            "labor": cost_data[3],
            "machinery": cost_data[4],
            "pesticides": cost_data[5],
            "transport": cost_data[6],
            "total": sum(cost_data)  # Total cost calculation
        }
    return None  # If no data found

# Function to fetch market price of a crop
def get_market_price(crop_name):
    with sqlite3.connect("crop_info.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT market_price FROM crop_costs WHERE LOWER(crop_name) = ?", (crop_name.lower(),))
        result = cursor.fetchone()
        return result[0] if result else 0



# Weather API route
@app.route('/get-weather', methods=['POST'])
def get_weather():
    try:
        data = request.get_json()
        location = data.get('location', '').strip()
        
        if not location:
            return jsonify({'error': 'Location is required'}), 400
        
        # Check if API key is configured properly
        if OPENWEATHER_API_KEY == 'YOUR_API_KEY_HERE' or OPENWEATHER_API_KEY == '17bf4de614fd7c4add7635a6d64b7d06':
            # Return demo data if API key is not configured
            demo_data = {
                'Mumbai': {'temp': 28.5, 'humidity': 75, 'rainfall': 2.5},
                'Delhi': {'temp': 32.0, 'humidity': 60, 'rainfall': 0},
                'Pune': {'temp': 26.0, 'humidity': 70, 'rainfall': 1.2},
                'Bangalore': {'temp': 24.5, 'humidity': 65, 'rainfall': 3.0},
                'Chennai': {'temp': 30.0, 'humidity': 80, 'rainfall': 5.0},
                'Kolkata': {'temp': 29.5, 'humidity': 82, 'rainfall': 4.5},
            }
            
            # Check if location matches demo data
            location_key = location.title()
            if location_key in demo_data:
                demo = demo_data[location_key]
                return jsonify({
                    'temperature': demo['temp'],
                    'humidity': demo['humidity'],
                    'rainfall': demo['rainfall'],
                    'location': location_key + ' (Demo Data - Get real API key from openweathermap.org)'
                })
            else:
                # Return default demo values for unknown locations
                return jsonify({
                    'temperature': 27.0,
                    'humidity': 70,
                    'rainfall': 2.0,
                    'location': location + ' (Demo Data - Get real API key from openweathermap.org)'
                })
        
        # Call OpenWeatherMap API with real key
        url = f'http://api.openweathermap.org/data/2.5/weather?q={location}&appid={OPENWEATHER_API_KEY}&units=metric'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            weather_data = response.json()
            
            # Extract required data
            temperature = weather_data['main']['temp']
            humidity = weather_data['main']['humidity']
            
            # Rainfall (mm) - use 1h rain if available, else 0
            rainfall = weather_data.get('rain', {}).get('1h', 0)
            
            # If no recent rain, check if there's any precipitation
            if rainfall == 0:
                # Approximate from weather description or set to minimal value
                weather_desc = weather_data['weather'][0]['main'].lower()
                if 'rain' in weather_desc or 'drizzle' in weather_desc:
                    rainfall = 5  # Default light rain value
            
            return jsonify({
                'temperature': round(temperature, 2),
                'humidity': humidity,
                'rainfall': round(rainfall, 2),
                'location': weather_data['name']
            })
        elif response.status_code == 401:
            return jsonify({'error': 'Invalid API key. Please get a valid key from openweathermap.org'}), 401
        else:
            return jsonify({'error': 'Location not found. Please enter a valid city name.'}), 404
            
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Weather service timeout. Please try again.'}), 500
    except requests.exceptions.RequestException:
        return jsonify({'error': 'Unable to fetch weather data. Please check your internet connection.'}), 500
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


# Home route
@app.route('/')
def home():
    if 'username' not in session:
        return redirect('/signup')  # Redirect to signup if not logged in
    return render_template('index.html')  # Show homepage only if logged in


# User Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect("crop_info.db")
    cursor = conn.cursor()
    
    # Get total predictions count
    cursor.execute("""
        SELECT COUNT(*) FROM prediction_history WHERE username = ?
    """, (session['username'],))
    total_predictions = cursor.fetchone()[0]
    
    # Get most recommended crop
    cursor.execute("""
        SELECT predicted_crop, COUNT(*) as count 
        FROM prediction_history 
        WHERE username = ?
        GROUP BY predicted_crop 
        ORDER BY count DESC 
        LIMIT 1
    """, (session['username'],))
    top_crop_result = cursor.fetchone()
    top_crop = top_crop_result[0] if top_crop_result else None
    
    # Get unique crops count
    cursor.execute("""
        SELECT COUNT(DISTINCT predicted_crop) FROM prediction_history WHERE username = ?
    """, (session['username'],))
    unique_crops = cursor.fetchone()[0]
    
    # Get last activity
    cursor.execute("""
        SELECT prediction_date FROM prediction_history 
        WHERE username = ? 
        ORDER BY prediction_date DESC 
        LIMIT 1
    """, (session['username'],))
    last_activity_result = cursor.fetchone()
    last_activity = last_activity_result[0][:10] if last_activity_result else None
    
    # Get recent predictions (last 5)
    cursor.execute("""
        SELECT id, nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall, 
               predicted_crop, location, prediction_date
        FROM prediction_history 
        WHERE username = ?
        ORDER BY prediction_date DESC
        LIMIT 5
    """, (session['username'],))
    recent_predictions = cursor.fetchall()
    
    # Get crop distribution
    cursor.execute("""
        SELECT predicted_crop, COUNT(*) as count 
        FROM prediction_history 
        WHERE username = ?
        GROUP BY predicted_crop 
        ORDER BY count DESC
    """, (session['username'],))
    crop_distribution = cursor.fetchall()
    
    conn.close()
    
    # Prepare data for chart
    crop_labels = [crop[0] for crop in crop_distribution]
    crop_counts = [crop[1] for crop in crop_distribution]
    
    return render_template('user_dashboard.html', 
                          total_predictions=total_predictions,
                          top_crop=top_crop,
                          unique_crops=unique_crops,
                          last_activity=last_activity,
                          recent_predictions=recent_predictions,
                          crop_distribution=crop_distribution,
                          crop_labels=crop_labels,
                          crop_counts=crop_counts)


# My Predictions History route
@app.route('/my-predictions')
def my_predictions():
    if 'username' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect("crop_info.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall, 
               predicted_crop, location, prediction_date
        FROM prediction_history 
        WHERE username = ?
        ORDER BY prediction_date DESC
    """, (session['username'],))
    predictions = cursor.fetchall()
    conn.close()
    
    return render_template('my_predictions.html', predictions=predictions)


# Delete prediction from history
@app.route('/delete-prediction/<int:prediction_id>')
def delete_prediction(prediction_id):
    if 'username' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect("crop_info.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM prediction_history WHERE id = ? AND username = ?", 
                  (prediction_id, session['username']))
    conn.commit()
    conn.close()
    
    return redirect('/my-predictions')


# Compare Crops route
@app.route('/compare-crops', methods=['GET', 'POST'])
def compare_crops():
    if 'username' not in session:
        return redirect('/login')
    
    selected_crops = []
    comparison_data = []
    
    if request.method == 'POST':
        # Get selected crops from form
        crop1 = request.form.get('crop1', '').strip()
        crop2 = request.form.get('crop2', '').strip()
        crop3 = request.form.get('crop3', '').strip()
        
        selected_crops = [c for c in [crop1, crop2, crop3] if c]
        
        # Fetch details for each crop
        conn = sqlite3.connect("crop_info.db")
        cursor = conn.cursor()
        
        for crop in selected_crops:
            # Get crop info
            cursor.execute("""
                SELECT name, soil_type, growth_duration, diseases, best_fertilizers, 
                       COALESCE(yield_per_acre, 0)
                FROM crops WHERE LOWER(name) = ?
            """, (crop.lower(),))
            crop_data = cursor.fetchone()
            
            # Get cost info
            cursor.execute("""
                SELECT seeds_cost, fertilizers_cost, water_cost, labor_cost, 
                       machinery_cost, pesticides_cost, transport_cost, market_price
                FROM crop_costs WHERE LOWER(crop_name) = ?
            """, (crop.lower(),))
            cost_data = cursor.fetchone()
            
            if crop_data:
                total_cost = sum(cost_data[:7]) if cost_data else 0
                market_price = cost_data[7] if cost_data else 0
                yield_per_acre = crop_data[5]
                profit_per_acre = (market_price * yield_per_acre) - total_cost if market_price and yield_per_acre else 0
                
                comparison_data.append({
                    'name': crop_data[0],
                    'soil_type': crop_data[1],
                    'growth_duration': crop_data[2],
                    'diseases': crop_data[3],
                    'fertilizers': crop_data[4],
                    'yield_per_acre': yield_per_acre,
                    'total_cost': total_cost,
                    'market_price': market_price,
                    'profit_per_acre': profit_per_acre,
                    'costs': {
                        'seeds': cost_data[0] if cost_data else 0,
                        'fertilizers': cost_data[1] if cost_data else 0,
                        'water': cost_data[2] if cost_data else 0,
                        'labor': cost_data[3] if cost_data else 0,
                        'machinery': cost_data[4] if cost_data else 0,
                        'pesticides': cost_data[5] if cost_data else 0,
                        'transport': cost_data[6] if cost_data else 0,
                    } if cost_data else {}
                })
        
        conn.close()
    
    # Get all available crops for dropdown
    conn = sqlite3.connect("crop_info.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT name FROM crops ORDER BY name")
    all_crops = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return render_template('compare_crops.html', 
                          comparison_data=comparison_data, 
                          all_crops=all_crops,
                          selected_crops=selected_crops)


# Predict route
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get user inputs
        N = float(request.form.get('N', 0))
        P = float(request.form.get('P', 0))
        K = float(request.form.get('K', 0))
        temperature = float(request.form.get('temperature', 0))
        humidity = float(request.form.get('humidity', 0))
        pH = float(request.form.get('pH', 0))
        rainfall = float(request.form.get('rainfall', 0))
        location = request.form.get('location', '')  # Optional location field

        # Create input array
        input_data = np.array([[N, P, K, temperature, humidity, pH, rainfall]])
        
        # Predict crop
        predicted_crop = model.predict(input_data)[0]

        # Save prediction to history if user is logged in
        if 'username' in session:
            conn = sqlite3.connect("crop_info.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO prediction_history 
                (username, nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall, predicted_crop, location)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (session['username'], N, P, K, temperature, humidity, pH, rainfall, predicted_crop, location))
            conn.commit()
            conn.close()

        # Fetch crop details
        crop_info = get_crop_info(predicted_crop)

        return render_template('result.html', crop=predicted_crop, crop_info=crop_info)

    except Exception as e:
        return f"Error: {str(e)}"
    
@app.route('/yield_cost', methods=['GET', 'POST'])
def yield_cost():
    # Get all available crops for dropdown
    conn = sqlite3.connect("crop_info.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT name FROM crops ORDER BY name")
    all_crops = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Get crop from URL parameter or form submission
    crop = request.args.get('crop', '') or request.form.get('crop', '')
    land_area = request.form.get('land_area', 1, type=float)  # Default land_area to 1

    # Initialize variables
    crop_info = None
    estimated_yield = 0
    cost_details = None
    total_cost = 0
    market_price = 0
    profit = 0

    if crop:
        # Fetch crop yield info
        crop_info = get_crop_info(crop)
        estimated_yield = land_area * crop_info["yield_per_acre"] if crop_info else 0

        # Fetch cost details
        cost_details = get_crop_costs(crop)

        if cost_details:
            # Multiply each cost by land area
            for key in cost_details:
                if key != "total":
                    cost_details[key] *= land_area
            cost_details["total"] *= land_area  # Scale total cost too
            total_cost = cost_details["total"]

        # Calculate market price and profit
        market_price = get_market_price(crop)
        total_revenue = market_price * estimated_yield
        profit = total_revenue - total_cost

    return render_template('yield_cost.html', 
                          crop=crop, 
                          estimated_yield=estimated_yield, 
                          total_cost=total_cost, 
                          cost_details=cost_details,
                          all_crops=all_crops,
                          land_area=land_area,
                          market_price=market_price,
                          profit=profit)

@app.route('/smart_bima', methods=['GET', 'POST'])
def smart_bima():
    if 'username' not in session:
        return redirect('/login')
    
    # Get all insurance schemes
    conn = sqlite3.connect("crop_info.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM insurance_schemes ORDER BY scheme_name")
    schemes_raw = cursor.fetchall()
    
    # Get all crops for dropdown
    cursor.execute("SELECT DISTINCT name FROM crops ORDER BY name")
    all_crops = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    # Convert schemes to dict format
    schemes = []
    for scheme in schemes_raw:
        schemes.append({
            'id': scheme[0],
            'scheme_name': scheme[1],
            'scheme_type': scheme[2],
            'coverage_type': scheme[3],
            'base_premium_rate': scheme[4],
            'subsidy_percentage': scheme[5],
            'max_sum_insured': scheme[6],
            'description': scheme[7],
            'eligibility': scheme[8]
        })
    
    premium_details = None
    selected_scheme = None
    selected_crop = None
    land_area = None
    sum_insured = None
    
    if request.method == 'POST':
        scheme_id = request.form.get('scheme_id', type=int)
        selected_crop = request.form.get('crop')
        land_area = request.form.get('land_area', type=float)
        sum_insured = request.form.get('sum_insured', type=float)
        
        # Get selected scheme details
        selected_scheme = next((s for s in schemes if s['id'] == scheme_id), None)
        
        if selected_scheme and sum_insured:
            # Calculate premium
            base_premium = (selected_scheme['base_premium_rate'] / 100) * sum_insured
            subsidy_amount = (selected_scheme['subsidy_percentage'] / 100) * base_premium
            farmer_premium = base_premium - subsidy_amount
            
            premium_details = {
                'scheme_name': selected_scheme['scheme_name'],
                'scheme_type': selected_scheme['scheme_type'],
                'coverage_type': selected_scheme['coverage_type'],
                'crop': selected_crop,
                'land_area': land_area,
                'sum_insured': sum_insured,
                'premium_rate': selected_scheme['base_premium_rate'],
                'base_premium': base_premium,
                'subsidy_percentage': selected_scheme['subsidy_percentage'],
                'subsidy_amount': subsidy_amount,
                'farmer_premium': farmer_premium
            }
    
    return render_template('smart_bima.html',
                          schemes=schemes,
                          all_crops=all_crops,
                          premium_details=premium_details,
                          selected_scheme=selected_scheme,
                          selected_crop=selected_crop,
                          land_area=land_area,
                          sum_insured=sum_insured)

@app.route('/disease-detect')
def disease_detect_disabled():
    return render_template('disease_detect.html')

# # Load models once
# tomato_model = load_model("tomato_disease_model.h5")
# potato_model = load_model("potato_disease_model.h5")

# # Class labels
# tomato_classes = ['Tomato_Early_blight', 'Tomato_Late_blight', 'Tomato_healthy']
# potato_classes = ['Potato__Early_blight', 'Potato__Late_blight', 'Potato__healthy']


# @app.route('/disease-detect', methods=['GET', 'POST'])
# def detect_disease():
#     if request.method == 'POST':
#         crop = request.form['crop']
#         file = request.files['file']
#         if file:
#             filepath = os.path.join('static', 'uploads', file.filename)
#             file.save(filepath)

#             # Preprocess
#             img = image.load_img(filepath, target_size=(128, 128))
#             img_array = image.img_to_array(img)
#             img_array = np.expand_dims(img_array, axis=0) / 255.0

#             # Select model & classes
#             if crop == 'Tomato':
#                 model = tomato_model
#                 class_labels = tomato_classes
#             elif crop == 'Potato':
#                 model = potato_model
#                 class_labels = potato_classes
#             else:
#                 return "Unsupported crop selected."

#             # Predict
#             prediction = model.predict(img_array)
#             class_index = np.argmax(prediction[0])
#             predicted_class = class_labels[class_index]

#             # 🔗 Fetch fertilizer, tip, cause from database
#             conn = sqlite3.connect('crop_info.db')
#             cursor = conn.cursor()
#             cursor.execute("""
#                 SELECT fertilizer, prevention_tip, cause
#                 FROM disease_info
#                 WHERE disease_name = ?
#             """, (predicted_class,))
#             row = cursor.fetchone()
#             conn.close()

#             if row:
#                 fertilizer, tip, cause = row
#             else:
#                 fertilizer, tip, cause = "Unknown", "No tip available.", "Unknown cause."

#             # Return result page
#             return render_template('disease_result.html',
#                                    crop=crop,
#                                    predicted_class=predicted_class,
#                                    fertilizer=fertilizer,
#                                    tip=tip,
#                                    cause=cause,
#                                    image_path=filepath)

#     return render_template('disease_detect.html')


# Function to calculate estimated yield based on land area
def calculate_yield(crop, land_area):
    crop_info = get_crop_info(crop)  # Fetch yield per acre from database
    if crop_info and crop_info["yield_per_acre"]:
        return land_area * crop_info["yield_per_acre"]
    return 0  # Default to 0 if no data found

# Function to calculate estimated cost based on land area
def calculate_cost(crop, land_area):
    cost_details = get_crop_costs(crop)  # Fetch cost details from database
    if cost_details:
        # Multiply each cost by land area
        for key in cost_details:
            if key != "total":
                cost_details[key] *= land_area
        cost_details["total"] *= land_area  # Scale total cost too
        return cost_details, cost_details["total"]
    return None, 0  # Default to 0 if no data found


@app.route('/calculate_yield_cost', methods=['POST'])
def calculate_yield_cost():
    try:
        crop = request.form.get("crop")  
        land_area = request.form.get("land_area", "").strip()

        # ✅ Check if land_area is empty before proceeding
        if not land_area:
            return render_template('yield_cost.html', crop=crop, estimated_yield=None,
                                   cost_details=None, total_cost=None,
                                   market_price=None, profit=None)

        land_area = float(land_area)

        # ✅ Calculate yield and cost
        estimated_yield = calculate_yield(crop, land_area)
        cost_details, total_cost = calculate_cost(crop, land_area)

        # ✅ Fetch market price
        market_price = get_market_price(crop)

        # ✅ Calculate profit
        profit = (market_price * estimated_yield) - total_cost

        return render_template('yield_cost.html',
                               crop=crop,
                               estimated_yield=estimated_yield,
                               cost_details=cost_details,
                               total_cost=total_cost,
                               market_price=market_price,
                               profit=profit)
    
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Validation
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('signup.html', error='Username and password are required.')
        
        if len(username) < 3:
            return render_template('signup.html', error='Username must be at least 3 characters long.')
        
        if len(password) < 6:
            return render_template('signup.html', error='Password must be at least 6 characters long.')

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Save to database
        conn = sqlite3.connect("crop_info.db")
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                          (username, hashed_password))
            conn.commit()
            conn.close()
            flash('Account created successfully! Please login.', 'success')
            return redirect('/login')
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('signup.html', error='Username already exists. Please try another.')

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            return render_template('login.html', error='Please enter both username and password.')

        conn = sqlite3.connect("crop_info.db")
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[0]):
            session.permanent = True
            session['username'] = username
            return redirect('/')
        else:
            return render_template('login.html', error='Invalid username or password. Please try again.')

    return render_template('login.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            return render_template('login.html', error='Please enter both username and password.')

        conn = sqlite3.connect("crop_info.db")
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM admin WHERE username=?", (username,))
        admin = cursor.fetchone()
        conn.close()

        if admin and bcrypt.checkpw(password.encode('utf-8'), admin[0]):
            session.permanent = True
            session['admin'] = username
            return redirect('/admin-dashboard')
        else:
            return render_template('login.html', error='Invalid admin credentials. Please try again.')

    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin-login')

    # Fetch all crop records
    conn = sqlite3.connect("crop_info.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM crops")
    crops = cursor.fetchall()
    conn.close()

    return render_template('admin_dashboard.html', admin=session['admin'], crops=crops)

@app.route('/delete-crop/<name>')
def delete_crop(name):
    if 'admin' not in session:
        return redirect('/admin-login')

    conn = sqlite3.connect("crop_info.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM crops WHERE name = ?", (name,))
    conn.commit()
    conn.close()

    return redirect('/admin')

@app.route('/edit-crop/<name>', methods=['GET', 'POST'])
def edit_crop(name):
    if 'admin' not in session:
        return redirect('/admin-login')

    conn = sqlite3.connect("crop_info.db")
    cursor = conn.cursor()

    if request.method == 'POST':
        soil_type = request.form.get('soil_type')
        growth_duration = request.form.get('growth_duration')
        diseases = request.form.get('diseases')
        best_fertilizers = request.form.get('best_fertilizers')
        yield_per_acre = request.form.get('yield_per_acre')

        cursor.execute("""
            UPDATE crops SET
                soil_type = ?,
                growth_duration = ?,
                diseases = ?,
                best_fertilizers = ?,
                yield_per_acre = ?
            WHERE name = ?
        """, (soil_type, growth_duration, diseases, best_fertilizers, yield_per_acre, name))

        conn.commit()
        conn.close()
        return redirect('/admin')

    # GET request → fetch current crop data
    cursor.execute("SELECT * FROM crops WHERE name = ?", (name,))
    crop = cursor.fetchone()
    conn.close()

    if crop:
        return render_template('edit_crop.html', crop=crop)
    else:
        return "Crop not found", 404

@app.route('/add-crop', methods=['GET', 'POST'])
def add_crop():
    if 'admin' not in session:
        return redirect('/admin-login')

    if request.method == 'POST':
        name = request.form.get('name').strip()
        soil_type = request.form.get('soil_type').strip()
        growth_duration = request.form.get('growth_duration').strip()
        diseases = request.form.get('diseases').strip()
        best_fertilizers = request.form.get('best_fertilizers').strip()
        yield_per_acre = request.form.get('yield_per_acre')

        conn = sqlite3.connect("crop_info.db")
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO crops (name, soil_type, growth_duration, diseases, best_fertilizers, yield_per_acre)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, soil_type, growth_duration, diseases, best_fertilizers, yield_per_acre))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "❌ Crop with this name already exists."
        conn.close()
        return redirect('/admin')

    return render_template('add_crop.html')

@app.route('/admin-dashboard')
def admin_main_dashboard():
    if 'admin' not in session:
        return redirect('/admin-login')
    return render_template('admin_main_dashboard.html', admin=session['admin'])

@app.route('/admin-diseases')
def admin_diseases():
    if 'admin' not in session:
        return redirect('/admin-login')

    conn = sqlite3.connect("crop_info.db")
    cursor = conn.cursor()
    cursor.execute("SELECT disease_name, fertilizer, prevention_tip, cause FROM disease_info")
    diseases = cursor.fetchall()
    conn.close()

    return render_template('admin_diseases.html', diseases=diseases)

@app.route('/edit-disease/<disease_name>', methods=['GET', 'POST'])
def edit_disease(disease_name):
    if 'admin' not in session:
        return redirect('/admin-login')

    conn = sqlite3.connect("crop_info.db")
    cursor = conn.cursor()

    if request.method == 'POST':
        fertilizer = request.form.get('fertilizer').strip()
        prevention_tip = request.form.get('prevention_tip').strip()
        cause = request.form.get('cause').strip()

        cursor.execute("""
            UPDATE disease_info
            SET fertilizer = ?, prevention_tip = ?, cause = ?
            WHERE disease_name = ?
        """, (fertilizer, prevention_tip, cause, disease_name))

        conn.commit()
        conn.close()
        return redirect('/admin-diseases')

    # GET method — fetch current data
    cursor.execute("""
        SELECT disease_name, fertilizer, prevention_tip, cause
        FROM disease_info WHERE disease_name = ?
    """, (disease_name,))
    disease = cursor.fetchone()
    conn.close()

    if disease:
        return render_template('edit_disease.html', disease=disease)
    else:
        return "Disease not found", 404

@app.route('/admin-costs')
def admin_costs():
    if 'admin' not in session:
        return redirect('/admin-login')

    conn = sqlite3.connect("crop_info.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM crop_costs")
    costs = cursor.fetchall()
    conn.close()

    return render_template('admin_costs.html', costs=costs)

@app.route('/edit-cost/<name>', methods=['GET', 'POST'])
def edit_cost(name):
    if 'admin' not in session:
        return redirect('/admin-login')

    conn = sqlite3.connect("crop_info.db")
    cursor = conn.cursor()

    if request.method == 'POST':
        data = (
            request.form.get('seeds_cost'),
            request.form.get('fertilizers_cost'),
            request.form.get('water_cost'),
            request.form.get('labor_cost'),
            request.form.get('machinery_cost'),
            request.form.get('pesticides_cost'),
            request.form.get('transport_cost'),
            name
        )

        cursor.execute("""
            UPDATE crop_costs
            SET seeds_cost=?, fertilizers_cost=?, water_cost=?, labor_cost=?,
                machinery_cost=?, pesticides_cost=?, transport_cost=?
            WHERE crop_name=?
        """, data)

        conn.commit()
        conn.close()
        return redirect('/admin-costs')

    # GET request
    cursor.execute("SELECT * FROM crop_costs WHERE crop_name = ?", (name,))
    cost = cursor.fetchone()
    conn.close()

    if cost:
        return render_template('edit_cost.html', cost=cost)
    else:
        return "❌ Cost data not found for this crop", 404



@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
