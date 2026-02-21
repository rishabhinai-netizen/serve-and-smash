"""
Generate a round-robin schedule for 7 teams across 2 courts.

7 teams => C(7,2) = 21 matches. ✓
Each team plays 6 matches (against each other team exactly once).

Constraint: No team plays more than 2 matches back-to-back (measured in
consecutive *rounds*). Each round has 2 concurrent matches (one per court).
One team gets a BYE each round (7 teams, 2 courts = 4 playing, 3 idle per round
→ actually 3 teams rest per round).

We use a standard round-robin algorithm for 7 teams + 1 dummy bye slot = 8 slots.
"""

import random
from itertools import combinations


TEAM_NAMES = ["Team A", "Team B", "Team C", "Team D", "Team E", "Team F", "Team G"]


def round_robin_schedule(teams):
    """
    Generate balanced round-robin using standard rotation algorithm.
    Returns list of rounds. Each round is a list of (team1, team2) pairs.
    With 7 teams + 1 dummy = 8, we get 7 rounds of 3 matches each = 21 matches.
    But we only have 2 courts, so each round plays 2 matches + 1 waits.
    We will split into slots differently.
    """
    n = len(teams)
    if n % 2 == 1:
        teams = teams + ["BYE"]
    n = len(teams)
    rounds = []
    fixed = teams[0]
    rotating = list(teams[1:])
    for _ in range(n - 1):
        half = n // 2
        pairs = []
        for i in range(half):
            a = fixed if i == 0 else rotating[i - 1]
            b = rotating[n - 2 - i]
            if "BYE" not in (a, b):
                pairs.append((a, b))
        rounds.append(pairs)
        rotating = [rotating[-1]] + rotating[:-1]
    return rounds


def build_court_schedule(team_names, courts):
    """
    Build a flat list of match slots respecting:
    - Max 2 consecutive matches for any team (counted across ALL slots, not per-round)
    - All 21 matches played
    - 2 courts running concurrently when possible

    Returns: list of dicts with {team1, team2, court_name, match_order}
    """
    # Generate all 21 pairings
    all_pairs = list(combinations(team_names, 2))
    random.shuffle(all_pairs)

    # Track consecutive play count per team
    consecutive = {t: 0 for t in team_names}
    last_played = {t: -1 for t in team_names}

    schedule = []
    remaining = list(all_pairs)
    slot = 0  # court slot index (each slot = one round of up to 2 concurrent matches)

    MAX_SLOTS = 200  # safety
    slot_count = 0

    while remaining and slot_count < MAX_SLOTS:
        slot_count += 1
        slot_matches = []
        busy_this_slot = set()

        for court in courts:
            if not remaining:
                break
            # Find best match for this court slot
            best = None
            best_score = -1
            for pair in remaining:
                t1, t2 = pair
                if t1 in busy_this_slot or t2 in busy_this_slot:
                    continue
                # Check consecutive constraint
                c1 = consecutive[t1] if last_played[t1] == slot - 1 else 0
                c2 = consecutive[t2] if last_played[t2] == slot - 1 else 0
                if c1 >= 2 or c2 >= 2:
                    continue
                # Score: prefer teams that haven't played recently (more rest)
                rest1 = slot - last_played[t1]
                rest2 = slot - last_played[t2]
                score = rest1 + rest2
                if score > best_score:
                    best_score = score
                    best = pair

            if best:
                remaining.remove(best)
                slot_matches.append((best[0], best[1], court))
                busy_this_slot.add(best[0])
                busy_this_slot.add(best[1])

        # Update consecutive counts
        playing_now = set()
        for t1, t2, _ in slot_matches:
            playing_now.add(t1)
            playing_now.add(t2)

        for team in team_names:
            if team in playing_now:
                if last_played[team] == slot - 1:
                    consecutive[team] += 1
                else:
                    consecutive[team] = 1
                last_played[team] = slot
            # Don't reset consecutive here; only matters when they play again

        for t1, t2, court in slot_matches:
            schedule.append({
                "team1": t1, "team2": t2,
                "court_name": court,
                "match_order": len(schedule) + 1
            })

        slot += 1

    # If any remaining (shouldn't happen with valid inputs), append them
    for pair in remaining:
        t1, t2 = pair
        schedule.append({
            "team1": t1, "team2": t2,
            "court_name": courts[len(schedule) % len(courts)],
            "match_order": len(schedule) + 1
        })

    return schedule


def validate_schedule(schedule, team_names):
    """Validate no team has more than 2 back-to-back matches. Returns issues list."""
    issues = []
    # Group by match_order pairs (concurrent = same slot)
    # Determine slots: matches on same slot are concurrent
    # We define a 'slot' as every 2 matches (since 2 courts)
    from math import ceil
    n = len(schedule)
    slots = []
    for i in range(0, n, 2):
        slot_matches = schedule[i:i+2]
        playing = set()
        for m in slot_matches:
            playing.add(m["team1"])
            playing.add(m["team2"])
        slots.append(playing)

    for team in team_names:
        consecutive = 0
        for i, slot in enumerate(slots):
            if team in slot:
                consecutive += 1
                if consecutive > 2:
                    issues.append(f"{team} plays 3+ consecutive slots at slot {i+1}")
            else:
                consecutive = 0
    return issues
