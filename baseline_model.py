import pandas as pd
from datasets import build_game_level_row, load_base_dataset, clean_whitespace

def baseline_predict_winner(game_row):
    """
    Baseline prediction: higher seed wins. If seeds are equal, use diff_WIN%.
    Returns 1 if Team1 is predicted to win, 2 if Team2 is predicted to win.
    """
    seed1 = game_row['Seed1']
    seed2 = game_row['Seed2']
    # Lower seed number is better
    if seed1 < seed2:
        return game_row['Team1']
    elif seed2 < seed1:
        return game_row['Team2']
    else:
        # If seeds are equal, use diff_WIN%
        diff_win = game_row.get('diff_WIN%', 0)
        return game_row['Team1'] if diff_win > 0 else game_row['Team2']

def simulate_region(region_df):
    """
    Simulate the tournament for a single region using baseline logic.
    Returns the champion and the full bracket path.
    """
    # Initial teams: list of (seed, team)
    teams = [(row['Seed1'], row['Team1']) for _, row in region_df.iterrows()] + [(row['Seed2'], row['Team2']) for _, row in region_df.iterrows()]
    teams = list({(seed, team) for seed, team in teams})
    teams = sorted(teams, key=lambda x: x[0])
    bracket_path = []
    round_num = len(teams)
    stats_df = clean_whitespace(load_base_dataset())
    while len(teams) > 1:
        round_num = len(teams) * 4
        teams = sorted(teams, key=lambda x: x[0])
        matchups = []
        n = len(teams)
        for i in range(n // 2):
            high = teams[i]
            low = teams[n - 1 - i]
            matchups.append((region_df.iloc[0]['Region'], high[0], high[1], low[0], low[1]))
        # Build all game-level rows for this round
        round_rows = []
        for matchup in matchups:
            row = build_game_level_row(matchup, stats_df)
            if row:
                round_rows.append(row)
        # Predict winners for this round
        winners = []
        for row in round_rows:
            winner = baseline_predict_winner(row)
            winner_team = row['Team1'] if winner == row['Team1'] else row['Team2']
            winner_seed = row['Seed1'] if winner == row['Team1'] else row['Seed2']
            bracket_path.append({'Round': round_num, 'Matchup': f"{row['Team1']} ({row['Seed1']}) vs {row['Team2']} ({row['Seed2']})", 'Winner': winner_team})
            winners.append((winner_seed, winner_team))
        teams = winners
    champion = teams[0][1]
    return champion, bracket_path

# Example usage
if __name__ == '__main__':
    # For global accuracy aggregation
    global_round_acc = {64: {'correct': 0, 'total': 0}, 32: {'correct': 0, 'total': 0}, 16: {'correct': 0, 'total': 0}, 8: {'correct': 0, 'total': 0}, 4: {'correct': 0, 'total': 0}, 2: {'correct': 0, 'total': 0}}
    global_total = 0
    global_correct = 0
    # Load KenPom Barttorvik dataset for actual results
    actual_df = clean_whitespace(load_base_dataset())

    def get_team_round(team, stats_df):
        row = stats_df[(stats_df['TEAM'] == str(team)) & (stats_df['YEAR'] == 2023)]
        if not row.empty:
            return int(row.iloc[0]['ROUND'])
        return None

    def evaluate_predictions(bracket_path, stats_df):
        global global_round_acc, global_total, global_correct
        correct = 0
        total = 0
        round_acc = {}
        for match in bracket_path:
            round_num = match['Round']
            winner = match['Winner']
            winner_round = get_team_round(winner, stats_df)
            is_correct = winner_round < round_num if winner_round is not None else False
            correct += int(is_correct)
            total += 1
            if round_num not in round_acc:
                round_acc[round_num] = {'correct': 0, 'total': 0}
            round_acc[round_num]['correct'] += int(is_correct)
            round_acc[round_num]['total'] += 1
            if round_num in global_round_acc:
                global_round_acc[round_num]['correct'] += int(is_correct)
                global_round_acc[round_num]['total'] += 1
            global_total += 1
            global_correct += int(is_correct)
        overall_acc = correct / total if total > 0 else 0
        print(f"\nPrediction Accuracy (Region): {correct}/{total} ({overall_acc:.2%})")
        for rnd in sorted(round_acc.keys()):
            acc = round_acc[rnd]['correct'] / round_acc[rnd]['total'] if round_acc[rnd]['total'] > 0 else 0
            print(f"Round {rnd} Accuracy (Region): {round_acc[rnd]['correct']}/{round_acc[rnd]['total']} ({acc:.2%})")

    # Load game-level rows from previous step
    game_level_df = pd.read_csv('game_level_rows.csv')  # Update path if needed
    game_level_df['BaselineWinner'] = game_level_df.apply(baseline_predict_winner, axis=1)
    region_champions = {}
    region_seeds = {}
    for region in game_level_df['Region'].unique():
        region_df = game_level_df[game_level_df['Region'] == region]
        champion, bracket_path = simulate_region(region_df)
        print(f"Region: {region} Champion: {champion}")
        for match in bracket_path:
            winner_round = get_team_round(match['Winner'], actual_df)
            print(f"Round {match['Round']}: {match['Matchup']} -> Winner: {match['Winner']} (Eliminated at ROUND: {winner_round})")
        print()
        # Evaluate predictions for this region
        evaluate_predictions(bracket_path, actual_df)
        last_match = bracket_path[-1]
        champ_row = [row for row in region_df.itertuples() if row.Team1 == champion or row.Team2 == champion]
        if champ_row:
            champ_seed = champ_row[0].Seed1 if champ_row[0].Team1 == champion else champ_row[0].Seed2
        else:
            champ_seed = None
        region_champions[region] = champion
        region_seeds[region] = champ_seed

    # Semifinals: South vs East, Midwest vs West
    stats_df = clean_whitespace(load_base_dataset())
    semi_matchups = [
        ('Semifinal', region_seeds.get('South', 1), region_champions.get('South'), region_seeds.get('East', 1), region_champions.get('East')),
        ('Semifinal', region_seeds.get('Midwest', 1), region_champions.get('Midwest'), region_seeds.get('West', 1), region_champions.get('West'))
    ]
    semi_winners = []
    print('--- SEMIFINALS ---')
    for matchup in semi_matchups:
        row = build_game_level_row(matchup, stats_df)
        if row:
            winner = baseline_predict_winner(row)
            winner_team = row['Team1'] if winner == row['Team1'] else row['Team2']
            winner_seed = row['Seed1'] if winner == row['Team1'] else row['Seed2']
            winner_round = get_team_round(winner_team, actual_df)
            print(f"Round 4: {row['Team1']} ({row['Seed1']}) vs {row['Team2']} ({row['Seed2']}) -> Winner: {winner_team} (Eliminated at ROUND: {winner_round})")
            semi_winners.append((winner_seed, winner_team))

    # Final
    print('--- CHAMPIONSHIP ---')
    if len(semi_winners) == 2:
        final_matchup = ('Final', semi_winners[0][0], semi_winners[0][1], semi_winners[1][0], semi_winners[1][1])
        row = build_game_level_row(final_matchup, stats_df)
        if row:
            winner = baseline_predict_winner(row)
            winner_team = row['Team1'] if winner == row['Team1'] else row['Team2']
            winner_round = get_team_round(winner_team, actual_df)
            print(f"Round 2: {row['Team1']} ({row['Seed1']}) vs {row['Team2']} ({row['Seed2']}) -> WINNER: {winner_team} (Eliminated at ROUND: {winner_round})")

    # After all regions and finals, print global accuracy
    print("\n--- GLOBAL PREDICTION ACCURACY ---")
    for rnd in [64, 32, 16, 8, 4, 2]:
        correct = global_round_acc[rnd]['correct']
        total = global_round_acc[rnd]['total']
        acc = correct / total if total > 0 else 0
        print(f"Round {rnd} Accuracy: {correct}/{total} ({acc:.2%})")
    overall_acc = global_correct / global_total if global_total > 0 else 0
    print(f"Total Prediction Accuracy: {global_correct}/{global_total} ({overall_acc:.2%})")
