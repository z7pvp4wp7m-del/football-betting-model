import pandas as pd
import numpy as np

def calculate_features(df):
    """
    Calculates features for the football match data, including xG stats.
    """
    # Sort by date
    df['Date'] = pd.to_datetime(df['Date'], format='mixed')
    df = df.sort_values('Date')
    
    # Result encoding
    df['Result'] = df['FTR'].map({'H': 0, 'D': 1, 'A': 2})
    
    # Create a long dataframe for team stats
    home_df = df[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 'Home_xG', 'Away_xG']].copy()
    home_df.columns = ['Date', 'Team', 'Opponent', 'GoalsScored', 'GoalsConceded', 'FTR', 'xG_For', 'xG_Against']
    home_df['Points'] = home_df['FTR'].map({'H': 3, 'D': 1, 'A': 0})
    home_df['IsHome'] = 1
    
    away_df = df[['Date', 'AwayTeam', 'HomeTeam', 'FTAG', 'FTHG', 'FTR', 'Away_xG', 'Home_xG']].copy()
    away_df.columns = ['Date', 'Team', 'Opponent', 'GoalsScored', 'GoalsConceded', 'FTR', 'xG_For', 'xG_Against']
    away_df['Points'] = away_df['FTR'].map({'A': 3, 'D': 1, 'H': 0})
    away_df['IsHome'] = 0
    
    team_stats = pd.concat([home_df, away_df]).sort_values(['Team', 'Date'])
    
    # Calculate rolling features
    window = 5
    
    # Basic Form
    team_stats['Form_Points'] = team_stats.groupby('Team')['Points'].transform(lambda x: x.shift(1).rolling(window).sum())
    team_stats['Form_GoalsScored'] = team_stats.groupby('Team')['GoalsScored'].transform(lambda x: x.shift(1).rolling(window).mean())
    team_stats['Form_GoalsConceded'] = team_stats.groupby('Team')['GoalsConceded'].transform(lambda x: x.shift(1).rolling(window).mean())
    
    # xG Form
    team_stats['Form_xG_For'] = team_stats.groupby('Team')['xG_For'].transform(lambda x: x.shift(1).rolling(window).mean())
    team_stats['Form_xG_Against'] = team_stats.groupby('Team')['xG_Against'].transform(lambda x: x.shift(1).rolling(window).mean())
    
    # xG Performance (Actual - Expected) - Positive means overperforming (lucky or good finishing)
    team_stats['xG_Diff_For'] = team_stats['GoalsScored'] - team_stats['xG_For']
    team_stats['xG_Diff_Against'] = team_stats['GoalsConceded'] - team_stats['xG_Against'] # Positive means conceding more than expected (bad luck or bad defense)
    
    team_stats['Form_xG_Diff_For'] = team_stats.groupby('Team')['xG_Diff_For'].transform(lambda x: x.shift(1).rolling(window).mean())
    team_stats['Form_xG_Diff_Against'] = team_stats.groupby('Team')['xG_Diff_Against'].transform(lambda x: x.shift(1).rolling(window).mean())

    # Merge back
    home_stats = team_stats[team_stats['IsHome'] == 1][['Date', 'Team', 'Form_Points', 'Form_GoalsScored', 'Form_GoalsConceded', 'Form_xG_For', 'Form_xG_Against', 'Form_xG_Diff_For', 'Form_xG_Diff_Against']]
    home_stats.columns = ['Date', 'HomeTeam', 'Home_Form_Points', 'Home_Form_GS', 'Home_Form_GC', 'Home_Form_xG', 'Home_Form_xGA', 'Home_Form_xG_Diff', 'Home_Form_xGA_Diff']
    
    away_stats = team_stats[team_stats['IsHome'] == 0][['Date', 'Team', 'Form_Points', 'Form_GoalsScored', 'Form_GoalsConceded', 'Form_xG_For', 'Form_xG_Against', 'Form_xG_Diff_For', 'Form_xG_Diff_Against']]
    away_stats.columns = ['Date', 'AwayTeam', 'Away_Form_Points', 'Away_Form_GS', 'Away_Form_GC', 'Away_Form_xG', 'Away_Form_xGA', 'Away_Form_xG_Diff', 'Away_Form_xGA_Diff']
    
    df = pd.merge(df, home_stats, on=['Date', 'HomeTeam'], how='left')
    df = pd.merge(df, away_stats, on=['Date', 'AwayTeam'], how='left')
    
    # Drop rows with NaN (first 5 games)
    df = df.dropna(subset=['Home_Form_Points', 'Away_Form_Points'])
    
    return df
