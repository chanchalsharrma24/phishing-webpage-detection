"""Phishing Classifier: enter a URL and get a phishing / safe prediction.

Run with:  streamlit run app.py
If models/phishing_rf.joblib exists (created by the notebook) it is loaded; otherwise the model is
trained from data/urls.csv when the app starts (takes a few seconds).
"""

import os

import joblib
import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestClassifier

from features import extract_features, features_from_urls

MODEL_PATH = "models/phishing_rf.joblib"


@st.cache_resource
def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    data = pd.read_csv("data/urls.csv")
    model = RandomForestClassifier(n_estimators=300, min_samples_leaf=2, n_jobs=-1, random_state=42)
    model.fit(features_from_urls(data["url"]), data["status"].eq("phishing").astype(int))
    return model


st.set_page_config(page_title="Phishing Classifier", page_icon="🔐")
st.title("🔐 Phishing Classifier (Scikit-learn)")
st.write("Checks a URL using only its text, with a Random Forest model trained on 11,429 labelled URLs.")

model = load_model()
url = st.text_input("Enter a URL to classify:", placeholder="e.g. http://amaz0n-update.info")

if st.button("Predict") and url.strip():
    features = pd.DataFrame([extract_features(url)])
    probability = model.predict_proba(features)[0, 1]

    if probability >= 0.5:
        st.error(f"⚠️ This URL is likely **phishing** (phishing probability: {probability:.0%}).")
    else:
        st.success(f"✅ This URL appears to be **safe** (phishing probability: {probability:.0%}).")

    with st.expander("See the features the model used"):
        st.dataframe(features.T.rename(columns={0: "value"}))

st.caption("This is a learning project. Always be careful with links in unexpected emails or messages.")
