"""
Create dummy data to test ML pipeline
Generates realistic sensor data with normal and abnormal cases
"""

import pandas as pd
import random

print("Creating dummy health data...")

data = []

for i in range(200):  # 200 samples
    # Decide if normal or abnormal (first 100 normal, next 100 mixed)
    if i < 100:
        # Normal readings
        hr = random.randint(65, 95)
        spo2 = random.randint(96, 99)
        body_temp = round(random.uniform(36.3, 37.0), 1)
        room_temp = round(random.uniform(22, 28), 1)
        humidity = random.randint(45, 65)
    else:
        # Mixed abnormal cases (simulate different conditions)
        condition = random.choice(['fever', 'stress', 'critical', 'moderate'])
        
        if condition == 'fever':
            hr = random.randint(100, 125)
            spo2 = random.randint(92, 97)
            body_temp = round(random.uniform(38.0, 39.5), 1)
            room_temp = round(random.uniform(23, 27), 1)
            humidity = random.randint(45, 65)
            
        elif condition == 'stress':
            hr = random.randint(110, 130)
            spo2 = random.randint(90, 96)
            body_temp = round(random.uniform(36.8, 37.5), 1)
            room_temp = round(random.uniform(28, 35), 1)
            humidity = random.randint(40, 55)
            
        elif condition == 'critical':
            hr = random.randint(130, 150)
            spo2 = random.randint(80, 89)
            body_temp = round(random.uniform(39.0, 40.5), 1)
            room_temp = round(random.uniform(25, 30), 1)
            humidity = random.randint(35, 50)
            
        else:  # moderate
            hr = random.randint(100, 115)
            spo2 = random.randint(92, 95)
            body_temp = round(random.uniform(37.3, 38.0), 1)
            room_temp = round(random.uniform(24, 29), 1)
            humidity = random.randint(40, 60)
    
    data.append([hr, spo2, body_temp, room_temp, humidity])

# Create DataFrame
df = pd.DataFrame(data, columns=['HeartRate', 'SpO2', 'BodyTemp', 'RoomTemp', 'Humidity'])

# Save to CSV
df.to_csv('health_data.csv', index=False)

print(f"\n✅ Created dummy data with {len(df)} records")
print("\nSample data:")
print(df.head(10))