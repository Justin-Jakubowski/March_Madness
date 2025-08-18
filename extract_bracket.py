import pdfplumber
import csv
import pandas as pd

# Path to your PDF file
pdf_path = "2023 bracket.pdf"
output_csv = "bracket.csv"

ignore_keywords = ["FINAL", "FOUR", "ELITE", "CHAMPIONSHIP", "NATIONAL", "ROUND", "SWEET", "MARCH", "APRIL", "MEN'S", "TOURNAMENT", "BRACKET", "SECOND", "16-17", "18-19", "23-24", "25-26", "14-15", "EAST", "FIRST", "MEN’S", "MIDWEST", "NCAA", "SOUTH", "WEST" ]

# Load college names from Excel file
excel_path = "college_names.xlsx"  # Update with your actual file path
import re
df = pd.read_excel(excel_path)
def clean_team_name(name):
    # Remove non-ASCII and non-printable characters, normalize whitespace
    name = re.sub(r'[\s\u200B\u200C\u200D\uFEFF]+', ' ', name)  # Remove all whitespace and invisible chars
    name = re.sub(r'[^\x20-\x7E]', '', name)
    return name.strip()
college_names = [clean_team_name(n) for n in df['School'].dropna().astype(str).tolist()]

# Nickname mapping: PDF nickname -> full college name
nickname_map = {
    'Uconn': 'Connecticut',
    'charleston': 'College of Charleston',
    'Texas a m-cc': 'Texas A&M-Corpus Christi',
    'se missouri state': 'Missouri State',
    'Saint mary s': 'Saint Mary\'s (CA)',
    'usc': 'Southern California',
    'miami': 'Miami (FL)',
    'VCU': 'Virginia Commonwealth',
    'texas a m': 'Texas A&M',



    # Add more as needed
}


# Improved: Scan for multi-word college names using Excel list
team_seed_entries = []
with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    words = page.extract_words()
    seed_positions = []
    for i, word in enumerate(words):
        if word['text'].isdigit() and 1 <= int(word['text']) <= 16:
            seed_positions.append({'index': i, 'seed': int(word['text'])})
    # Lowercase list of college names for matching
    college_names_lower = [cname.lower() for cname in college_names]
    # Build a list of just the text from words
    import re
    # First pass: split any word containing both digits and letters into separate tokens
    cleaned_words = []
    for w in words:
        text = w['text']
        tokens = re.findall(r'\d+|[A-Za-z][A-Za-z\s\'-]*', text)
        for token in tokens:
            cleaned_words.append(token)

    # Lowercase list of college names for matching
    college_names_lower = [cname.lower() for cname in college_names]
    # Apply nickname mapping to college names for matching
    nickname_reverse = {v.lower(): k for k, v in nickname_map.items()}
    valid_school_names = set(college_names_lower) | set(nickname_reverse.keys())

    # === BEGIN QUADRUPLET MATCHING: number + 3-word school, 3-word school + number ===
    quadruplet_log = []
    used_indices = set()
    i = 0
    while i < len(cleaned_words) - 3:
        w1, w2, w3, w4 = cleaned_words[i], cleaned_words[i+1], cleaned_words[i+2], cleaned_words[i+3]
        w1_l, w2_l, w3_l, w4_l = w1.lower().strip(), w2.lower().strip(), w3.lower().strip(), w4.lower().strip()
        # Case 1: number + 3-word school
        if w1_l.isdigit():
            team_name = w2 + ' ' + w3 + ' ' + w4
            team_name_key = ' '.join(team_name.split()).lower().strip()
            for cname in valid_school_names:
                cname_norm = ' '.join(cname.split()).lower().strip()
                if team_name_key == cname_norm:
                    seed = int(w1)
                    quadruplet_log.append((w1, w2, w3, w4))
                    print(f"MATCH FOUND: '{team_name}' with seed {seed} (quadruplet, PDF vs Excel)")
                    team_seed_entries.append({'Team': team_name, 'Seed': seed})
                    # Remove matched words from cleaned_words
                    used_indices.update([i, i+1, i+2, i+3])
                    i += 4
                    break
            else:
                for nick_key, full_name in nickname_map.items():
                    nick_norm = ' '.join(nick_key.split()).lower().strip()
                    if team_name_key == nick_norm:
                        seed = int(w1)
                        quadruplet_log.append((w1, w2, w3, w4))
                        print(f"MATCH FOUND: '{team_name}' with seed {seed} (quadruplet, PDF vs Nickname)")
                        team_seed_entries.append({'Team': full_name, 'Seed': seed})
                        # Remove matched words from cleaned_words
                        used_indices.update([i, i+1, i+2, i+3])
                        i += 4
                        break
        # Case 2: 3-word school + number
        if w4_l.isdigit():
            team_name = w1 + ' ' + w2 + ' ' + w3
            team_name_key = ' '.join(team_name.split()).lower().strip()
            for cname in valid_school_names:
                cname_norm = ' '.join(cname.split()).lower().strip()
                if team_name_key == cname_norm:
                    seed = int(w4)
                    quadruplet_log.append((w1, w2, w3, w4))
                    print(f"MATCH FOUND: '{team_name}' with seed {seed} (quadruplet, PDF vs Excel)")
                    team_seed_entries.append({'Team': team_name, 'Seed': seed})
                    # Remove matched words from cleaned_words
                    for idx in sorted([i, i+1, i+2, i+3], reverse=True):
                        del cleaned_words[idx]
                    i = 0  # Restart scan after modification
                    break
            else:
                for nick_key, full_name in nickname_map.items():
                    nick_norm = ' '.join(nick_key.split()).lower().strip()
                    if team_name_key == nick_norm:
                        seed = int(w4)
                        quadruplet_log.append((w1, w2, w3, w4))
                        print(f"MATCH FOUND: '{team_name}' with seed {seed} (quadruplet, PDF vs Nickname)")
                        team_seed_entries.append({'Team': full_name, 'Seed': seed})
                        # Remove matched words from cleaned_words
                        for idx in sorted([i, i+1, i+2, i+3], reverse=True):
                            del cleaned_words[idx]
                        i = 0  # Restart scan after modification
                        break
        i += 1
    # === END QUADRUPLET MATCHING ===
    # Print all quadruplet matches
    if quadruplet_log:
        print("Quadruplet matches used for team/seed extraction:")
        for q in quadruplet_log:
            print(q)
        matched_teams_quad = set()
        for entry in team_seed_entries:
            team = entry['Team']
            team_key = team.lower().strip()
            if team_key in nickname_map:
                matched_teams_quad.add(nickname_map[team_key])
            else:
                matched_teams_quad.add(team)
        print(f"Teams found in PDF after quadruplet matching: {len(matched_teams_quad)} teams")

    # Triplet matching logic follows here
    triplet_log = []
    i = 0
    while i < len(cleaned_words) - 2:
        w1, w2, w3 = cleaned_words[i], cleaned_words[i+1], cleaned_words[i+2]
        w1_l, w2_l, w3_l = w1.lower().strip(), w2.lower().strip(), w3.lower().strip()
        # Case 1: number + valid school name (possibly multi-word)
        if w1_l.isdigit():
            team_name = w2 + ' ' + w3
            team_name_key = team_name.lower().strip()
            if team_name_key in valid_school_names:
                seed = int(w1)
                triplet_log.append((w1, w2, w3))
                print(f"MATCH FOUND: '{team_name}' with seed {seed} (triplet, PDF vs Excel)")
                team_seed_entries.append({'Team': team_name, 'Seed': seed})
                # Remove matched words from cleaned_words
                used_indices.update([i, i+1, i+2])
                i += 3
                continue
            else:
                # Try nickname conversion if not a direct match
                for nick_key, full_name in nickname_map.items():
                    if team_name_key == nick_key.lower().strip():
                        seed = int(w1)
                        triplet_log.append((w1, w2, w3))
                        print(f"MATCH FOUND: '{team_name}' with seed {seed} (triplet, PDF vs Nickname)")
                        team_seed_entries.append({'Team': full_name, 'Seed': seed})
                        # Remove matched words from cleaned_words
                        used_indices.update([i, i+1, i+2])
                        i += 3
                        break
                else:
                    pass  # No match, continue to next case
        # Case 2: valid school name (possibly multi-word) + number
        if w3_l.isdigit():
            team_name = w1 + ' ' + w2
            team_name_key = team_name.lower().strip()
            if team_name_key in valid_school_names:
                seed = int(w3)
                triplet_log.append((w1, w2, w3))
                print(f"MATCH FOUND: '{team_name}' with seed {seed} (triplet, PDF vs Excel)")
                team_seed_entries.append({'Team': team_name, 'Seed': seed})
                # Remove matched words from cleaned_words
                used_indices.update([i, i+1, i+2])
                i += 3
                continue
            else:
                # Try nickname conversion if not a direct match
                for nick_key, full_name in nickname_map.items():
                    if team_name_key == nick_key.lower().strip():
                        seed = int(w3)
                        triplet_log.append((w1, w2, w3))
                        print(f"MATCH FOUND: '{team_name}' with seed {seed} (triplet, PDF vs Nickname)")
                        team_seed_entries.append({'Team': full_name, 'Seed': seed})
                        # Remove matched words from cleaned_words
                        used_indices.update([i, i+1, i+2])
                        i += 3
                        break
                else:
                    pass  # No match, continue to next case
        i += 1
    # Print all triplet matches
    if triplet_log:
        print("Triplet matches used for team/seed extraction:")
        for t in triplet_log:
            print(t)
        matched_teams_triplet = set()
        for entry in team_seed_entries:
            team = entry['Team']
            team_key = team.lower().strip()
            if team_key in nickname_map:
                matched_teams_triplet.add(nickname_map[team_key])
            else:
                matched_teams_triplet.add(team)
        print(f"Teams found in PDF after triplet matching: {len(matched_teams_triplet)} teams")


    # Print teams found after triplet matching
    matched_teams_triplet = set()
    for entry in team_seed_entries:
        team = entry['Team']
        team_key = team.lower().strip()
        if team_key in nickname_map:
            matched_teams_triplet.add(nickname_map[team_key])
        else:
            matched_teams_triplet.add(team)
    print(f"Teams found in PDF after triplet matching: {len(matched_teams_triplet)} teams")


    # Second: extract pairs (number + valid school name)
    pair_log = []
    for i in range(len(cleaned_words) - 1):
        w1, w2 = cleaned_words[i], cleaned_words[i+1]
        w1_l, w2_l = w1.lower().strip(), w2.lower().strip()
        # Remove pair only if it is specifically 'april' and '3'
        # Case: number + valid school name
        if w1_l.isdigit() and w2_l in valid_school_names:
            team_name = w2
            seed = int(w1)
            pair_log.append((w1, w2))
            team_seed_entries.append({'Team': team_name, 'Seed': seed})
            used_indices.update([i, i+1])
            i += 2
            continue
        # Case: valid school name + number
        if w1_l in valid_school_names and w2_l.isdigit():
            team_name = w1
            seed = int(w2)
            pair_log.append((w2, w1))
            team_seed_entries.append({'Team': team_name, 'Seed': seed})
            used_indices.update([i, i+1])
            i += 2
            continue
        # Nickname handling for number + nickname
        if w1_l.isdigit():
            for nick_key, full_name in nickname_map.items():
                if w2_l == nick_key.lower().strip():
                    seed = int(w1)
                    pair_log.append((w1, w2))
                    team_seed_entries.append({'Team': full_name, 'Seed': seed})
                    used_indices.update([i, i+1])
                    i += 2
                    break
        # Nickname handling for nickname + number
        if w2_l.isdigit():
            for nick_key, full_name in nickname_map.items():
                if w1_l == nick_key.lower().strip():
                    seed = int(w2)
                    pair_log.append((w2, w1))   
                    team_seed_entries.append({'Team': full_name, 'Seed': seed})
                    used_indices.update([i, i+1])
                    i += 2
                    break
        i += 2

    # Print all pair matches
    
    # After pair matching, print the log and count
    if pair_log:
        print("Pair matches used for team/seed extraction:")
        for p in pair_log:
            print(p)
        matched_teams_pair = set()
        for entry in team_seed_entries:
            team = entry['Team']
            team_key = team.lower().strip()
            if team_key in nickname_map:
                matched_teams_pair.add(nickname_map[team_key])
            else:
                matched_teams_pair.add(team)
        print(f"Teams found in PDF after pair matching: {len(matched_teams_pair)} teams")

    
    # Sort college names by number of words (descending) to prioritize longer names
    sorted_colleges = sorted(zip(college_names, college_names_lower), key=lambda x: -len(x[1].split()))

# Write team-seed pairs to CSV
# Use the original team_seed_entries list, not the unique set

# Remove exact duplicates: team and seed both match ****************************************************************************************************************need to fix
unique_entries = []
seen = set()
for entry in team_seed_entries:
    key = (entry['Team'].lower().strip(), str(entry['Seed']))
    if key not in seen:
        unique_entries.append(entry)
        seen.add(key)
sorted_entries = sorted(unique_entries, key=lambda x: (int(x['Seed']) if str(x['Seed']).isdigit() else 99, x['Team']))

with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Team', 'Seed']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for entry in sorted_entries:
        writer.writerow({'Team': entry['Team'], 'Seed': entry['Seed']})

print(f"Team-seed data saved to {output_csv}")

"""DEBUGGING PURPOSES 
# Print all matched team names from quadruplets, triplets, and pairs
matched_teams = set()
for entry in team_seed_entries:
    team = entry['Team']
    team_key = team.lower().strip()
    if team_key in nickname_map:
        matched_teams.add(nickname_map[team_key])
    else:
        matched_teams.add(team)
print(f"Teams found in PDF after quadruplets, triplets, and pairs check: {len(matched_teams)} teams")
for team in sorted(matched_teams):
    print(team)


#Print all cleaned words from the PDF that were not matched as a team
matched_team_words = set()
for entry in team_seed_entries:
    for word in entry['Team'].split():
        matched_team_words.add(word.lower().strip())
unmatched_pdf_words = []
for word in cleaned_words:
    w_clean = word.lower().strip()
    # Ignore digits and already matched team words
    if not w_clean.isdigit() and w_clean not in matched_team_words:
        unmatched_pdf_words.append(word)
if unmatched_pdf_words:
    print(f"PDF words not matched as teams ({len(unmatched_pdf_words)}):")
    for word in sorted(set(unmatched_pdf_words)):
        print(word)
"""
#Print all possible consecutive word pairs in PDF
print("All consecutive word pairs in PDF:")
for i in range(len(cleaned_words) - 1):
    w1, w2 = cleaned_words[i], cleaned_words[i+1]
    print((w1, w2))
    """"""




