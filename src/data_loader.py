import pandas as pd
import requests
import io
import os
import json
from bs4 import BeautifulSoup
import time
from src.weather_loader import fetch_weather_batch

def download_data(league='E0', seasons=['2526', '2425', '2324', '2223', '2122']):
    """
    Downloads data for specified league and seasons from football-data.co.uk.
    Leagues: 'E0' (EPL), 'B1' (Belgium).
    """
    base_url = "https://www.football-data.co.uk/mmz4281/"
    data_frames = []
    
    for season in seasons:
        url = f"{base_url}{season}/{league}.csv"
        print(f"Downloading {url}...")
        try:
            s = requests.get(url).content
            df = pd.read_csv(io.StringIO(s.decode('utf-8', errors='ignore')))
            df['Season'] = season
            data_frames.append(df)
        except Exception as e:
            print(f"Error downloading {season} for {league}: {e}")
            
    if not data_frames:
        return None
        
    full_df = pd.concat(data_frames, ignore_index=True)
    
    # Save to disk
    os.makedirs('data', exist_ok=True)
    full_df.to_csv(f'data/{league}_history.csv', index=False)
    print(f"Saved {len(full_df)} matches to data/{league}_history.csv")
    return full_df

def fetch_understat_data(league='EPL', seasons=[2025, 2024, 2023, 2022, 2021]):
    """
    Scrapes xG data from Understat.com.
    Only supports leagues covered by Understat (EPL, La Liga, etc.).
    Returns None if league is not supported.
    """
    if league != 'EPL':
        print(f"Understat data not available/implemented for {league}")
        return None

    base_url = f"https://understat.com/league/{league}/"
    all_matches = []
    
    for season in seasons:
        url = f"{base_url}{season}"
        print(f"Fetching Understat data for {season}...")
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            scripts = soup.find_all('script')
            
            # Find the script with datesData
            data_script = None
            for script in scripts:
                if script.string and 'datesData' in script.string:
                    data_script = script.string
                    break
            
            if not data_script:
                print(f"Could not find data for {season}")
                continue
                
            # Extract JSON
            json_data = data_script.split("('")[1].split("')")[0]
            decoded_data = json_data.encode('utf-8').decode('unicode_escape')
            matches = json.loads(decoded_data)
            
            for match in matches:
                match['Season'] = season
                all_matches.append(match)
                
            time.sleep(1) # Be polite
            
        except Exception as e:
            print(f"Error fetching Understat {season}: {e}")
            
    if not all_matches:
        return None
        
    # Process xG DataFrame
    processed_matches = []
    for m in all_matches:
        if not m.get('isResult'):
            continue
            
        processed_matches.append({
            'Date': m['datetime'].split(' ')[0], # YYYY-MM-DD
            'HomeTeam_Understat': m['h']['title'],
            'AwayTeam_Understat': m['a']['title'],
            'Home_xG': float(m['xG']['h']),
            'Away_xG': float(m['xG']['a']),
            'Season': m['Season']
        })
        
    xg_df = pd.DataFrame(processed_matches)
    xg_df.to_csv(f'data/understat_{league}_history.csv', index=False)
    print(f"Saved {len(xg_df)} xG records to data/understat_{league}_history.csv")
    return xg_df

def merge_data(league_code='E0', understat_league='EPL'):
    """
    Merges football-data.co.uk data with Understat xG data (if available).
    """
    print(f"Merging data for {league_code}...")
    
    # Ensure raw data exists
    if not os.path.exists(f'data/{league_code}_history.csv'):
        download_data(league=league_code)
    
    df_fd = pd.read_csv(f'data/{league_code}_history.csv')
    
    # Try to fetch/load xG data
    df_xg = None
    if understat_league:
        if not os.path.exists(f'data/understat_{understat_league}_history.csv'):
            fetch_understat_data(league=understat_league)
        
        if os.path.exists(f'data/understat_{understat_league}_history.csv'):
            df_xg = pd.read_csv(f'data/understat_{understat_league}_history.csv')
    
    # Standardize Dates
    # Use mixed format for robustness as seen in previous issues
    df_fd['Date'] = pd.to_datetime(df_fd['Date'], format='mixed')
    
    if df_xg is not None:
        df_xg['Date'] = pd.to_datetime(df_xg['Date'])
        
        # Team Name Mapping
        name_map = {
            'Manchester United': 'Man United',
            'Manchester City': 'Man City',
            'Newcastle United': 'Newcastle',
            'Nottingham Forest': "Nott'm Forest",
            'Sheffield United': 'Sheffield United',
            'Wolverhampton Wanderers': 'Wolves',
            'Brighton': 'Brighton',
            'Leeds': 'Leeds',
            'Leicester': 'Leicester',
            'West Bromwich Albion': 'West Brom',
            'Tottenham': 'Tottenham',
            'West Ham': 'West Ham',
            'Luton': 'Luton',
        }
        
        df_xg['HomeTeam_Map'] = df_xg['HomeTeam_Understat'].replace(name_map)
        
        # Drop Season from xG data to avoid collision (Season_x, Season_y)
        if 'Season' in df_xg.columns:
            df_xg = df_xg.drop(columns=['Season'])
        
        merged_df = pd.merge(df_fd, df_xg, 
                             left_on=['Date', 'HomeTeam'], 
                             right_on=['Date', 'HomeTeam_Map'], 
                             how='inner')
        
        print(f"Merged {len(merged_df)} matches with xG data.")
        
        # Fetch Weather
        print("Fetching weather data...")
        # merged_df = fetch_weather_batch(merged_df)
        print("Skipping weather fetch (User requested speed)")
        
        merged_df.to_csv(f'data/merged_{league_code}.csv', index=False)
        return merged_df
    else:
        print("No xG data available. Using basic data.")
        
        # Fetch Weather
        print("Fetching weather data...")
        # df_fd = fetch_weather_batch(df_fd)
        print("Skipping weather fetch (User requested speed)")
        
        df_fd.to_csv(f'data/merged_{league_code}.csv', index=False)
        return df_fd

if __name__ == "__main__":
    # EPL
    merge_data('E0', 'EPL')
    # Belgium
    merge_data('B1', None)
