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
    'uconn': 'Connecticut',
    'charleston': 'College of Charleston',
    'texas a m cc': 'Texas A&M-Corpus Christi',
    'se missouri state': 'Missouri State',
    'saint mary s': 'Saint Mary\'s',
    #'usc': 'Southern California',
    'miami': 'Miami FL',
    'vcu': 'Virginia Commonwealth',
    'texas a m': 'Texas A&M',
    'kansas state': 'Kansas St.',
    'boise state': 'Boise St.',
    'louisiana': 'Louisiana Lafayette',
    'arizona state': 'Arizona St.',

    # Add more as needed
}



team_seed_entries = []
with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    words = page.extract_words()

    def group_words_by_seed(words, top_min, top_max, x0_min, x0_max):
        import re
        groups = []
        used_indices = set()
        quadrant_words = [w for w in words if top_min <= w['top'] <= top_max and x0_min <= w['x0'] <= x0_max]
        quadrant_words.sort(key=lambda w: (w['top'], w['x0']))
        i = 0
        while i < len(quadrant_words):
            if i in used_indices:
                i += 1
                continue
            w = quadrant_words[i]
            text = w['text']
            tokens = re.findall(r'[A-Za-z]+|\d+', text)
            entry_words = set()
            entry_indices = set([i])
            # Case 1: digit only
            if len(tokens) == 1 and tokens[0].isdigit():
                seed = tokens[0]
                seed_top = w['top']
                entry = [seed]
                entry_words.add(seed)
                for j in range(len(quadrant_words)):
                    if j != i and abs(quadrant_words[j]['top'] - seed_top) <= 1 and j not in used_indices:
                        t2 = quadrant_words[j]['text']
                        t2_tokens = re.findall(r'[A-Za-z]+|\d+', t2)
                        for tok in t2_tokens:
                            if not tok.isdigit() and tok not in entry_words:
                                entry.append(tok)
                                entry_words.add(tok)
                        entry_indices.add(j)
                groups.append(entry)
                used_indices.update(entry_indices)
                i += 1
                continue
            # Case 2: digit-text combination (e.g., '14UC', '10Utah')
            if len(tokens) == 2 and tokens[0].isdigit():
                seed = tokens[0]
                seed_top = w['top']
                entry = [seed]
                entry_words.add(seed)
                if tokens[1] not in entry_words:
                    entry.append(tokens[1])
                    entry_words.add(tokens[1])
                entry_indices.add(i)
                for j in range(len(quadrant_words)):
                    if j != i and abs(quadrant_words[j]['top'] - seed_top) <= 1 and j not in used_indices:
                        t2 = quadrant_words[j]['text']
                        t2_tokens = re.findall(r'[A-Za-z]+|\d+', t2)
                        for tok in t2_tokens:
                            if not tok.isdigit() and tok not in entry_words:
                                entry.append(tok)
                                entry_words.add(tok)
                        entry_indices.add(j)
                groups.append(entry)
                used_indices.update(entry_indices)
                i += 1
                continue
            # Case 2b: text-digit combination (e.g., 'State10')
            if len(tokens) == 2 and tokens[1].isdigit():
                seed = tokens[1]
                seed_top = w['top']
                entry = [seed]
                entry_words.add(seed)
                if tokens[0] not in entry_words:
                    entry.append(tokens[0])
                    entry_words.add(tokens[0])
                entry_indices.add(i)
                for j in range(len(quadrant_words)):
                    if j != i and abs(quadrant_words[j]['top'] - seed_top) <= 1 and j not in used_indices:
                        t2 = quadrant_words[j]['text']
                        t2_tokens = re.findall(r'[A-Za-z]+|\d+', t2)
                        for tok in t2_tokens:
                            if not tok.isdigit() and tok not in entry_words:
                                entry.append(tok)
                                entry_words.add(tok)
                        entry_indices.add(j)
                groups.append(entry)
                used_indices.update(entry_indices)
                i += 1
                continue
            # Case 3: text only, keep reading until digit or digit-text
            if len(tokens) == 1 and tokens[0].isalpha():
                entry_text = [tokens[0]]
                entry_words.add(tokens[0])
                entry_indices.add(i)
                seed = None
                seed_top = w['top']
                j = i + 1
                while j < len(quadrant_words):
                    if j in used_indices:
                        j += 1
                        continue
                    w_next = quadrant_words[j]
                    t_next = w_next['text']
                    t_next_tokens = re.findall(r'[A-Za-z]+|\d+', t_next)
                    # If next is digit only
                    if len(t_next_tokens) == 1 and t_next_tokens[0].isdigit():
                        seed = t_next_tokens[0]
                        seed_top = w_next['top']
                        entry_indices.add(j)
                        break
                    # If next is digit-text
                    if len(t_next_tokens) == 2 and t_next_tokens[0].isdigit():
                        seed = t_next_tokens[0]
                        if t_next_tokens[1] not in entry_words:
                            entry_text.append(t_next_tokens[1])
                            entry_words.add(t_next_tokens[1])
                        seed_top = w_next['top']
                        entry_indices.add(j)
                        break
                    # If next is text-digit
                    if len(t_next_tokens) == 2 and t_next_tokens[1].isdigit():
                        seed = t_next_tokens[1]
                        if t_next_tokens[0] not in entry_words:
                            entry_text.append(t_next_tokens[0])
                            entry_words.add(t_next_tokens[0])
                        seed_top = w_next['top']
                        entry_indices.add(j)
                        break
                    # Otherwise, keep adding text
                    for tok in t_next_tokens:
                        if tok.isalpha() and tok not in entry_words:
                            entry_text.append(tok)
                            entry_words.add(tok)
                    entry_indices.add(j)
                    j += 1
                if seed:
                    entry = [seed] + entry_text
                    for k in range(len(quadrant_words)):
                        if k != i and k != j and abs(quadrant_words[k]['top'] - seed_top) <= 1 and k not in used_indices and k not in entry_indices:
                            t2 = quadrant_words[k]['text']
                            t2_tokens = re.findall(r'[A-Za-z]+|\d+', t2)
                            for tok2 in t2_tokens:
                                if not tok2.isdigit() and tok2 not in entry_words:
                                    entry.append(tok2)
                                    entry_words.add(tok2)
                            entry_indices.add(k)
                    groups.append(entry)
                    used_indices.update(entry_indices)
                    i = j + 1
                else:
                    i += 1
                continue
            i += 1
        return groups

# ...existing code to open PDF and extract words...

    south_teams_list = group_words_by_seed(words, 90, 310, 0, 200)
    print("BEFORE NICKNAME REPLACEMENT:", south_teams_list)
    midwest_teams_list = group_words_by_seed(words, 90, 310, 650, 800)
    print("BEFORE NICKNAME REPLACEMENT:", midwest_teams_list)
    east_teams_list = group_words_by_seed(words, 320, 570, 0, 200)
    print("BEFORE NICKNAME REPLACEMENT:", east_teams_list)
    west_teams_list = group_words_by_seed(words, 320, 570, 650, 800)
    print("BEFORE NICKNAME REPLACEMENT:", west_teams_list)

# Iterate through each region's team list and replace nicknames with actual names

def replace_nicknames(region_lists, nickname_map):
    for teams in region_lists:
        for entry in teams:
            if len(entry) >= 2:
                i = 1
                while i < len(entry):
                    found = False
                    # Try all window sizes from 1 up to remaining words
                    for window in range(len(entry)-i, 0, -1):
                        candidate = ' '.join(entry[i:i+window]).lower().strip()
                        if candidate in nickname_map:
                            actual_name = nickname_map[candidate].split()
                            # Replace the matched window with the actual name
                            entry[i:i+window] = actual_name
                            i += len(actual_name)
                            found = True
                            break
                    if not found:
                        i += 1
    return region_lists

region_lists = [south_teams_list, midwest_teams_list, east_teams_list, west_teams_list]
replace_nicknames(region_lists, nickname_map)

print("AFTER NICKNAME REPLACEMENT:", south_teams_list)
print("AFTER NICKNAME REPLACEMENT:", midwest_teams_list)
print("AFTER NICKNAME REPLACEMENT:", east_teams_list)
print("AFTER NICKNAME REPLACEMENT:", west_teams_list)

output_csv = "bracket.csv"
with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Seed', 'Team', 'Region'])
    for region_name, region_list in zip(['South', 'Midwest', 'East', 'West'], [south_teams_list, midwest_teams_list, east_teams_list, west_teams_list]):
        for entry in region_list:
            if len(entry) >= 2:
                seed = entry[0]
                team = ' '.join(entry[1:])
                writer.writerow([seed, team, region_name])


   
