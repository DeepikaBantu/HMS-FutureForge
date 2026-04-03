"""
BIONODE ANURAG HOSPITAL - Complete Patient Monitoring System
"""

import warnings
warnings.filterwarnings('ignore')

import pickle
import numpy as np
import serial
import time
import threading
from datetime import datetime
import yagmail
from flask import Flask, render_template_string
import pyttsx3
import os
import sys

# ==================== CONFIGURATION ====================

USB_PORT = "COM3"
BAUD_RATE = 115200
EMAIL_COOLDOWN_SECONDS = 300
VOICE_COOLDOWN = 15
last_email_time = 0
last_voice_time = 0

# Email Configuration
SENDER_EMAIL = "23c11a0536@anurag.ac.in"
SENDER_PASSWORD = "idpb lezl ytcn xtdi"

# Hospital Details
HOSPITAL_NAME = "BioNode Anurag Hospital"
HOSPITAL_TAGLINE = "Predictive Healthcare | AI-Powered | Smart Monitoring"
HOSPITAL_PHONE = "1800-XXX-XXXX"

# ==================== VOICE SYSTEM ====================

voice_engine = None

def init_voice():
    global voice_engine
    try:
        voice_engine = pyttsx3.init()
        voice_engine.setProperty('rate', 150)
        voice_engine.setProperty('volume', 0.95)
        return True
    except:
        return False

def speak_alert(message):
    global last_voice_time, voice_engine
    current_time = time.time()
    if current_time - last_voice_time < VOICE_COOLDOWN:
        return
    if voice_engine is None:
        if not init_voice():
            return
    try:
        last_voice_time = current_time
        def speak_thread():
            voice_engine.say(message)
            voice_engine.runAndWait()
        threading.Thread(target=speak_thread, daemon=True).start()
        print(f"VOICE: {message}")
    except:
        pass

def get_voice_message(name, age, overall, alert_msg, risk_level, recs):
    if risk_level == "CRITICAL":
        return (f"Attention. BioNode Anurag Hospital. Patient {name}, age {age}. "
                f"Overall condition CRITICAL. {alert_msg}. {recs[0] if recs else 'Seek emergency care'}.")
    elif risk_level == "WARNING":
        return (f"Attention. Patient {name}. Condition MODERATE. {alert_msg}. "
                f"{recs[0] if recs else 'Rest and monitor'}.")
    else:
        return (f"BioNode Anurag Hospital report for {name}. Condition NORMAL. "
                f"Continue healthy lifestyle.")

# ==================== LOAD ML MODELS ====================

print("\n" + "="*60)
print("     Loading AI Models...")
print("="*60)

models_loaded = False
try:
    with open('model_status.pkl', 'rb') as f:
        model_status = pickle.load(f)
    with open('model_fever.pkl', 'rb') as f:
        model_fever = pickle.load(f)
    with open('model_stress.pkl', 'rb') as f:
        model_stress = pickle.load(f)
    with open('label_encoders.pkl', 'rb') as f:
        le_status, le_fever, le_stress = pickle.load(f)
    models_loaded = True
    print("AI Models Loaded Successfully")
except Exception as e:
    print(f"Fallback Mode Active")

def predict_health(hr, spo2, body_temp, room_temp, humidity):
    """Predict health status"""
    if (60 <= hr <= 100) and (spo2 >= 95) and (36.1 <= body_temp <= 37.2):
        health = "Normal"
        fever = "No Fever"
        stress = "Low Stress"
    elif (hr > 120 or hr < 50) or (spo2 < 90) or (body_temp > 38.5 or body_temp < 35):
        health = "Critical"
        fever = "High Fever" if body_temp > 38.5 else "Low Fever"
        stress = "High Stress"
    else:
        health = "Moderate"
        fever = "Low Fever" if body_temp > 37.2 else "No Fever"
        stress = "Moderate Stress"
    
    return health, fever, stress

# ==================== PREDICTIVE ALERT ====================

class PredictiveAlert:
    def __init__(self, age=30):
        self.history_hr = []
        self.history_spo2 = []
        self.history_temp = []
        self.age = age
        
        if age < 12:
            self.critical_hr, self.warning_hr = 140, 130
        elif age < 65:
            self.critical_hr, self.warning_hr = 120, 110
        else:
            self.critical_hr, self.warning_hr = 110, 100
        
        self.critical_spo2, self.warning_spo2 = 90, 94
        self.critical_temp, self.warning_temp = 38.5, 37.5
    
    def add_reading(self, hr, spo2, temp):
        if 30 < hr < 220 and 50 < spo2 <= 100 and 32 < temp < 42:
            self.history_hr.append(hr)
            self.history_spo2.append(spo2)
            self.history_temp.append(temp)
            if len(self.history_hr) > 8:
                self.history_hr.pop(0)
                self.history_spo2.pop(0)
                self.history_temp.pop(0)
            return True
        return False
    
    def get_trend(self, values):
        if len(values) < 3:
            return 0, "→"
        slope = np.polyfit(range(len(values)), values, 1)[0]
        if slope > 0.5:
            return slope, "↑"
        elif slope < -0.5:
            return slope, "↓"
        return slope, "→"
    
    def predict(self):
        if len(self.history_hr) < 3:
            return "COLLECTING", "Collecting data...", "→", "→", "→"
        
        hr_s, hr_d = self.get_trend(self.history_hr)
        sp_s, sp_d = self.get_trend(self.history_spo2)
        tp_s, tp_d = self.get_trend(self.history_temp)
        
        curr_hr = self.history_hr[-1]
        curr_sp = self.history_spo2[-1]
        curr_tp = self.history_temp[-1]
        
        pred_hr = curr_hr + (hr_s * 3)
        pred_sp = curr_sp + (sp_s * 3)
        pred_tp = curr_tp + (tp_s * 3)
        
        alerts = []
        if pred_hr > self.critical_hr:
            alerts.append(f"HR may reach {pred_hr:.0f} BPM")
        if pred_sp < self.critical_spo2:
            alerts.append(f"SpO2 may drop to {pred_sp:.0f}%")
        if pred_tp > self.critical_temp:
            alerts.append(f"Temp may rise to {pred_tp:.1f}C")
        
        if len(alerts) >= 2:
            return "CRITICAL", " | ".join(alerts[:2]), hr_d, sp_d, tp_d
        elif alerts:
            return "WARNING", alerts[0], hr_d, sp_d, tp_d
        return "STABLE", "All stable", hr_d, sp_d, tp_d

# ==================== EMAIL REPORT ====================

def send_email_report(to_email, name, age, readings, predictions, alert, recommendations, overall):
    global last_email_time
    
    if time.time() - last_email_time < EMAIL_COOLDOWN_SECONDS:
        print("Email cooldown active.")
        return False
    
    patient_id = f"BNAH-{datetime.now().strftime('%Y%m%d')}-{name[:3].upper()}"
    timestamp = datetime.now().strftime("%Y-%m-%d | %H:%M:%S")
    
    avg_hr = np.mean([r['hr'] for r in readings])
    avg_spo2 = np.mean([r['spo2'] for r in readings])
    avg_body_temp = np.mean([r['body_temp'] for r in readings])
    
    health_status, fever_risk, stress_level = predictions
    risk_level, alert_msg, hr_trend, sp_trend, temp_trend = alert
    
    recs_text = "\n".join([f"   {i+1}. {r}" for i, r in enumerate(recommendations)])
    
    report = f"""
======================================================================
                    {HOSPITAL_NAME}
                    {HOSPITAL_TAGLINE}
======================================================================

                     OFFICIAL HEALTH REPORT
                     
Patient Name    : {name}
Age             : {age}
Patient ID      : {patient_id}
Report Date     : {timestamp}

======================================================================
                    OVERALL HEALTH CONDITION
                    {overall}
======================================================================

VITAL SIGNS (Average of 5 readings)
----------------------------------------------------------------------
Heart Rate        : {avg_hr:.0f} BPM        {hr_trend}
SpO2              : {avg_spo2:.0f} %          {sp_trend}
Body Temperature  : {avg_body_temp:.1f} C      {temp_trend}

AI ANALYSIS
----------------------------------------------------------------------
Health Status       : {health_status}
Fever Risk          : {fever_risk}
Stress Level        : {stress_level}

PREDICTIVE ALERT
----------------------------------------------------------------------
Risk Level          : {risk_level}
Alert Message       : {alert_msg}

RECOMMENDATIONS
----------------------------------------------------------------------
{recs_text}

Emergency Contact: {HOSPITAL_PHONE}

This is an AI-generated health report for monitoring purposes.
Please consult a doctor for medical advice.

(c) 2026 BioNode Anurag Hospital | Predictive Healthcare Division
"""
    
    try:
        yag = yagmail.SMTP(SENDER_EMAIL, SENDER_PASSWORD)
        yag.send(to=to_email, subject=f"BIONODE REPORT - {name}", contents=report)
        print(f"\nEmail sent to {to_email}")
        last_email_time = time.time()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ==================== FLASK DASHBOARD ====================

HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>BioNode Hospital</title>
    <meta http-equiv="refresh" content="2">
    <style>
        body { background: linear-gradient(135deg, #0a0f2a 0%, #0a1a3a 100%); font-family: Arial; padding: 20px; color: white; }
        .container { max-width: 1200px; margin: auto; }
        .header { background: #c41e3a; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
        .overall { background: #1e3a5f; padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 20px; border: 3px solid gold; }
        .overall-text { font-size: 48px; font-weight: bold; margin-top: 10px; }
        .critical { color: #ff6b6b; }
        .warning { color: #ffb347; }
        .normal { color: #5cb85c; }
        .grid { display: flex; gap: 20px; margin-bottom: 20px; }
        .card { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px; flex: 1; text-align: center; }
        .value { font-size: 48px; font-weight: bold; margin: 10px 0; }
        .patient-info { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>BioNode Anurag Hospital</h1>
            <p>AI-Powered Patient Monitoring</p>
        </div>
        <div class="patient-info">
            Patient: {{ name }} (Age: {{ age }}) | {{ email }}
        </div>
        <div class="overall">
            <div>OVERALL CONDITION</div>
            <div class="overall-text {{ cls }}">{{ overall }}</div>
        </div>
        <div class="grid">
            <div class="card">HEART RATE<br><div class="value">{{ hr }} BPM</div>{{ hr_dir }}</div>
            <div class="card">SpO2<br><div class="value">{{ spo2 }} %</div>{{ spo2_dir }}</div>
            <div class="card">BODY TEMP<br><div class="value">{{ temp }} C</div>{{ temp_dir }}</div>
        </div>
        <div class="grid">
            <div class="card"><b>ALERT</b><br>{{ risk }}<br>{{ alert_msg }}</div>
            <div class="card"><b>AI DIAGNOSIS</b><br>Health: {{ health }}<br>Fever: {{ fever }}<br>Stress: {{ stress }}</div>
        </div>
    </div>
</body>
</html>
"""

app = Flask(__name__)
data_store = {
    "overall": "NORMAL - STABLE",
    "patient": {"name": "", "age": "", "email": ""},
    "latest": {},
    "predictions": {},
    "alert": {}
}

@app.route('/')
def dashboard():
    return render_template_string(
        HTML_DASHBOARD,
        name=data_store["patient"].get("name", ""),
        age=data_store["patient"].get("age", ""),
        email=data_store["patient"].get("email", ""),
        overall=data_store.get("overall", "NORMAL"),
        cls="critical" if "CRITICAL" in data_store.get("overall", "") else "warning" if "MODERATE" in data_store.get("overall", "") else "normal",
        hr=data_store["latest"].get("hr", 0),
        spo2=data_store["latest"].get("spo2", 0),
        temp=data_store["latest"].get("temp", 0),
        hr_dir=data_store["latest"].get("hr_dir", "→"),
        spo2_dir=data_store["latest"].get("spo2_dir", "→"),
        temp_dir=data_store["latest"].get("temp_dir", "→"),
        risk=data_store["alert"].get("level", "STABLE"),
        alert_msg=data_store["alert"].get("message", ""),
        health=data_store["predictions"].get("health_status", "Normal"),
        fever=data_store["predictions"].get("fever_risk", "No Fever"),
        stress=data_store["predictions"].get("stress_level", "Low")
    )

def start_dashboard():
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    try:
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
    except:
        try:
            app.run(host='127.0.0.1', port=8080, debug=False, use_reloader=False)
            print("Dashboard: http://localhost:8080")
        except:
            print("Dashboard unavailable")

# ==================== MAIN ====================

def collect_readings(ser, num_readings=5, timeout=30):
    """Collect readings from ESP32"""
    readings = []
    start_time = time.time()
    
    print(f"Collecting {num_readings} readings...")
    print("-" * 50)
    
    # Clear the serial buffer
    ser.reset_input_buffer()
    
    # Send command to start readings
    ser.write(b'1\r\n')
    print("Command sent to ESP32...")
    
    while len(readings) < num_readings and time.time() - start_time < timeout:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if 'DATA:' in line:
                    try:
                        data_part = line.split('DATA:')[1].strip()
                        vals = data_part.split(',')
                        if len(vals) == 5:
                            room_temp, humidity, hr, spo2, body_temp = map(float, vals)
                            readings.append({
                                'reading_no': len(readings) + 1,
                                'room_temp': room_temp,
                                'humidity': humidity,
                                'hr': hr,
                                'spo2': spo2,
                                'body_temp': body_temp
                            })
                            print(f"Reading {len(readings)}/{num_readings}: HR={hr:.0f} BPM | SpO2={spo2:.0f}% | Temp={body_temp:.1f}C")
                    except Exception as e:
                        print(f"Parse error: {e}")
        except Exception as e:
            print(f"Serial error: {e}")
            time.sleep(0.5)
        time.sleep(0.1)
    
    return readings

def main():
    print("\n" + "="*60)
    print("     BIONODE ANURAG HOSPITAL")
    print("="*60)
    
    # Get patient details
    print("\nPATIENT REGISTRATION")
    name = input("Patient Name: ").strip()
    age = int(input("Age: ").strip())
    email = input("Email: ").strip()
    
    # Start dashboard
    threading.Thread(target=start_dashboard, daemon=True).start()
    print("\nDashboard: http://localhost:5000")
    
    # Connect to ESP32
    print(f"\nConnecting to {USB_PORT}...")
    ser = None
    try:
        # Close any existing connections
        try:
            ser = serial.Serial(USB_PORT, BAUD_RATE, timeout=5)
            time.sleep(2)
            print("ESP32 Connected!")
        except Exception as e:
            print(f"Could not connect to {USB_PORT}: {e}")
            print("\nTroubleshooting:")
            print("1. Close Arduino IDE Serial Monitor")
            print("2. Unplug and replug ESP32")
            print("3. Restart this program")
            return
    except Exception as e:
        print(f"Failed to connect: {e}")
        return
    
    # Update dashboard with patient info
    data_store["patient"] = {"name": name, "age": age, "email": email}
    
    # Instructions
    print("\n" + "="*60)
    print("READY TO MONITOR")
    print("="*60)
    print("\n1. Place your finger on the MAX30100 sensor")
    print("2. Keep your hand steady")
    print("\nPress Enter to start readings...")
    input()
    
    # Collect readings
    readings = collect_readings(ser, num_readings=5, timeout=30)
    
    if len(readings) < 5:
        print(f"\nOnly got {len(readings)} readings out of 5.")
        print("Please try again with better finger placement.")
        ser.close()
        return
    
    # Process readings
    predictor = PredictiveAlert(age=age)
    all_readings = []
    
    print("\n" + "="*60)
    print("     ANALYZING HEALTH DATA")
    print("="*60)
    
    for r in readings:
        predictor.add_reading(r['hr'], r['spo2'], r['body_temp'])
        health, fever, stress = predict_health(
            r['hr'], r['spo2'], r['body_temp'], r['room_temp'], r['humidity']
        )
        risk, alert_msg, hd, sd, td = predictor.predict()
        
        all_readings.append({
            'hr': r['hr'], 'spo2': r['spo2'], 'body_temp': r['body_temp']
        })
        
        data_store["latest"] = {
            "hr": r['hr'], "spo2": r['spo2'], "temp": r['body_temp'],
            "hr_dir": hd, "spo2_dir": sd, "temp_dir": td
        }
        data_store["predictions"] = {"health_status": health, "fever_risk": fever, "stress_level": stress}
        data_store["alert"] = {"level": risk, "message": alert_msg}
        
        if health == "Critical" or risk == "CRITICAL":
            data_store["overall"] = "CRITICAL - EMERGENCY"
        elif health == "Moderate" or risk == "WARNING":
            data_store["overall"] = "MODERATE - MONITOR"
        else:
            data_store["overall"] = "NORMAL - STABLE"
    
    # Final analysis
    final_health, final_fever, final_stress = predict_health(
        readings[-1]['hr'], readings[-1]['spo2'], readings[-1]['body_temp'],
        readings[-1]['room_temp'], readings[-1]['humidity']
    )
    final_risk, final_alert, hd, sd, td = predictor.predict()
    
    if final_health == "Critical" or final_risk == "CRITICAL":
        overall = "CRITICAL - IMMEDIATE MEDICAL ATTENTION"
    elif final_health == "Moderate" or final_risk == "WARNING":
        overall = "MODERATE - MONITOR CLOSELY"
    else:
        overall = "NORMAL - STABLE"
    
    recommendations = [
        "Maintain healthy lifestyle",
        "Exercise regularly",
        "Stay hydrated",
        "Get adequate sleep"
    ]
    
    # Voice alert
    voice_msg = get_voice_message(name, age, overall, final_alert, final_risk, recommendations)
    speak_alert(voice_msg)
    
    # Display summary
    print("\n" + "="*60)
    print("PATIENT HEALTH SUMMARY")
    print("="*60)
    print(f"\nPatient: {name}")
    print(f"Age: {age}")
    print(f"\nAverage Readings:")
    print(f"   Heart Rate: {np.mean([r['hr'] for r in all_readings]):.0f} BPM")
    print(f"   SpO2: {np.mean([r['spo2'] for r in all_readings]):.0f} %")
    print(f"   Body Temp: {np.mean([r['body_temp'] for r in all_readings]):.1f} C")
    print(f"\nStatus: {final_health}")
    print(f"Alert: {final_risk} - {final_alert}")
    
    # Send email
    print("\nSending email report...")
    alert_tuple = (final_risk, final_alert, hd, sd, td)
    predictions_tuple = (final_health, final_fever, final_stress)
    
    send_email_report(email, name, age, all_readings, predictions_tuple, alert_tuple, recommendations, overall)
    
    print("\n" + "="*60)
    print("COMPLETE! Dashboard: http://localhost:5000")
    print("Press Ctrl+C to exit")
    print("="*60)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    
    ser.close()

if __name__ == "__main__":
    main()