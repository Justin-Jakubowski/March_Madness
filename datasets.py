import pandas as pd

# Load KenPom Barttorvik dataset
BASE_CSV = 'Kaggle/KenPom Barttorvik.csv'  # Update path if needed
def load_base_dataset(csv_path=BASE_CSV):
    """
    Loads the KenPom Barttorvik CSV as the base dataset.
    Returns a pandas DataFrame.
    """
    df = pd.read_csv(csv_path)
    return df

def generate_first_round_matchups(bracket_csv):
    """
    Given a bracket CSV with columns Seed, Team, Region,
    returns a list of matchups for each region: [(region, seed1, team1, seed2, team2)]
    """
    df = pd.read_csv(bracket_csv)
    matchups = []
    for region in df['Region'].unique():
        region_df = df[df['Region'] == region].copy()
        # Convert seed to int for sorting
        region_df.loc[:, 'Seed'] = region_df['Seed'].astype(int)
        # Sort by seed
        region_df = region_df.sort_values('Seed')
        # Create seed pairs: 1 vs 16, 2 vs 15, ..., 8 vs 9
        for i in range(1, 9):
            team1 = region_df[region_df['Seed'] == i]
            team2 = region_df[region_df['Seed'] == 17 - i]
            if not team1.empty and not team2.empty:
                matchups.append((region, i, team1.iloc[0]['Team'], 17 - i, team2.iloc[0]['Team']))
    return matchups

def clean_whitespace(df):
    """
    Removes extra whitespace from all string columns in the DataFrame.
    """
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)
    return df

def build_game_level_row(matchup, stats_df):
    """
    Given a single matchup tuple and stats DataFrame,
    returns a dict of stat differences for that game.
    Prints a warning if either team is not found for 2023.
    """
    stat_cols = ['K TEMPO', 'KADJ T', 'K OFF', 'K DEF', 'KADJ D', 'BADJ EM', 'BADJ O', 'BADJ D', 'WIN%']
    region, seed1, team1, seed2, team2 = matchup
    # Only use stats for 2023
    df_2023 = stats_df[stats_df['YEAR'] == 2023]
    t1_stats = df_2023[df_2023['TEAM'] == str(team1)]
    t2_stats = df_2023[df_2023['TEAM'] == str(team2)]
    #print(f"DEBUG: {team1} stats:")
    """DEBUG 
    if not t1_stats.empty:
        for col in stat_cols:
            print(f"  {col}: {t1_stats.iloc[0][col]}")
    else:
        print("  Team not found in 2023 stats.")
    #print(f"DEBUG: {team2} stats:")
    if not t2_stats.empty:
        for col in stat_cols:
            print(f"  {col}: {t2_stats.iloc[0][col]}")
    else:
        print("  Team not found in 2023 stats.")
        """
    if t1_stats.empty or t2_stats.empty:
        print(f"WARNING: Missing 2023 team stats for matchup: {team1} vs {team2} in {region}")
        
        return None  # Skip if either team not found
    t1_stats = t1_stats.iloc[0]
    t2_stats = t2_stats.iloc[0]
    diff_dict = {'Region': region, 'Seed1': seed1, 'Team1': team1, 'Seed2': seed2, 'Team2': team2}
    for col in stat_cols:
        try:
            diff_dict[f'diff_{col}'] = float(t1_stats[col]) - float(t2_stats[col])
        except Exception:
            diff_dict[f'diff_{col}'] = None
    return diff_dict

# Example usage
if __name__ == '__main__':
    df = load_base_dataset()
    df = clean_whitespace(df)
    bracket_csv = 'bracket.csv'
    matchups = generate_first_round_matchups(bracket_csv)
    game_level_rows = []
    for m in matchups:
        row = build_game_level_row(m, df)
        print(type(row), row)  # Debug print
        if row:
            game_level_rows.append(row)
            print("Appended:", row)
    game_level_df = pd.DataFrame(game_level_rows)
   #print("Game-level rows with stat differences:")
    #print(game_level_df.head())
    # Export to CSV
    game_level_df.to_csv('game_level_rows.csv', index=False)
    #print("Exported game-level rows to game_level_rows.csv")
