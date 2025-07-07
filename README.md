# 🌱 CropGenius Lite

**CropGenius Lite** is a web-based crop recommendation and cost estimation system designed for farmers and agriculture planners.  
It uses machine learning to suggest the best crop based on soil and climate data, along with tools for cost, yield, and crop info.

> ✅ [Live Demo Here](https://cropgenius-lite.onrender.com/)

---

## 🚀 Features

- 🌾 **Crop Prediction** based on N, P, K, pH, temperature, humidity, and rainfall
- 💰 **Yield & Cost Estimation** based on land area and crop-specific input costs
- 📋 **Crop Information** including soil type, growth duration, diseases, and fertilizers
- 👨‍💼 **Admin Panel** to manage crop data, cost estimations, and disease info
- 🔐 **User Authentication** – Sign up, log in, and protected access
- 🌐 **Multilingual Support** – English + Marathi (via Google Translate)
- 📱 **Mobile-Responsive UI** – Tailwind CSS for seamless experience


---

## 🛠️ Tech Stack

- **Frontend:** HTML, Tailwind CSS, Jinja2
- **Backend:** Python, Flask
- **Database:** SQLite (`crop_info.db`)
- **ML Model:** Scikit-learn (`crop_model.pkl`)
- **Hosting:** Render.com (free deployment)

---

## 🌐 Live Link

👉 [https://cropgenius-lite.onrender.com](https://cropgenius-lite.onrender.com)

---

## 🧪 How to Run Locally

```bash
git clone https://github.com/your-username/cropgenius-lite.git
cd cropgenius-lite
pip install -r requirements.txt
python app.py

📦 cropgenius-lite
├── app.py
├── crop_model.pkl
├── crop_info.db
├── requirements.txt
├── Procfile
├── static/
└── templates/

