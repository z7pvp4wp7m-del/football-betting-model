import pandas as pd
import pickle
import sys
from src.features import calculate_features

def predict_match(home_team, away_team):
    """
    Predicts the outcome of a match between home_team and away_team.
    """
    # Load model
    try:
        with open('models/xgb_model.pkl', 'rb') as f:
            model = pickle.load(f)
    except FileNotFoundError:
        print("Model not found. Please run main.py first to train the model.")
        return

    # Load recent data
    try:
        df = pd.read_csv('data/merged_data.csv')
    except FileNotFoundError:
        print("Data not found. Please run main.py first.")
        return

    # Check if teams exist
    if home_team not in df['HomeTeam'].unique():
        print(f"Team '{home_team}' not found in database.")
        return
    if away_team not in df['AwayTeam'].unique():
        print(f"Team '{away_team}' not found in database.")
        return

    # Create dummy row
    dummy_row = {
        'Date': pd.Timestamp.now().strftime('%d/%m/%Y'),
        'HomeTeam': home_team,
        'AwayTeam': away_team,
        'FTHG': 0, 'FTAG': 0, 'FTR': 'D', 
        'B365H': 2.0, 'B365D': 3.0, 'B365A': 4.0,
        'Home_xG': 1.5, 'Away_xG': 1.0, # Dummy xG for the dummy match
        'Season': '2324'
    }
    
    # Append to df
    df_with_dummy = pd.concat([df, pd.DataFrame([dummy_row])], ignore_index=True)
    
    # Recalculate features
    df_processed = calculate_features(df_with_dummy)
    
    # Get the last row (our dummy match)
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
    
    outcomes = ['Home Win', 'Draw', 'Away Win']
    
    print(f"\nPrediction for {home_team} vs {away_team}:")
    print(f"Predicted Outcome: {outcomes[prediction]}")
    print(f"Probabilities:")
    print(f"  Home Win: {probs[0]:.1%}")
    print(f"  Draw:     {probs[1]:.1%}")
    print(f"  Away Win: {probs[2]:.1%}")
    
    print(f"\n(Note: Odds used for prediction were defaults: 2.0/3.0/4.0. Actual odds may vary model output if included as features.)")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python predict.py 'Home Team' 'Away Team'")
        print("Example: python predict.py 'Arsenal' 'Liverpool'")
    else:
        predict_match(sys.argv[1], sys.argv[2])
