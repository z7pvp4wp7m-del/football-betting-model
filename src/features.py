import pandas as pd
import numpy as np

def calculate_features(df):
    """
    Calculates features for the football match data.
    Handles optional xG stats.
    """
    # Sort by date
    df['Date'] = pd.to_datetime(df['Date'], format='mixed')
    df = df.sort_values('Date')
    
    # Result encoding
    df['Result'] = df['FTR'].map({'H': 0, 'D': 1, 'A': 2})
    
    # Check if xG data is available
    has_xg = 'Home_xG' in df.columns and 'Away_xG' in df.columns
    
    # Create a long dataframe for team stats
    cols = ['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']
    if has_xg:
        cols.extend(['Home_xG', 'Away_xG'])
        
    home_df = df[cols].copy()
    home_df.rename(columns={'HomeTeam': 'Team', 'AwayTeam': 'Opponent', 'FTHG': 'GoalsScored', 'FTAG': 'GoalsConceded'}, inplace=True)
    if has_xg:
        home_df.rename(columns={'Home_xG': 'xG_For', 'Away_xG': 'xG_Against'}, inplace=True)
    home_df['Points'] = home_df['FTR'].map({'H': 3, 'D': 1, 'A': 0})
    home_df['IsHome'] = 1
    
    away_df = df[cols].copy()
    away_df.rename(columns={'AwayTeam': 'Team', 'HomeTeam': 'Opponent', 'FTAG': 'GoalsScored', 'FTHG': 'GoalsConceded'}, inplace=True)
    if has_xg:
        away_df.rename(columns={'Away_xG': 'xG_For', 'Home_xG': 'xG_Against'}, inplace=True)
    away_df['Points'] = away_df['FTR'].map({'A': 3, 'D': 1, 'H': 0})
    away_df['IsHome'] = 0
    
    team_stats = pd.concat([home_df, away_df]).sort_values(['Team', 'Date'])
    
    # Calculate rolling features
    window = 5
    
    # Basic Form
    team_stats['Form_Points'] = team_stats.groupby('Team')['Points'].transform(lambda x: x.shift(1).rolling(window).sum())
    team_stats['Form_GS'] = team_stats.groupby('Team')['GoalsScored'].transform(lambda x: x.shift(1).rolling(window).mean())
    team_stats['Form_GC'] = team_stats.groupby('Team')['GoalsConceded'].transform(lambda x: x.shift(1).rolling(window).mean())
    
    # xG Form (Optional)
    if has_xg:
        team_stats['Form_xG_For'] = team_stats.groupby('Team')['xG_For'].transform(lambda x: x.shift(1).rolling(window).mean())
        team_stats['Form_xG_Against'] = team_stats.groupby('Team')['xG_Against'].transform(lambda x: x.shift(1).rolling(window).mean())
        
        # xG Performance
        team_stats['xG_Diff_For'] = team_stats['GoalsScored'] - team_stats['xG_For']
        team_stats['xG_Diff_Against'] = team_stats['GoalsConceded'] - team_stats['xG_Against']
        
        team_stats['Form_xG_Diff_For'] = team_stats.groupby('Team')['xG_Diff_For'].transform(lambda x: x.shift(1).rolling(window).mean())
        team_stats['Form_xG_Diff_Against'] = team_stats.groupby('Team')['xG_Diff_Against'].transform(lambda x: x.shift(1).rolling(window).mean())

    # Weather Features
    if 'Rain' in team_stats.columns:
        # Fill missing weather with 0/mean
        team_stats['Rain'] = team_stats['Rain'].fillna(0)
        team_stats['Temperature'] = team_stats['Temperature'].fillna(team_stats['Temperature'].mean())
        team_stats['WindSpeed'] = team_stats['WindSpeed'].fillna(team_stats['WindSpeed'].mean())
        
        # Interaction: Win Rate in Rain
        # We need to calculate this carefully to avoid data leakage (only use past games)
        team_stats['IsRain'] = (team_stats['Rain'] > 0.1).astype(int)
        
        # Calculate rolling win rate in rain for each team
        # This is complex, so for now let's just use the raw weather stats as features
        # The model (Gradient Boosting) can learn interactions itself
        
    # Merge back
    stats_cols = ['Date', 'Team', 'Form_Points', 'Form_GS', 'Form_GC']
    if 'Rain' in team_stats.columns:
        stats_cols.extend(['Rain', 'Temperature', 'WindSpeed'])
    if has_xg:
        stats_cols.extend(['Form_xG_For', 'Form_xG_Against', 'Form_xG_Diff_For', 'Form_xG_Diff_Against'])
        
    home_stats = team_stats[team_stats['IsHome'] == 1][stats_cols]
    home_stats.columns = ['Date', 'HomeTeam'] + [f'Home_{c}' for c in stats_cols[2:]]
    
    away_stats = team_stats[team_stats['IsHome'] == 0][stats_cols]
    away_stats.columns = ['Date', 'AwayTeam'] + [f'Away_{c}' for c in stats_cols[2:]]
    
    df = pd.merge(df, home_stats, on=['Date', 'HomeTeam'], how='left')
    df = pd.merge(df, away_stats, on=['Date', 'AwayTeam'], how='left')
    
    # Drop rows with NaN (first 5 games)
    df = df.dropna(subset=['Home_Form_Points', 'Away_Form_Points'])
    
    return df
