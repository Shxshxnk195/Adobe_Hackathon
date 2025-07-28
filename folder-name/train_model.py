import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib

df = pd.read_csv("training_data.csv")

X = df[["font_size", "is_bold", "is_caps", "y_pos", "text_length", "page"]]
le = LabelEncoder()
y = le.fit_transform(df["label"])

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

joblib.dump(model, "heading_classifier.pkl")
joblib.dump(le, "label_encoder.pkl")
print("✅ Model and label encoder saved")
