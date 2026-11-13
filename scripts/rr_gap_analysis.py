"""
RR IPL 2026 Gap Analysis
Identifies Rajasthan Royals' squad, phase-wise performance, 
win/loss breakdown, and strategic gaps for 2027 auction targeting.
"""

import pandas as pd
import numpy as np
import json

pd.set_option('future.no_silent_downcasting', True)

print("Loading enriched ball-by-ball data...")
df = pd.read_csv('d:/ipl-rating/enriched_bbb.csv', low_memory=False)

# ── 1. Isolate IPL 2026 ──────────────────────────────────────────────────────
ipl26 = df[df['comp_id'] == 3298].copy()
print(f"IPL 2026 deliveries: {len(ipl26)}")

# Check which teams are present
batting_teams = ipl26['batting_team_id'].unique()
bowling_teams = ipl26['bowling_team_id'].unique()
all_team_ids = set(batting_teams) | set(bowling_teams)
print(f"Team IDs in IPL 2026: {all_team_ids}")

# ── 2. Identify RR team_id ───────────────────────────────────────────────────
# Try loading competition_team_player_mapping from the Data Pack
import os

data_pack_paths = [
    r'C:\Users\Shourya\Downloads\6af458274c1e8_data_pack\Data Pack',
    r'C:\Users\Shourya\Downloads',
]

ctpm = None
for dp in data_pack_paths:
    fp = os.path.join(dp, 'competition_team_player_mapping.csv')
    if os.path.exists(fp):
        ctpm = pd.read_csv(fp)
        print(f"Loaded ctpm from {fp}: {ctpm.shape}")
        break

if ctpm is None:
    print("WARNING: competition_team_player_mapping.csv not found, trying teams.csv")
    for dp in data_pack_paths:
        fp = os.path.join(dp, 'teams.csv')
        if os.path.exists(fp):
            teams_df = pd.read_csv(fp)
            print("teams.csv cols:", teams_df.columns.tolist())
            rr_teams = teams_df[teams_df.apply(lambda r: 'rajasthan' in str(r).lower(), axis=1)]
            print("RR rows:", rr_teams)
            break

if ctpm is not None:
    print("CTPM cols:", ctpm.columns.tolist())
    print("CTPM sample:\n", ctpm.head(3))
    # Find RR
    rr_rows = ctpm[ctpm.apply(lambda r: 'rajasthan' in str(r).lower(), axis=1)]
    print("RR rows in ctpm:", rr_rows.shape)
    if len(rr_rows) > 0:
        print(rr_rows[['comp_id', 'team_id', 'team_name']].drop_duplicates().head(10) if 'team_name' in rr_rows.columns else rr_rows.head(5))
