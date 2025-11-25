import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, log_loss
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
import pickle
import os

def train_model(df):
    """
    Trains a HistGradientBoostingClassifier predictive model.
    """
    # Define features and target
    features = [
        'Home_Form_Points', 'Home_Form_GS', 'Home_Form_GC', 
        'Away_Form_Points', 'Away_Form_GS', 'Away_Form_GC',
        'Home_Form_xG', 'Home_Form_xGA', 'Home_Form_xG_Diff', 'Home_Form_xGA_Diff',
        'Away_Form_xG', 'Away_Form_xGA', 'Away_Form_xG_Diff', 'Away_Form_xGA_Diff',
        'B365H', 'B365D', 'B365A'
    ]
    target = 'Result' # 0: Home, 1: Draw, 2: Away
    
    # Drop rows with missing values in features
    df = df.dropna(subset=features + [target])
    
    X = df[features]
    y = df[target]
    
    # Time-based split (train on older, test on newer)
    split_index = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split_index], X.iloc[split_index:]
    y_train, y_test = y.iloc[:split_index], y.iloc[split_index:]
    
    print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples.")
    
    # Initialize Model
    model = HistGradientBoostingClassifier(
        max_iter=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42,
        scoring='loss'
    )
    
    # Train
    model.fit(X_train, y_train)
    
    # Predict
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)
    
    # Evaluate
    acc = accuracy_score(y_test, y_pred)
    loss = log_loss(y_test, y_prob)
    
    print(f"Accuracy: {acc:.4f}")
    print(f"Log Loss: {loss:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Home', 'Draw', 'Away']))
    
    # Feature Importance (Permutation Importance since HistGradientBoosting doesn't have feature_importances_)
    print("\nCalculating Feature Importance...")
    result = permutation_importance(model, X_test, y_test, n_repeats=10, random_state=42, n_jobs=1)
    importances = pd.DataFrame({
        'feature': features,
        'importance': result.importances_mean
    }).sort_values('importance', ascending=False)
    
    print("\nFeature Importance:")
    print(importances)
    
    # Save model
    os.makedirs('models', exist_ok=True)
    with open('models/xgb_model.pkl', 'wb') as f: # Keep name for compatibility with predict.py
        pickle.dump(model, f)
        
    return model, X_test, y_test, y_prob

def evaluate_betting_strategy(X_test, y_test, y_prob):
    """
    Simple simulation of a value betting strategy.
    """
    results = X_test.copy()
    results['Actual'] = y_test
    results['Prob_H'] = y_prob[:, 0]
    results['Prob_D'] = y_prob[:, 1]
    results['Prob_A'] = y_prob[:, 2]
    
    results['Implied_H'] = 1 / results['B365H']
    results['Implied_D'] = 1 / results['B365D']
    results['Implied_A'] = 1 / results['B365A']
    
    threshold = 1.05 
    
    initial_bankroll = 1000
    bankroll = initial_bankroll
    bet_size = 10 
    
    bets_placed = 0
    wins = 0
    
    for idx, row in results.iterrows():
        if row['Prob_H'] > row['Implied_H'] * threshold:
            bets_placed += 1
            bankroll -= bet_size
            if row['Actual'] == 0: 
                bankroll += bet_size * row['B365H']
                wins += 1
        
        elif row['Prob_A'] > row['Implied_A'] * threshold:
            bets_placed += 1
            bankroll -= bet_size
            if row['Actual'] == 2: 
                bankroll += bet_size * row['B365A']
                wins += 1
                
    roi = (bankroll - initial_bankroll) / (bets_placed * bet_size) if bets_placed > 0 else 0
    
    print(f"\n--- Betting Simulation ---")
    print(f"Initial Bankroll: {initial_bankroll}")
    print(f"Final Bankroll: {bankroll:.2f}")
    print(f"Bets Placed: {bets_placed}")
    print(f"Win Rate: {wins/bets_placed:.2%}" if bets_placed > 0 else "Win Rate: N/A")
    print(f"ROI: {roi:.2%}")
    
    return bankroll
