"""
BIONODE ANURAG HOSPITAL - AI Health Monitoring System
Predictive Healthcare | IoT + AI | Voice Alerts (English + Telugu) | Hospital-Grade Reports
"""

import pickle
import numpy as np
import serial
import time
import os
import threading
from datetime import datetime
import yagmail
from flask import Flask, render_template_string, jsonify
import pyttsx3
import warnings
warnings.filterwarnings('ignore')

# ==================== CONFIGURATION ====================

USB_PORT = "COM3"  # CHANGE TO YOUR PORT (COM4, COM5, etc.)
BAUD_RATE = 115200
EMAIL_COOLDOWN_SECONDS = 300
VOICE_COOLDOWN = 15
last_email_time = 0
last_voice_time = 0

# ==================== EMAIL CONFIGURATION ====================
# Your college email credentials (already working)
SENDER_EMAIL = "23c11a0536@anurag.ac.in"
SENDER_PASSWORD = "idpb lezl ytcn xtdi"  # ⚠️ REPLACE WITH YOUR APP PASSWORD

# Hospital Branding
HOSPITAL_NAME = "🏥 BioNode Anurag Hospital"
HOSPITAL_TAGLINE = "Predictive Healthcare | AI-Powered | Smart Monitoring"
HOSPITAL_LOGO = "⚕️ BNAH"
EMERGENCY_NUMBER = "108 / 102"
HOSPITAL_HELPLINE = "1800-XXX-XXXX"

# ==================== VOICE SYSTEM ====================

voice_engine = None

def init_voice():
    global voice_engine
    try:
        voice_engine = pyttsx3.init()
        voice_engine.setProperty('rate', 150)
        voice_engine.setProperty('volume', 0.95)
        voices = voice_engine.getProperty('voices')
        for voice in voices:
            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                voice_engine.setProperty('voice', voice.id)
                break
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
        print("\a")
        def speak_thread():
            voice_engine.say(message)
            voice_engine.runAndWait()
        threading.Thread(target=speak_thread, daemon=True).start()
        print(f"🔊 VOICE: {message}")
    except:
        pass

def speak_telugu(message):
    print(f"🔊 TELUGU: {message}")

def get_voice_message_en(name, age, overall, alert_msg, risk_level, recs):
    if risk_level == "CRITICAL":
        return (f"Attention. BioNode Anurag Hospital. Patient {name}, age {age}. "
                f"Overall condition CRITICAL. {alert_msg}. {recs[0] if recs else 'Seek emergency care'}.")
    elif risk_level == "WARNING":
        return (f"Attention. Patient {name}. Condition MODERATE. {alert_msg}. "
                f"{recs[0] if recs else 'Rest and monitor'}.")
    else:
        return (f"BioNode Anurag Hospital report for {name}. Condition NORMAL. "
                f"Continue healthy lifestyle.")

def get_voice_message_te(name, age, overall, risk_level):
    if risk_level == "CRITICAL":
        return (f"బయోనోడ్ అనురాగ్ హాస్పిటల్. రోగి {name}, వయసు {age}. "
                f"పరిస్థితి క్లిష్టమైనది. వెంటనే వైద్య సహాయం తీసుకోండి.")
    elif risk_level == "WARNING":
        return (f"రోగి {name}. పరిస్థితి మధ్యస్థం. దయచేసి విశ్రాంతి తీసుకోండి.")
    else:
        return (f"రోగి {name}. పరిస్థితి సాధారణం. ఆరోగ్యకరమైన జీవనశైలి కొనసాగించండి.")

# ==================== LOAD ML MODELS ====================

print("Loading AI Models...")
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
    print("✅ AI Models Loaded")
except:
    print("⚠️ Fallback Mode Active")
    models_loaded = False

def fallback_predict(hr, spo2, body_temp):
    if (60 <= hr <= 100) and (spo2 >= 95) and (36.1 <= body_temp <= 37.2):
        health = "Normal"
    elif (hr > 120 or hr < 50) or (spo2 < 90) or (body_temp > 38.5 or body_temp < 35):
        health = "Critical"
    else:
        health = "Moderate"
    if body_temp < 37.3:
        fever = "No Fever"
    elif body_temp <= 38.5:
        fever = "Low Fever"
    else:
        fever = "High Fever"
    if hr <= 90 and spo2 >= 96:
        stress = "Low Stress"
    elif hr <= 115 and spo2 >= 92:
        stress = "Moderate Stress"
    else:
        stress = "High Stress"
    return health, fever, stress

init_voice()
print("🔊 Voice System Ready\n")

# ==================== PREDICTIVE ALERT ====================

class PredictiveAlert:
    def __init__(self, age=30):
        self.history_hr, self.history_spo2, self.history_temp = [], [], []
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
            return 0, "→ STABLE"
        slope = np.polyfit(range(len(values)), values, 1)[0]
        if slope > 0.5:
            return slope, "↑ RISING"
        if slope < -0.5:
            return slope, "↓ FALLING"
        return slope, "→ STABLE"
    
    def predict(self):
        if len(self.history_hr) < 3:
            return "COLLECTING", "Collecting data...", "→", "→", "→"
        hr_s, hr_d = self.get_trend(self.history_hr)
        sp_s, sp_d = self.get_trend(self.history_spo2)
        tp_s, tp_d = self.get_trend(self.history_temp)
        curr_hr, curr_sp, curr_tp = self.history_hr[-1], self.history_spo2[-1], self.history_temp[-1]
        pred_hr = curr_hr + (hr_s * 3)
        pred_sp = curr_sp + (sp_s * 3)
        pred_tp = curr_tp + (tp_s * 3)
        alerts = []
        if pred_hr > self.critical_hr:
            alerts.append(f"HR predicted {pred_hr:.0f} BPM")
        elif pred_hr > self.warning_hr:
            alerts.append(f"HR may reach {pred_hr:.0f} BPM")
        if pred_sp < self.critical_spo2:
            alerts.append(f"SpO2 predicted {pred_sp:.0f}%")
        elif pred_sp < self.warning_spo2:
            alerts.append(f"SpO2 may drop to {pred_sp:.0f}%")
        if pred_tp > self.critical_temp:
            alerts.append(f"Temp predicted {pred_tp:.1f}°C")
        if len([a for a in alerts if "predicted" in a]) >= 2:
            return "CRITICAL", " | ".join(alerts[:2]), hr_d, sp_d, tp_d
        elif alerts:
            return "WARNING", alerts[0], hr_d, sp_d, tp_d
        return "STABLE", "All stable", hr_d, sp_d, tp_d

def get_overall_condition(health_status, risk_level):
    if health_status == "Critical" or risk_level == "CRITICAL":
        return "🔴 CRITICAL - IMMEDIATE MEDICAL ATTENTION"
    elif health_status == "Moderate" or risk_level == "WARNING":
        return "🟡 MODERATE - MONITOR CLOSELY"
    return "🟢 NORMAL - STABLE"

def get_recommendations(health_status, fever_risk, stress_level, risk_level, age):
    recs = []
    if health_status == "Critical" or risk_level == "CRITICAL":
        recs = ["🚨 SEEK IMMEDIATE MEDICAL ATTENTION", "📞 Call 108/102", "🛌 Lie down", "💧 Sip water"]
    elif health_status == "Moderate" or risk_level == "WARNING":
        recs = ["⚠️ Schedule Doctor Visit", "🛑 Rest", "💧 Stay Hydrated", "📊 Monitor Symptoms"]
    else:
        recs = ["✅ Maintain Healthy Lifestyle", "🏃 Light Exercise", "🥗 Balanced Diet", "💤 7-8 Hours Sleep"]
    if fever_risk == "High Fever":
        recs.append("🌡️ Take Paracetamol if prescribed | Cold compress")
    if stress_level == "High Stress":
        recs.append("🧘 Deep breathing (5-5-5 method)")
    if age > 60:
        recs.append("👴 Keep emergency contacts ready")
    if risk_level == "CRITICAL":
        recs.insert(0, "⏰ ACTION REQUIRED WITHIN 10-15 MINUTES")
    return recs[:6]

# ==================== EMAIL FUNCTION ====================

def send_hospital_report(to_email, name, age, data, predictions, risk_level, alert_msg, trends, recs, overall_condition, voice_en, voice_te):
    global last_email_time
    if time.time() - last_email_time < EMAIL_COOLDOWN_SECONDS and risk_level != "CRITICAL":
        return False
    
    hr, spo2, body_temp, room_temp, humidity = data
    health_status, fever_risk, stress_level = predictions
    hr_dir, sp_dir, tp_dir = trends
    patient_id = f"BNAH-{datetime.now().strftime('%Y%m%d')}-{name[:3].upper()}"
    
    recs_text = "\n".join([f"   {i+1}. {r}" for i, r in enumerate(recs)])
    
    report = f"""
╔══════════════════════════════════════════════════════════════════╗
║              🏥 {HOSPITAL_NAME} 🏥                              ║
║         {HOSPITAL_TAGLINE}                                       ║
╚══════════════════════════════════════════════════════════════════╝

                     OFFICIAL HEALTH REPORT
                     {name}
                     Report ID: {patient_id}
                     {datetime.now().strftime("%Y-%m-%d | %H:%M:%S")}

╔══════════════════════════════════════════════════════════════════╗
║              🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴              ║
║                 OVERALL HEALTH CONDITION                         ║
║                 {overall_condition}                              ║
║              🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴              ║
╚══════════════════════════════════════════════════════════════════╝

VITAL SIGNS
----------------------------------------------------
❤️ Heart Rate    : {hr:.0f} BPM    {hr_dir}
🫁 SpO2          : {spo2:.0f} %      {sp_dir}
🌡️ Body Temp     : {body_temp:.1f} °C    {tp_dir}
🏠 Room Temp     : {room_temp:.1f} °C
💧 Humidity      : {humidity:.0f} %

AI ANALYSIS
----------------------------------------------------
Health Status    : {health_status}
Fever Risk       : {fever_risk}
Stress Level     : {stress_level}

PREDICTIVE ALERT
----------------------------------------------------
Level            : {risk_level}
Prediction       : {alert_msg}
Trend            : HR {hr_dir} | SpO2 {sp_dir} | Temp {tp_dir}

RECOMMENDATIONS
----------------------------------------------------
{recs_text}

VOICE ALERTS
----------------------------------------------------
ENGLISH: "{voice_en}"
TELUGU : "{voice_te}"

AUTHORIZED BY
----------------------------------------------------
AI Medical Assistant System
BioNode Anurag Hospital
(This is an AI-generated report for monitoring purposes only)

© 2026 BioNode Anurag Hospital | Predictive Healthcare Division
Report ID: {patient_id}
"""
    
    try:
        yag = yagmail.SMTP(SENDER_EMAIL, SENDER_PASSWORD)
        yag.send(to=to_email, subject=f"🏥 BIONODE REPORT - {name}", contents=report)
        print(f"\n📧 REPORT SENT to {to_email}")
        last_email_time = time.time()
        return True
    except Exception as e:
        print(f"⚠️ Email error: {e}")
        return False

# ==================== DASHBOARD ====================

HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>BioNode Anurag Hospital</title>
    <meta http-equiv="refresh" content="2">
    <style>
        body { background: linear-gradient(135deg, #0a0f2a 0%, #0a1a3a 100%); font-family: Arial; padding: 20px; color: white; }
        .container { max-width: 1200px; margin: auto; }
        .header { background: #c41e3a; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
        .overall { background: #1e3a5f; padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 20px; border: 3px solid gold; }
        .overall-text { font-size: 48px; font-weight: bold; }
        .critical { color: #ff6b6b; }
        .warning { color: #ffb347; }
        .normal { color: #5cb85c; }
        .grid { display: flex; gap: 20px; margin-bottom: 20px; }
        .card { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px; flex: 1; text-align: center; }
        .value { font-size: 48px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header"><h1>🏥 BIONODE ANURAG HOSPITAL</h1><p>Predictive Healthcare | AI-Powered</p></div>
        <div class="overall"><div>OVERALL CONDITION</div><div class="overall-text {{ cls }}">{{ overall }}</div></div>
        <div class="grid">
            <div class="card">❤️ HEART RATE<br><span class="value">{{ hr }} BPM</span><br>{{ hr_dir }}</div>
            <div class="card">🫁 SpO2<br><span class="value">{{ spo2 }} %</span><br>{{ spo2_dir }}</div>
            <div class="card">🌡️ BODY TEMP<br><span class="value">{{ temp }} °C</span><br>{{ temp_dir }}</div>
        </div>
        <div class="grid">
            <div class="card"><b>🚨 ALERT</b><br>{{ risk }}<br>{{ alert_msg }}</div>
            <div class="card"><b>🤖 AI</b><br>Health: {{ health }}<br>Fever: {{ fever }}<br>Stress: {{ stress }}</div>
        </div>
    </div>
</body>
</html>
"""

app = Flask(__name__)
data_store = {"overall": "🟢 NORMAL - STABLE", "latest": {}, "predictions": {}, "alert": {}}

@app.route('/')
def dashboard():
    return render_template_string(HTML_DASHBOARD,
        overall=data_store.get("overall", "NORMAL"),
        cls="critical" if "CRITICAL" in data_store.get("overall", "") else "warning" if "MODERATE" in data_store.get("overall", "") else "normal",
        hr=data_store["latest"].get("hr", 0), spo2=data_store["latest"].get("spo2", 0), temp=data_store["latest"].get("temp", 0),
        hr_dir=data_store["latest"].get("hr_dir", "→"), spo2_dir=data_store["latest"].get("spo2_dir", "→"), temp_dir=data_store["latest"].get("temp_dir", "→"),
        risk=data_store["alert"].get("level", "STABLE"), alert_msg=data_store["alert"].get("message", ""),
        health=data_store["predictions"].get("health_status", "Normal"), fever=data_store["predictions"].get("fever_risk", "No Fever"),
        stress=data_store["predictions"].get("stress_level", "Low"))

def start_dashboard():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# ==================== MAIN ====================

print("\n" + "="*70)
print("     🏥 BIONODE ANURAG HOSPITAL - READY FOR DEMO")
print("="*70)

name = input("\n👤 Patient Name: ").strip()
age = int(input("🎂 Age: ").strip())
email = input("📧 Patient Email: ").strip()

os.makedirs('patients', exist_ok=True)
predictor = PredictiveAlert(age=age)
threading.Thread(target=start_dashboard, daemon=True).start()
print("\n🌐 Dashboard: http://localhost:5000")

print(f"\n🔌 Connecting to ESP32 on {USB_PORT}...")
try:
    ser = serial.Serial(USB_PORT, BAUD_RATE, timeout=2)
    time.sleep(2)
    hardware = True
    print("✅ ESP32 CONNECTED! Reading live data...\n")
except:
    hardware = False
    print("⚠️ Manual Demo Mode\n")

print("="*70)
print("📊 MONITORING ACTIVE | Press Ctrl+C to stop")
print("="*70 + "\n")

try:
    if hardware:
        while True:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if 'DATA:' in line:
                    vals = line.split('DATA:')[1].strip().split(',')
                    if len(vals) == 5:
                        room_temp, humidity, hr, spo2, body_temp = map(float, vals)
                        if predictor.add_reading(hr, spo2, body_temp):
                            risk, alert_msg, hd, sd, td = predictor.predict()
                            if models_loaded:
                                inp = np.array([[hr, spo2, body_temp, room_temp, humidity]])
                                health = le_status.inverse_transform(model_status.predict(inp))[0]
                                fever = le_fever.inverse_transform(model_fever.predict(inp))[0]
                                stress = le_stress.inverse_transform(model_stress.predict(inp))[0]
                            else:
                                health, fever, stress = fallback_predict(hr, spo2, body_temp)
                            overall = get_overall_condition(health, risk)
                            recs = get_recommendations(health, fever, stress, risk, age)
                            voice_en = get_voice_message_en(name, age, overall, alert_msg, risk, recs)
                            voice_te = get_voice_message_te(name, age, overall, risk)
                            data_store["latest"] = {"hr": hr, "spo2": spo2, "temp": body_temp, "hr_dir": hd, "spo2_dir": sd, "temp_dir": td}
                            data_store["predictions"] = {"health_status": health, "fever_risk": fever, "stress_level": stress}
                            data_store["alert"] = {"level": risk, "message": alert_msg}
                            data_store["overall"] = overall
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❤️ {hr:.0f} | 🫁 {spo2:.0f} | 🌡️ {body_temp:.1f}°C | {health} | {risk}")
                            if risk in ["CRITICAL", "WARNING"]:
                                send_hospital_report(email, name, age, (hr, spo2, body_temp, room_temp, humidity),
                                    (health, fever, stress), risk, alert_msg, (hd, sd, td), recs, overall, voice_en, voice_te)
                                speak_alert(voice_en)
                                speak_telugu(voice_te)
            time.sleep(0.5)
    else:
        print("MANUAL DEMO MODE - Enter readings:")
        print("Format: HR,SpO2,BodyTemp,RoomTemp,Humidity")
        print("Example: 75,98,36.8,25,55\n")
        while True:
            entry = input("Enter: ").strip()
            if entry.lower() == 'q':
                break
            try:
                hr, spo2, body_temp, room_temp, humidity = map(float, entry.split(','))
                if predictor.add_reading(hr, spo2, body_temp):
                    risk, alert_msg, hd, sd, td = predictor.predict()
                    if models_loaded:
                        inp = np.array([[hr, spo2, body_temp, room_temp, humidity]])
                        health = le_status.inverse_transform(model_status.predict(inp))[0]
                        fever = le_fever.inverse_transform(model_fever.predict(inp))[0]
                        stress = le_stress.inverse_transform(model_stress.predict(inp))[0]
                    else:
                        health, fever, stress = fallback_predict(hr, spo2, body_temp)
                    overall = get_overall_condition(health, risk)
                    recs = get_recommendations(health, fever, stress, risk, age)
                    voice_en = get_voice_message_en(name, age, overall, alert_msg, risk, recs)
                    voice_te = get_voice_message_te(name, age, overall, risk)
                    print(f"\n{'='*50}")
                    print(f"🏥 OVERALL: {overall}")
                    print(f"❤️ {hr:.0f} BPM | 🫁 {spo2:.0f}% | 🌡️ {body_temp:.1f}°C")
                    print(f"🚨 {risk}: {alert_msg}")
                    print(f"📈 Trend: HR {hd} | SpO2 {sd} | Temp {td}")
                    print(f"💊 Top Rec: {recs[0] if recs else 'Monitor'}")
                    print(f"🔊 EN: {voice_en[:80]}...")
                    print(f"🔊 TE: {voice_te}")
                    print(f"{'='*50}\n")
                    if risk in ["CRITICAL", "WARNING"]:
                        send_hospital_report(email, name, age, (hr, spo2, body_temp, room_temp, humidity),
                            (health, fever, stress), risk, alert_msg, (hd, sd, td), recs, overall, voice_en, voice_te)
                        speak_alert(voice_en)
                        speak_telugu(voice_te)
            except:
                print("Invalid. Use: 75,98,36.8,25,55")
except KeyboardInterrupt:
    print("\n\n📊 Demo Complete")

print("\n🏥 BioNode Anurag Hospital Ready!")
print("🌐 Dashboard: http://localhost:5000")