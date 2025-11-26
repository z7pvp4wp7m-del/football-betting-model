import streamlit as st
import pandas as pd
import pickle
import os
import time
from src.features import calculate_features

# Page Config
st.set_page_config(page_title="Football Predictor", page_icon="⚽", layout="centered")

# Header
st.title("⚽ Match Predictor")

# League Selector
league_map = {'Premier League (EPL)': 'E0', 'Belgian Pro League': 'B1'}
selected_league_name = st.selectbox("Select League", list(league_map.keys()))
league_code = league_map[selected_league_name]

st.markdown(f"Predicting **{selected_league_name}** matches.")
if league_code == 'B1':
    st.caption("Note: Belgian predictions use Basic Model (Form & Odds only) as xG data is unavailable.")
else:
    st.caption("Using Advanced Model with xG (Expected Goals).")

# Handle Retraining
if st.session_state.get('retrain_needed'):
    with st.status("Retraining model...", expanded=True) as status:
        st.write("DEBUG: Starting retraining process...")
        try:
            st.write("Importing modules...")
            from src.data_loader import merge_data
            from src.features import calculate_features
            from src.model import train_model
            
            st.write("Downloading and merging data...")
            # Force data reload
            understat_league = 'EPL' if league_code == 'E0' else None
            merge_data(league_code, understat_league)
            
            st.write("Loading new data...")
            df = pd.read_csv(f'data/merged_{league_code}.csv')
            
            st.write("Calculating features...")
            df_processed = calculate_features(df)
            
            st.write("Training model...")
            train_model(df_processed, league_code)
            
            status.update(label="Model retrained successfully!", state="complete", expanded=False)
            st.success("Done! Reloading app...")
            st.session_state['retrain_needed'] = False
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Error during retraining: {e}")
            status.update(label="Retraining failed", state="error")
            st.session_state['retrain_needed'] = False
            st.stop()

# Load Model
def load_model(code):
    path = f'models/model_{code}.pkl'
    # Fallback for old model name if upgrading
    if not os.path.exists(path) and code == 'E0' and os.path.exists('models/xgb_model.pkl'):
        path = 'models/xgb_model.pkl'
        
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return pickle.load(f)
    return None

model = load_model(league_code)

# Load Data
def load_data(code):
    path = f'data/merged_{code}.csv'
    # Fallback
    if not os.path.exists(path) and code == 'E0' and os.path.exists('data/merged_data.csv'):
        path = 'data/merged_data.csv'
        
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

df = load_data(league_code)

if model is None or df is None:
    st.warning(f"⚠️ Model or Data for {selected_league_name} not found.")
    
    if st.button(f"Train {selected_league_name} Model Now", type="primary"):
        with st.spinner("Downloading data and training model..."):
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
                understat_league = 'EPL' if league_code == 'E0' else None
                merge_data(league_code, understat_league)
                df = pd.read_csv(f'data/merged_{league_code}.csv')
                
                st.write("Step 2/3: Engineering Features...")
                df_processed = calculate_features(df)
                
                st.write("Step 3/3: Training Model...")
                train_model(df_processed, league_code)
                
                st.success("Done! Refreshing...")
                st.rerun()
            except Exception as e:
                st.error(f"An error occurred: {e}")
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
        'Season': '2324'
    }
    
    # Add dummy xG if needed (only if we plan to use it)
    # We will let calculate_features handle it, but we need to know if the model expects it.
    # For now, we provide it for EPL, but we will filter features later based on the model.
    if league_code == 'E0':
        dummy_row['Home_xG'] = 1.3
        dummy_row['Away_xG'] = 1.1
    
    # Append to df to calculate features
    df_with_dummy = pd.concat([df, pd.DataFrame([dummy_row])], ignore_index=True)
    
    # Recalculate features
    with st.spinner("Calculating recent form..."):
        df_processed = calculate_features(df_with_dummy)
    
    # Get the last row
    match_features = df_processed.iloc[[-1]]
    
    # Features required (Must match training)
    base_features = [
        'Home_Form_Points', 'Home_Form_GS', 'Home_Form_GC', 
        'Away_Form_Points', 'Away_Form_GS', 'Away_Form_GC',
        'B365H', 'B365D', 'B365A'
    ]
    xg_features = [
        'Home_Form_xG', 'Home_Form_xGA', 'Home_Form_xG_Diff', 'Home_Form_xGA_Diff',
        'Away_Form_xG', 'Away_Form_xGA', 'Away_Form_xG_Diff', 'Away_Form_xGA_Diff'
    ]
    
    features = base_features.copy()
    
    # Check if model expects xG features
    # Base features = 9. With xG = 17.
    if hasattr(model, 'n_features_in_') and model.n_features_in_ > 9:
        if 'Home_Form_xG' in match_features.columns:
            features.extend(xg_features)
        else:
            st.error("⚠️ Model expects xG features but data is missing them.")
            st.info("This happens when the data source changes. Please retrain the model to fix it.")
            def start_retraining():
                st.session_state['retrain_needed'] = True
                
            st.button("Retrain Model to Fix", type="primary", on_click=start_retraining)
            st.stop()
            

            
    X = match_features[features]
    
    # Predict
    probs = model.predict_proba(X)[0]
    prediction = model.predict(X)[0]
    
    # Display Results
    st.divider()
    
    # Winner
    outcomes = ['Home Win', 'Draw', 'Away Win']
    
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
    
    metrics = ['Points', 'Goals Scored', 'Goals Conceded']
    home_vals = [
        match_features['Home_Form_Points'].values[0],
        match_features['Home_Form_GS'].values[0],
        match_features['Home_Form_GC'].values[0]
    ]
    away_vals = [
        match_features['Away_Form_Points'].values[0],
        match_features['Away_Form_GS'].values[0],
        match_features['Away_Form_GC'].values[0]
    ]
    
    if 'Home_Form_xG' in match_features.columns:
        metrics.extend(['xG For', 'xG Against'])
        home_vals.extend([
            match_features['Home_Form_xG'].values[0],
            match_features['Home_Form_xGA'].values[0]
        ])
        away_vals.extend([
            match_features['Away_Form_xG'].values[0],
            match_features['Away_Form_xGA'].values[0]
        ])
    
    stats_df = pd.DataFrame({
        'Metric': metrics,
        f'{home_team}': home_vals,
        f'{away_team}': away_vals
    })
    st.table(stats_df.set_index('Metric'))
