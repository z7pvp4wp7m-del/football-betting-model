import streamlit as st
import pandas as pd
import pickle
import os
from src.features import calculate_features

# Page Config
st.set_page_config(page_title="Football Predictor", page_icon="⚽", layout="centered")

# Load Model
def load_model():
    if os.path.exists('models/xgb_model.pkl'):
        with open('models/xgb_model.pkl', 'rb') as f:
            return pickle.load(f)
    return None

model = load_model()

# Load Data
def load_data():
    if os.path.exists('data/merged_data.csv'):
        return pd.read_csv('data/merged_data.csv')
    return None

df = load_data()

# Header
st.title("⚽ Premier League Match Predictor")
st.markdown("Predict match outcomes using **xG (Expected Goals)** and historical form.")

if model is None or df is None:
    st.warning("⚠️ Model or Data not found.")
    st.info("This is expected on a new deployment. Click below to download data and train the model.")
    
    if st.button("Train Model Now", type="primary"):
        with st.spinner("Downloading data and training model... (This takes ~1 minute)"):
            try:
                # Import pipeline components
                from src.data_loader import merge_data
                from src.features import calculate_features
                from src.model import train_model
                
                # Ensure directories exist
                os.makedirs('data', exist_ok=True)
                os.makedirs('models', exist_ok=True)
                
                # Run Pipeline
                st.write("Step 1/3: Downloading & Merging Data...")
                merge_data()
                df = pd.read_csv('data/merged_data.csv')
                
                st.write("Step 2/3: Engineering Features...")
                df_processed = calculate_features(df)
                
                st.write("Step 3/3: Training Model...")
                train_model(df_processed)
                
                st.success("Done! Refreshing...")
                st.rerun()
            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.write("Debug info:", os.getcwd(), os.listdir('.'))
    st.stop()

# Team Selection
teams = sorted(df['HomeTeam'].unique())
col1, col2 = st.columns(2)
with col1:
    home_team = st.selectbox("Home Team", teams, index=0)
with col2:
    away_team = st.selectbox("Away Team", teams, index=1)

if home_team == away_team:
    st.warning("Please select different teams.")
    st.stop()

# Prediction Logic
if st.button("Predict Outcome", type="primary"):
    # Create dummy row for prediction
    dummy_row = {
        'Date': pd.Timestamp.now().strftime('%Y-%m-%d'),
        'HomeTeam': home_team,
        'AwayTeam': away_team,
        'FTHG': 0, 'FTAG': 0, 'FTR': 'D', 
        'B365H': 2.0, 'B365D': 3.0, 'B365A': 4.0, # Dummy odds
        'Home_xG': 1.3, 'Away_xG': 1.1, # Dummy xG
        'Season': '2324'
    }
    
    # Append to df to calculate features
    df_with_dummy = pd.concat([df, pd.DataFrame([dummy_row])], ignore_index=True)
    
    # Recalculate features (using the same logic as training)
    # Note: In a real app, we'd optimize this to not re-calc everything
    with st.spinner("Calculating recent form..."):
        df_processed = calculate_features(df_with_dummy)
    
    # Get the last row
    match_features = df_processed.iloc[[-1]]
    
    # Features required
    features = [
        'Home_Form_Points', 'Home_Form_GS', 'Home_Form_GC', 
        'Away_Form_Points', 'Away_Form_GS', 'Away_Form_GC',
        'Home_Form_xG', 'Home_Form_xGA', 'Home_Form_xG_Diff', 'Home_Form_xGA_Diff',
        'Away_Form_xG', 'Away_Form_xGA', 'Away_Form_xG_Diff', 'Away_Form_xGA_Diff',
        'B365H', 'B365D', 'B365A'
    ]
    
    X = match_features[features]
    
    # Predict
    probs = model.predict_proba(X)[0]
    prediction = model.predict(X)[0]
    
    # Display Results
    st.divider()
    
    # Winner
    outcomes = ['Home Win', 'Draw', 'Away Win']
    winner = outcomes[prediction]
    
    if prediction == 0:
        st.success(f"**Prediction: {home_team} Win**")
    elif prediction == 2:
        st.success(f"**Prediction: {away_team} Win**")
    else:
        st.info(f"**Prediction: Draw**")
        
    # Probabilities
    col1, col2, col3 = st.columns(3)
    col1.metric(f"{home_team}", f"{probs[0]:.1%}")
    col2.metric("Draw", f"{probs[1]:.1%}")
    col3.metric(f"{away_team}", f"{probs[2]:.1%}")
    
    # Stats Comparison
    st.subheader("Form Comparison (Last 5 Games)")
    
    stats_df = pd.DataFrame({
        'Metric': ['Points', 'Goals Scored', 'Goals Conceded', 'xG For', 'xG Against'],
        f'{home_team}': [
            match_features['Home_Form_Points'].values[0],
            match_features['Home_Form_GS'].values[0],
            match_features['Home_Form_GC'].values[0],
            match_features['Home_Form_xG'].values[0],
            match_features['Home_Form_xGA'].values[0]
        ],
        f'{away_team}': [
            match_features['Away_Form_Points'].values[0],
            match_features['Away_Form_GS'].values[0],
            match_features['Away_Form_GC'].values[0],
            match_features['Away_Form_xG'].values[0],
            match_features['Away_Form_xGA'].values[0]
        ]
    })
    st.table(stats_df.set_index('Metric'))

