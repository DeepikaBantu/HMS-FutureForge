# HMS-FutureForge
BioNode - AI-powered IoT patient health monitoring system using ESP32. Monitors Heart Rate, SpO2, Body Temperature, Room Temperature &amp; Humidity. Features ML predictions, bilingual voice alerts (English/Telugu), automated email reports, and live web dashboard. Designed for hospital use.
# 🏥 BioNode - AI-Powered Patient Health Monitoring System

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![ESP32](https://img.shields.io/badge/ESP32-Arduino-green.svg)](https://www.arduino.cc/)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-red.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📌 Overview

**BioNode** is an IoT-based AI-powered patient health monitoring system that collects real-time vital signs using ESP32 and multiple sensors, analyzes data using machine learning, and generates automated hospital reports with voice alerts in **English and Telugu**.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| 📊 **5 Vital Parameters** | Heart Rate, SpO2, Body Temp, Room Temp, Humidity |
| 🤖 **AI Analysis** | Health Status, Fever Risk, Stress Level prediction |
| 🚨 **Predictive Alerts** | Early warning for critical conditions |
| 🔊 **Bilingual Voice** | English & Telugu text-to-speech alerts |
| 📧 **Auto Email Reports** | Professional hospital-grade reports |
| 🖥️ **Live Dashboard** | Real-time web dashboard |
| 👥 **Patient Management** | Register and track multiple patients |

---

## 🩺 Vital Signs & Normal Ranges

| Parameter | Sensor | Normal Range |
|-----------|--------|--------------|
| ❤️ Heart Rate | MAX30100 | 60-100 BPM |
| 🫁 SpO2 | MAX30100 | 95-100% |
| 🌡️ Body Temp | DS18B20 | 36.1-37.2°C |
| 🏠 Room Temp | DHT11 | 20-30°C |
| 💧 Humidity | DHT11 | 30-60% |

---

## 🛠️ Hardware Required

| Component | Quantity |
|-----------|----------|
| ESP32 Development Board | 1 |
| MAX30100 Sensor | 1 |
| DHT11 Sensor | 1 |
| DS18B20 Sensor | 1 |
| 4.7kΩ Resistor | 1 |
| Breadboard & Jumper Wires | As needed |

### 🔌 Wiring Connections
MAX30100 ESP32
VCC ───► 3.3V
GND ───► GND
SDA ───► GPIO21
SCL ───► GPIO22

DHT11 ESP32
VCC ───► 3.3V
GND ───► GND
DATA ───► GPIO18

DS18B20 ESP32
VCC ───► 3.3V
GND ───► GND
DATA ───► GPIO5 (with 4.7kΩ resistor to 3.3V)

text

---

## 💻 Software Installation

### 1. Install Python Dependencies
```bash
pip install numpy pandas scikit-learn flask yagmail pyttsx3 gtts pygame pyserial
2. Install Arduino Libraries
Open Arduino IDE → Tools → Manage Libraries → Install:

MAX30100 by OXullo Intersecans

DHT sensor library by Adafruit

DallasTemperature by Miles Burton

3. Upload ESP32 Code
Open Arduino IDE

Select Board: DOIT ESP32 DEVKIT V1

Select Port: COM3 (or your ESP32 port)

Click Upload

🚀 How to Run
Step 1: Train ML Models (First Time Only)
bash
python 0_create_dummy_data.py
python 1_label_data.py
python 2_train_model.py
Step 2: Run the Application
bash
python fin.py
Step 3: Follow Prompts
Enter Patient Name, Age, Email

Place finger on MAX30100 sensor

Press Enter to start

Keep finger steady for 5 readings

Step 4: View Dashboard
Open browser: http://localhost:5000

📊 System Workflow
text
Patient Registration → Place Finger → 5 Readings (3 sec each)
         ↓
   AI Analysis (Health, Fever, Stress)
         ↓
   Voice Alerts (English + Telugu)
         ↓
   Email Report + Live Dashboard
🎯 AI Predictions
Output	Possible Values
Health Status	Normal / Moderate / Critical
Fever Risk	No Fever / Low Fever / High Fever
Stress Level	Low Stress / Moderate Stress / High Stress
Fallback Logic (if no ML models):
text
Normal:    HR 60-100, SpO2 ≥95%, Temp 36.1-37.2°C
Moderate:  Slightly abnormal values
Critical:  HR >120 or <50, SpO2 <90%, Temp >38.5°C or <35°C
📧 Email Report Includes
Patient Name, Age, ID, Date

Overall Health Condition

Average of 5 Vital Signs

AI Analysis Results

Predictive Alerts

Health Recommendations

Hospital Contact Information

🌐 Dashboard Access
URL	Description
http://localhost:5000	Live patient monitoring dashboard
Dashboard shows:

Real-time vital signs

Health condition status

AI diagnosis

Predictive alerts

Patient information

🔧 Troubleshooting
Problem	Solution
ESP32 not connecting	Close Arduino Serial Monitor, unplug/replug ESP32
No sensor readings	Place finger FLAT and FIRM, wait 10-15 seconds
SpO2 = 0%	Increase LED current to 50mA in code
Email not sending	Use Gmail App Password, not regular password
Voice not working	Run: pip install pyttsx3 gtts pygame
COM port error	Check Device Manager for correct COM port
📁 Project Files
File	Purpose
fin.py	Main application
0_create_dummy_data.py	Generate training data
1_label_data.py	Label data for ML
2_train_model.py	Train ML models
model_*.pkl	Trained ML models
label_encoders.pkl	Encoded labels
patients/	Patient data storage
🚨 Emergency Alerts
Auto-triggered when:

CRITICAL: HR >120 or <50, SpO2 <90%, Temp >38.5°C

WARNING: HR >110 or <60, SpO2 <94%, Temp >37.5°C

Voice alerts play immediately in English & Telugu.

🧪 Testing
Test with Simulated Data
bash
python fin.py
# Enter manual values when prompted:
# Format: HR,SpO2,BodyTemp,RoomTemp,Humidity
# Example: 75,98,36.8,25,55
Test Emergency Alert
bash
# Enter critical values:
120,85,39.0,25,55
📈 Future Enhancements
Mobile App Integration

Cloud Database Storage

Multi-language Support (Hindi, Tamil)

Doctor Dashboard

Prescription Generation

WhatsApp Integration

📄 License
MIT License - Free for academic and research use.

🙏 Acknowledgments
Anurag Engineering College - Project guidance

Apollo Hospitals - Healthcare consultation

Open-source community

📧 Contact
For support or queries:

Email: 23c11a0536@anurag.ac.in

GitHub: DeepikaBantu

⭐ Show Your Support
If this project helped you, please give it a star on GitHub!

Built with ❤️ for Healthcare Innovation 🏥
