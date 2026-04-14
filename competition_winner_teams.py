import requests
import time
import csv

BASE_URL = "https://api.wiseoldman.net/v2"
COMPETITION_ID_TO_HUNT = {
    5982: 6,
    16803: 8,
    24042: 9,
    32847: 10,
    43599: 11,
    67778: 12,
    85479: 13,
    100262: 14,
    130725: 15
}
COMPETITION_IDS = list(COMPETITION_ID_TO_HUNT.keys())
WINNERS = {
    5982: "Jhinitalia",    # 6
    16803: "unlucky acc",  # 8
    24042: "muggerman3",   # 9
    32847: "gmbearmike",   # 10
    43599: "google knows", # 11
    67778: "airxrs",       # 12
    85479: "frank donner", # 13
    100262: "bigbloor",    # 14
    130725: "j essse"      # 15
}

RATE_LIMIT = 20
RATE_WINDOW = 60
REQUEST_SPACING = 3.2
MAX_RETRIES = 3
request_count = 0
window_start = time.time()
last_request_time = 0.0

def rate_limited_get(url):
    global request_count, window_start, last_request_time
    for attempt in range(1, MAX_RETRIES + 1):
        now = time.time()
        elapsed = now - last_request_time
        if elapsed < REQUEST_SPACING:
            time.sleep(REQUEST_SPACING - elapsed)
        now = time.time()
        if now - window_start >= RATE_WINDOW:
            request_count = 0
            window_start = now
        if request_count >= RATE_LIMIT:
            wait_time = RATE_WINDOW - (now - window_start)
            time.sleep(max(wait_time, 0))
            request_count = 0
            window_start = time.time()
        try:
            response = requests.get(url)
            last_request_time = time.time()
            request_count += 1
            response.raise_for_status()
            return response.json()
        except Exception:
            if attempt < MAX_RETRIES:
                time.sleep(2)
            else:
                return None

def get_competition_details(competition_id):
    return rate_limited_get(f"{BASE_URL}/competitions/{competition_id}")

def find_winner_team(details, winner_username):
    participations = details.get("participations", [])
    team_players = {}
    for p in participations:
        team = p.get("teamName", "No Team")
        player = p.get("player", {})
        username = player.get("username", "")
        if team not in team_players:
            team_players[team] = set()
        team_players[team].add(username.lower())

    for team, players in team_players.items():
        if winner_username.lower() in players:
            return team
    return "No Team Found"

def main():
    player_stats = {}
    for comp_id in COMPETITION_IDS:
        winner = WINNERS.get(comp_id)
        details = get_competition_details(comp_id)
        if not details:
            continue
        participations = details.get("participations", [])
        # Find winning team by matching winner to their team
        winning_team = None
        for p in participations:
            player = p.get("player", {})
            username = player.get("username", "")
            if username.lower() == winner.lower():
                winning_team = p.get("teamName", None)
                break
        hunt_num = COMPETITION_ID_TO_HUNT.get(comp_id, comp_id)
        print(f"Hunt {hunt_num}: Winning team is '{winning_team}'")
        # Mark all players in winning team as winners, others as participants
        for p in participations:
            player = p.get("player", {})
            username = player.get("username", "")
            team = p.get("teamName", None)
            if username not in player_stats:
                player_stats[username] = {
                    "wins": 0,
                    "participated": 0,
                    "won_hunts": [],
                    "lost_hunts": []
                }
            player_stats[username]["participated"] += 1
            if team == winning_team:
                player_stats[username]["wins"] += 1
                player_stats[username]["won_hunts"].append(hunt_num)
            else:
                player_stats[username]["lost_hunts"].append(hunt_num)

    results = []
    for username, stats in player_stats.items():
        win_pct = stats["wins"] / stats["participated"] if stats["participated"] > 0 else 0
        breakdown = f"Won: {stats['won_hunts']}; Lost: {stats['lost_hunts']}"
        results.append([
            username,
            f"{win_pct:.2%}",
            stats["wins"],
            stats["participated"],
            breakdown
        ])

    with open("hunt_player_stats.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "username",
            "hunt winning percentage",
            "number of hunts won",
            "number of hunts participated",
            "detailed breakdown"
        ])
        writer.writerows(results)
    print("\nCSV file written to: hunt_player_stats.csv")

if __name__ == "__main__":
    main()
