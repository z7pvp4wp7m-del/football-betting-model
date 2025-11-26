import pandas as pd
import requests
import time
import os
from datetime import datetime

# Stadium Coordinates (Lat, Lon)
# This is a manual mapping. In a production app, this could be a database or external service.
STADIUM_COORDS = {
    # Premier League (23/24 & 24/25)
    'Arsenal': (51.5549, -0.1084), # Emirates
    'Aston Villa': (52.5091, -1.8848), # Villa Park
    'Bournemouth': (50.7352, -1.8385), # Vitality
    'Brentford': (51.4907, -0.2928), # Gtech
    'Brighton': (50.8616, -0.0837), # Amex
    'Burnley': (53.7890, -2.2302), # Turf Moor
    'Chelsea': (51.4816, -0.1910), # Stamford Bridge
    'Crystal Palace': (51.3983, -0.0855), # Selhurst Park
    'Everton': (53.4388, -2.9663), # Goodison Park
    'Fulham': (51.4749, -0.2216), # Craven Cottage
    'Liverpool': (53.4308, -2.9608), # Anfield
    'Luton': (51.8841, -0.4188), # Kenilworth Road
    'Man City': (53.4831, -2.2004), # Etihad
    'Man United': (53.4631, -2.2913), # Old Trafford
    'Newcastle': (54.9756, -1.6217), # St James Park
    'Nott\'m Forest': (52.9400, -1.1328), # City Ground
    'Sheffield United': (53.3703, -1.4709), # Bramall Lane
    'Tottenham': (51.6042, -0.0662), # Tottenham Hotspur Stadium
    'West Ham': (51.5387, -0.0166), # London Stadium
    'Wolves': (52.5902, -2.1304), # Molineux
    'Ipswich': (52.0552, 1.1456), # Portman Road
    'Leicester': (52.6203, -1.1422), # King Power
    'Southampton': (50.9058, -1.3910), # St Mary's

    # Belgian Pro League (Major Teams)
    'Anderlecht': (50.8342, 4.2983), # Lotto Park
    'Antwerp': (51.2297, 4.4419), # Bosuilstadion
    'Club Brugge': (51.1931, 3.1805), # Jan Breydel
    'Genk': (51.0069, 5.5328), # Cegeka Arena
    'Gent': (51.0161, 3.7339), # Ghelamco Arena
    'Standard': (50.6097, 5.5444), # Sclessin
    'Union SG': (50.8275, 4.3358), # Joseph Marien
    'Charleroi': (50.4143, 4.4452), # Stade du Pays de Charleroi
    'Mechelen': (51.0383, 4.4777), # AFAS Stadion
    'Cercle Brugge': (51.1931, 3.1805), # Jan Breydel (Shared)
    'Leuven': (50.8625, 4.6853), # Den Dreef
    'Westerlo': (51.0933, 4.9183), # Het Kuipje
    'Kortrijk': (50.8253, 3.2497), # Guldensporenstadion
    'St Truiden': (50.8111, 5.1764), # Stayen
    'Eupen': (50.6211, 6.0375), # Kehrwegstadion
    'RWD Molenbeek': (50.8536, 4.2986), # Edmond Machtens
}

def get_coords(team_name):
    """Returns (lat, lon) for a team, or None if not found."""
    return STADIUM_COORDS.get(team_name)

def fetch_weather_batch(matches_df):
    """
    Fetches historical weather for a dataframe of matches.
    Uses caching to avoid redundant API calls.
    """
    cache_file = 'data/weather_cache.csv'
    
    # Load Cache
    if os.path.exists(cache_file):
        cache_df = pd.read_csv(cache_file)
        # Ensure Date is datetime
        cache_df['Date'] = pd.to_datetime(cache_df['Date'])
    else:
        cache_df = pd.DataFrame(columns=['Date', 'HomeTeam', 'Rain', 'Temperature', 'WindSpeed'])
    
    # Identify missing matches
    matches_df['Date'] = pd.to_datetime(matches_df['Date'])
    
    # Create a key for merging
    matches_df['key'] = matches_df['Date'].astype(str) + '_' + matches_df['HomeTeam']
    cache_df['key'] = cache_df['Date'].astype(str) + '_' + cache_df['HomeTeam']
    
    # Filter out matches already in cache
    missing_matches = matches_df[~matches_df['key'].isin(cache_df['key'])].copy()
    
    if missing_matches.empty:
        print("All weather data found in cache.")
        return pd.merge(matches_df, cache_df[['key', 'Rain', 'Temperature', 'WindSpeed']], on='key', how='left').drop(columns=['key'])

    print(f"Fetching weather for {len(missing_matches)} matches...")
    
    new_weather_data = []
    
    # Open-Meteo limits (approx 10k calls/day, but we should batch or be slow)
    # We will fetch one by one for simplicity, but with a small delay
    
    for idx, row in missing_matches.iterrows():
        team = row['HomeTeam']
        date_str = row['Date'].strftime('%Y-%m-%d')
        coords = get_coords(team)
        
        if not coords:
            # print(f"No coords for {team}, skipping weather.")
            continue
            
        lat, lon = coords
        
        # API Request
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": date_str,
            "end_date": date_str,
            "daily": "temperature_2m_max,precipitation_sum,wind_speed_10m_max",
            "timezone": "auto"
        }
        
        try:
            r = requests.get(url, params=params)
            data = r.json()
            
            if 'daily' in data:
                daily = data['daily']
                temp = daily['temperature_2m_max'][0]
                rain = daily['precipitation_sum'][0]
                wind = daily['wind_speed_10m_max'][0]
                
                new_weather_data.append({
                    'Date': row['Date'],
                    'HomeTeam': team,
                    'Rain': rain,
                    'Temperature': temp,
                    'WindSpeed': wind,
                    'key': row['key']
                })
        except Exception as e:
            print(f"Error fetching weather for {team} on {date_str}: {e}")
            
        # Be polite to the API
        # time.sleep(0.1) 
        
    # Update Cache
    if new_weather_data:
        new_df = pd.DataFrame(new_weather_data)
        # Drop key before saving to cache (we reconstruct it)
        # Actually we used key for checking, let's keep it consistent
        # cache_df has Date, HomeTeam, Rain, Temp, Wind
        
        # Append to cache
        save_cols = ['Date', 'HomeTeam', 'Rain', 'Temperature', 'WindSpeed']
        
        # We need to drop 'key' from new_df before concat if cache_df doesn't have it saved
        # But we added 'key' to cache_df in memory.
        # Let's just save the standard columns
        
        updated_cache = pd.concat([cache_df[save_cols], new_df[save_cols]], ignore_index=True)
        updated_cache.to_csv(cache_file, index=False)
        print(f"Updated weather cache with {len(new_df)} new records.")
        
        # Merge with original
        # Re-create key for merging
        new_df['key'] = new_df['Date'].astype(str) + '_' + new_df['HomeTeam']
        full_weather = pd.concat([cache_df[['key', 'Rain', 'Temperature', 'WindSpeed']], new_df[['key', 'Rain', 'Temperature', 'WindSpeed']]])
        
        result = pd.merge(matches_df, full_weather, on='key', how='left').drop(columns=['key'])
        return result
    else:
        # No new data found (maybe all missing coords)
        # Merge with existing cache
        result = pd.merge(matches_df, cache_df[['key', 'Rain', 'Temperature', 'WindSpeed']], on='key', how='left').drop(columns=['key'])
        return result

def fetch_forecast(team_name, date_str):
    """
    Fetches weather forecast for a specific team/date.
    Returns dict with Rain, Temperature, WindSpeed.
    """
    coords = get_coords(team_name)
    if not coords:
        return {'Rain': 0.0, 'Temperature': 15.0, 'WindSpeed': 10.0} # Default
        
    lat, lon = coords
    
    # Use Forecast API
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,precipitation_sum,wind_speed_10m_max",
        "timezone": "auto",
        "start_date": date_str,
        "end_date": date_str
    }
    
    try:
        r = requests.get(url, params=params)
        data = r.json()
        
        if 'daily' in data:
            daily = data['daily']
            return {
                'Rain': daily['precipitation_sum'][0],
                'Temperature': daily['temperature_2m_max'][0],
                'WindSpeed': daily['wind_speed_10m_max'][0]
            }
    except Exception as e:
        print(f"Error fetching forecast: {e}")
        
    return {'Rain': 0.0, 'Temperature': 15.0, 'WindSpeed': 10.0} # Fallback

if __name__ == "__main__":
    # Test
    test_df = pd.DataFrame({
        'Date': ['2023-08-12', '2023-08-12'],
        'HomeTeam': ['Arsenal', 'Burnley']
    })
    print(fetch_weather_batch(test_df))
