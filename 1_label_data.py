"""
Step 2: Add Labels to Data
Adds: Health Status, Fever Risk, Stress Level
"""

import pandas as pd

print("Loading data...")
df = pd.read_csv('health_data.csv')
print(f"Loaded {len(df)} records")

# ==================== Labeling Functions ====================

def get_health_status(row):
    """Classify overall health status"""
    hr = row['HeartRate']
    spo2 = row['SpO2']
    body_temp = row['BodyTemp']
    
    # Normal
    if (60 <= hr <= 100) and (spo2 >= 95) and (36.1 <= body_temp <= 37.2):
        return 'Normal'
    
    # Critical
    elif (hr > 130 or hr < 50) or (spo2 < 85) or (body_temp > 39.0 or body_temp < 35.0):
        return 'Critical'
    
    # Moderate
    else:
        return 'Moderate'

def get_fever_risk(row):
    """Classify fever risk based on body temperature"""
    temp = row['BodyTemp']
    
    if temp < 37.3:
        return 'No Fever'
    elif 37.3 <= temp <= 38.5:
        return 'Low Fever'
    else:
        return 'High Fever'

def get_stress_level(row):
    """Classify stress level based on heart rate, SpO2, and room temp"""
    hr = row['HeartRate']
    spo2 = row['SpO2']
    room_temp = row['RoomTemp']
    
    if hr <= 90 and spo2 >= 96 and room_temp <= 28:
        return 'Low Stress'
    elif (90 < hr <= 115 or 90 <= spo2 < 95) and room_temp <= 32:
        return 'Moderate Stress'
    else:
        return 'High Stress'

# ==================== Apply Labels ====================

print("\nApplying labels...")

df['HealthStatus'] = df.apply(get_health_status, axis=1)
df['FeverRisk'] = df.apply(get_fever_risk, axis=1)
df['StressLevel'] = df.apply(get_stress_level, axis=1)

# ==================== Show Distribution ====================

print("\n" + "="*50)
print("LABEL DISTRIBUTION")
print("="*50)

print("\n📊 Health Status:")
print(df['HealthStatus'].value_counts())

print("\n🌡️ Fever Risk:")
print(df['FeverRisk'].value_counts())

print("\n😰 Stress Level:")
print(df['StressLevel'].value_counts())

# ==================== Save Labeled Data ====================

df.to_csv('health_data_labeled.csv', index=False)
print("\n✅ Labeled data saved to: health_data_labeled.csv")
print(f"   Total records: {len(df)}")