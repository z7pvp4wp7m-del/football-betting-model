import pandas as pd

def calculate_league_table(df):
    """
    Calculates the league table from a dataframe of match results.
    Expects columns: HomeTeam, AwayTeam, FTHG, FTAG, FTR
    """
    teams = set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique())
    table = []
    
    for team in teams:
        # Home Stats
        home_games = df[df['HomeTeam'] == team]
        played_h = len(home_games)
        wins_h = len(home_games[home_games['FTR'] == 'H'])
        draws_h = len(home_games[home_games['FTR'] == 'D'])
        losses_h = len(home_games[home_games['FTR'] == 'A'])
        gf_h = home_games['FTHG'].sum()
        ga_h = home_games['FTAG'].sum()
        
        # Away Stats
        away_games = df[df['AwayTeam'] == team]
        played_a = len(away_games)
        wins_a = len(away_games[away_games['FTR'] == 'A'])
        draws_a = len(away_games[away_games['FTR'] == 'D'])
        losses_a = len(away_games[away_games['FTR'] == 'H'])
        gf_a = away_games['FTAG'].sum()
        ga_a = away_games['FTHG'].sum()
        
        # Total Stats
        played = played_h + played_a
        wins = wins_h + wins_a
        draws = draws_h + draws_a
        losses = losses_h + losses_a
        gf = gf_h + gf_a
        ga = ga_h + ga_a
        gd = gf - ga
        points = (wins * 3) + draws
        
        table.append({
            'Team': team,
            'P': played,
            'W': wins,
            'D': draws,
            'L': losses,
            'GF': int(gf) if not pd.isna(gf) else 0,
            'GA': int(ga) if not pd.isna(ga) else 0,
            'GD': int(gd) if not pd.isna(gd) else 0,
            'Pts': points
        })
        
    table_df = pd.DataFrame(table)
    # Sort by Points, then GD, then GF
    table_df = table_df.sort_values(by=['Pts', 'GD', 'GF'], ascending=False).reset_index(drop=True)
    table_df.index += 1 # 1-based rank
    return table_df

# Badge URLs (Using Wikipedia/Public sources for stability)
# A robust way is to use a mapping. 
BADGE_URLS = {
    # Premier League
    'Arsenal': 'https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg',
    'Aston Villa': 'https://upload.wikimedia.org/wikipedia/en/f/f9/Aston_Villa_FC_crest_%282016%29.svg',
    'Bournemouth': 'https://upload.wikimedia.org/wikipedia/en/e/e5/AFC_Bournemouth_%282013%29.svg',
    'Brentford': 'https://upload.wikimedia.org/wikipedia/en/2/2a/Brentford_FC_crest.svg',
    'Brighton': 'https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_%26_Hove_Albion_logo.svg',
    'Burnley': 'https://upload.wikimedia.org/wikipedia/en/6/62/Burnley_F.C._Logo.svg',
    'Chelsea': 'https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg',
    'Crystal Palace': 'https://upload.wikimedia.org/wikipedia/en/0/0c/Crystal_Palace_FC_logo.svg',
    'Everton': 'https://upload.wikimedia.org/wikipedia/en/7/7c/Everton_FC_logo.svg',
    'Fulham': 'https://upload.wikimedia.org/wikipedia/en/e/eb/Fulham_FC_%28shield%29.svg',
    'Liverpool': 'https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg',
    'Luton': 'https://upload.wikimedia.org/wikipedia/en/9/9d/Luton_Town_logo.svg',
    'Man City': 'https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg',
    'Man United': 'https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg',
    'Newcastle': 'https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg',
    'Nott\'m Forest': 'https://upload.wikimedia.org/wikipedia/en/e/e5/Nottingham_Forest_F.C._logo.svg',
    'Sheffield United': 'https://upload.wikimedia.org/wikipedia/en/9/9c/Sheffield_United_FC_logo.svg',
    'Tottenham': 'https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg',
    'West Ham': 'https://upload.wikimedia.org/wikipedia/en/c/c2/West_Ham_United_FC_logo.svg',
    'Wolves': 'https://upload.wikimedia.org/wikipedia/en/f/fc/Wolverhampton_Wanderers.svg',
    'Ipswich': 'https://upload.wikimedia.org/wikipedia/en/4/43/Ipswich_Town.svg',
    'Leicester': 'https://upload.wikimedia.org/wikipedia/en/2/2d/Leicester_City_crest.svg',
    'Southampton': 'https://upload.wikimedia.org/wikipedia/en/c/c9/FC_Southampton.svg',

    # Belgian Pro League (Selected)
    'Anderlecht': 'https://upload.wikimedia.org/wikipedia/en/7/76/RSC_Anderlecht_logo.svg',
    'Club Brugge': 'https://upload.wikimedia.org/wikipedia/en/d/d0/Club_Brugge_KV_logo.svg',
    'Genk': 'https://upload.wikimedia.org/wikipedia/en/f/f6/K_RC_Genk_Logo_2016.svg',
    'Gent': 'https://upload.wikimedia.org/wikipedia/en/f/f4/KAA_Gent_logo.svg',
    'Standard': 'https://upload.wikimedia.org/wikipedia/en/e/e4/Royal_Standard_de_Li%C3%A8ge.svg',
    'Union SG': 'https://upload.wikimedia.org/wikipedia/en/5/58/Royale_Union_Saint-Gilloise_Logo.svg',
    'Antwerp': 'https://upload.wikimedia.org/wikipedia/en/0/0f/Royal_Antwerp_Football_Club_logo.svg',
}

def get_team_badge(team_name):
    """Returns the URL of the team badge."""
    return BADGE_URLS.get(team_name, 'https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg')
