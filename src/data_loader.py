import pandas as pd
import requests
import io
import os
import json
from bs4 import BeautifulSoup
import time

def download_data(seasons=['2324', '2223', '2122', '2021', '1920']):
    """
    Downloads EPL data for specified seasons from football-data.co.uk.
    Seasons format: '2324' for 2023/2024.
    """
    base_url = "https://www.football-data.co.uk/mmz4281/"
    data_frames = []
    
    for season in seasons:
        url = f"{base_url}{season}/E0.csv"
        print(f"Downloading {url}...")
        try:
            s = requests.get(url).content
            df = pd.read_csv(io.StringIO(s.decode('utf-8', errors='ignore')))
            df['Season'] = season
            data_frames.append(df)
        except Exception as e:
            print(f"Error downloading {season}: {e}")
            
    if not data_frames:
        return None
        
    full_df = pd.concat(data_frames, ignore_index=True)
    
    # Save to disk
    os.makedirs('data', exist_ok=True)
    full_df.to_csv('data/epl_history.csv', index=False)
    print(f"Saved {len(full_df)} matches to data/epl_history.csv")
    return full_df

def fetch_understat_data(seasons=[2023, 2022, 2021, 2020, 2019]):
    """
    Scrapes xG data from Understat.com for EPL.
    """
    base_url = "https://understat.com/league/EPL/"
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
        
    xg_df = pd.DataFrame(all_matches)
    
    # Process xG DataFrame
    # Understat columns: 'h' (home team), 'a' (away team), 'xG' (home xG), 'xGA' (away xG) are inside 'history' usually? 
    # Actually datesData structure is: 
    # {'id': '22284', 'isResult': True, 'h': {'id': '89', 'title': 'Manchester United', 'short_title': 'MUN'}, 'a': {'id': '75', 'title': 'Fulham', 'short_title': 'FUL'}, 'goals': {'h': '1', 'a': '0'}, 'xG': {'h': '2.43807', 'a': '0.328325'}, 'datetime': '2024-08-16 19:00:00', ...}
    
    # Flatten the structure
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
    xg_df.to_csv('data/understat_history.csv', index=False)
    print(f"Saved {len(xg_df)} xG records to data/understat_history.csv")
    return xg_df

def merge_data():
    """
    Merges football-data.co.uk data with Understat xG data.
    """
    print("Merging data sources...")
    if not os.path.exists('data/epl_history.csv'):
        download_data()
    if not os.path.exists('data/understat_history.csv'):
        fetch_understat_data()
        
    df_fd = pd.read_csv('data/epl_history.csv')
    df_xg = pd.read_csv('data/understat_history.csv')
    
    # Standardize Dates
    df_fd['Date'] = pd.to_datetime(df_fd['Date'], dayfirst=True)
    df_xg['Date'] = pd.to_datetime(df_xg['Date'])
    
    # Team Name Mapping (Crucial step)
    # We need to map Understat names to football-data names
    # Let's try a fuzzy merge or manual mapping if needed.
    # For now, let's look at unique names.
    
    # Simple manual mapping for common discrepancies
    name_map = {
        'Manchester United': 'Man United',
        'Manchester City': 'Man City',
        'Newcastle United': 'Newcastle',
        'Nottingham Forest': "Nott'm Forest",
        'Sheffield United': 'Sheffield United', # Check FD
        'Wolverhampton Wanderers': 'Wolves',
        'Brighton': 'Brighton',
        'Leeds': 'Leeds',
        'Leicester': 'Leicester',
        'West Bromwich Albion': 'West Brom',
        'Tottenham': 'Tottenham',
        'West Ham': 'West Ham',
        'Luton': 'Luton',
        # Add more as discovered
    }
    
    # Apply mapping to Understat data to match football-data
    df_xg['HomeTeam_Map'] = df_xg['HomeTeam_Understat'].replace(name_map)
    df_xg['AwayTeam_Map'] = df_xg['AwayTeam_Understat'].replace(name_map)
    
    # Merge on Date and HomeTeam
    # Note: Dates might be slightly off (timezones). 
    # Let's merge on HomeTeam and "nearest date" or just Date if we trust it.
    # Understat dates are usually reliable.
    
    merged_df = pd.merge(df_fd, df_xg, 
                         left_on=['Date', 'HomeTeam'], 
                         right_on=['Date', 'HomeTeam_Map'], 
                         how='inner')
    
    # Check how many we lost
    print(f"Merged {len(merged_df)} matches out of {len(df_fd)} original matches.")
    
    merged_df.to_csv('data/merged_data.csv', index=False)
    return merged_df

if __name__ == "__main__":
    download_data()
    fetch_understat_data()
    merge_data()
