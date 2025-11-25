import pandas as pd
from src.data_loader import download_data, fetch_understat_data, merge_data
from src.features import calculate_features
from src.model import train_model, evaluate_betting_strategy
import os

def main():
    print("Step 1: Loading Data...")
    if os.path.exists('data/merged_data.csv'):
        df = pd.read_csv('data/merged_data.csv')
    else:
        # Ensure we have the data
        merge_data()
        df = pd.read_csv('data/merged_data.csv')
        
    print(f"Loaded {len(df)} matches.")

    print("\nStep 2: Feature Engineering...")
    df_processed = calculate_features(df)
    print(f"Processed data shape: {df_processed.shape}")
    
    print("\nStep 3: Training Gradient Boosting Model...")
    model, X_test, y_test, y_prob = train_model(df_processed)
    
    print("\nStep 4: Evaluating Strategy...")
    evaluate_betting_strategy(X_test, y_test, y_prob)

if __name__ == "__main__":
    main()
