"""
Step 3: Train ML Model for Triple Prediction
Predicts: Health Status, Fever Risk, Stress Level
"""

import pandas as pd
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder

print("="*50)
print("TRAINING ML MODEL")
print("="*50)

# ==================== Load Data ====================

print("\n📂 Loading labeled data...")
df = pd.read_csv('health_data_labeled.csv')
print(f"Loaded {len(df)} records")

# ==================== Prepare Features ====================

features = ['HeartRate', 'SpO2', 'BodyTemp', 'RoomTemp', 'Humidity']
X = df[features]

# ==================== Prepare Targets ====================

y_status = df['HealthStatus']
y_fever = df['FeverRisk']
y_stress = df['StressLevel']

# Encode labels to numbers
le_status = LabelEncoder()
le_fever = LabelEncoder()
le_stress = LabelEncoder()

y_status_encoded = le_status.fit_transform(y_status)
y_fever_encoded = le_fever.fit_transform(y_fever)
y_stress_encoded = le_stress.fit_transform(y_stress)

print(f"\n📊 Classes:")
print(f"   Health Status: {list(le_status.classes_)}")
print(f"   Fever Risk: {list(le_fever.classes_)}")
print(f"   Stress Level: {list(le_stress.classes_)}")

# Combine targets into a single array for multi-output
y_combined = np.column_stack([y_status_encoded, y_fever_encoded, y_stress_encoded])

# ==================== Split Data ====================

X_train, X_test, y_train, y_test = train_test_split(
    X, y_combined, test_size=0.2, random_state=42
)

print(f"\n📈 Training data: {len(X_train)} records")
print(f"📉 Test data: {len(X_test)} records")

# ==================== Train Model ====================

print("\n🤖 Training Random Forest model...")

# Train separate Random Forest for each target
model_status = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
model_fever = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
model_stress = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)

model_status.fit(X_train, y_train[:, 0])
model_fever.fit(X_train, y_train[:, 1])
model_stress.fit(X_train, y_train[:, 2])

print("✅ Training complete!")

# ==================== Evaluate Model ====================

print("\n" + "="*50)
print("MODEL EVALUATION")
print("="*50)

y_status_pred = model_status.predict(X_test)
y_fever_pred = model_fever.predict(X_test)
y_stress_pred = model_stress.predict(X_test)

print(f"\n🎯 Health Status Accuracy: {accuracy_score(y_test[:, 0], y_status_pred):.2%}")
print(f"🎯 Fever Risk Accuracy: {accuracy_score(y_test[:, 1], y_fever_pred):.2%}")
print(f"🎯 Stress Level Accuracy: {accuracy_score(y_test[:, 2], y_stress_pred):.2%}")

# ==================== Save Model ====================

print("\n💾 Saving model...")

# Save models
with open('model_status.pkl', 'wb') as f:
    pickle.dump(model_status, f)

with open('model_fever.pkl', 'wb') as f:
    pickle.dump(model_fever, f)

with open('model_stress.pkl', 'wb') as f:
    pickle.dump(model_stress, f)

# Save label encoders
with open('label_encoders.pkl', 'wb') as f:
    pickle.dump([le_status, le_fever, le_stress], f)

print("✅ Models saved to: model_status.pkl, model_fever.pkl, model_stress.pkl")
print("✅ Label encoders saved to: label_encoders.pkl")

# ==================== Test Prediction ====================

print("\n" + "="*50)
print("TEST PREDICTION ON SAMPLE DATA")
print("="*50)

def predict_sample(hr, spo2, body_temp, room_temp, humidity):
    input_data = [[hr, spo2, body_temp, room_temp, humidity]]
    status_encoded = model_status.predict(input_data)[0]
    fever_encoded = model_fever.predict(input_data)[0]
    stress_encoded = model_stress.predict(input_data)[0]
    
    status = le_status.inverse_transform([status_encoded])[0]
    fever = le_fever.inverse_transform([fever_encoded])[0]
    stress = le_stress.inverse_transform([stress_encoded])[0]
    return status, fever, stress

print("\n🟢 Normal Sample (HR:75, SpO2:98, Body:36.8, Room:25, Hum:55):")
status, fever, stress = predict_sample(75, 98, 36.8, 25, 55)
print(f"   Health Status: {status}")
print(f"   Fever Risk: {fever}")
print(f"   Stress Level: {stress}")

print("\n🔴 Critical Sample (HR:140, SpO2:82, Body:39.5, Room:28, Hum:45):")
status, fever, stress = predict_sample(140, 82, 39.5, 28, 45)
print(f"   Health Status: {status}")
print(f"   Fever Risk: {fever}")
print(f"   Stress Level: {stress}")

print("\n✅ All done! Model is ready for real hardware data.")