import requests
import time
import csv

BASE_URL = "https://api.wiseoldman.net/v2"
COMPETITION_CONFIGS = {
    5982: {"hunt": 6, "winner": "Jhinitalia"},
    16803: {"hunt": 8, "winner": "unlucky acc"},
    24042: {"hunt": 9, "winner": "muggerman3"},
    32847: {"hunt": 10, "winner": "gmbearmike"},
    43599: {"hunt": 11, "winner": "google knows"},
    67778: {"hunt": 12, "winner": "airxrs"},
    85479: {"hunt": 13, "winner": "frank donner"},
    100262: {"hunt": 14, "winner": "bigbloor"},
    130725: {"hunt": 15, "winner": "j essse"}
}

METRICS_TO_TRACK = [
    {
        "id": "ehb",
        "total_label": "total ehb gained",
        "average_label": "average ehb per hunt",
        "type": "progress_gained"
    },
    {
        "id": "chambers_of_xeric",
        "total_label": "total chambers_of_xeric",
        "average_label": "average chambers_of_xeric per hunt",
        "type": "progress_gained"
    },
    {
        "id": "chambers_of_xeric_challenge_mode",
        "total_label": "total chambers_of_xeric_challenge_mode",
        "average_label": "average chambers_of_xeric_challenge_mode per hunt",
        "type": "progress_gained"
    },
    {
        "id": "theatre_of_blood",
        "total_label": "total theatre_of_blood",
        "average_label": "average theatre_of_blood per hunt",
        "type": "progress_gained"
    },
    {
        "id": "theatre_of_blood_hard_mode",
        "total_label": "total theatre_of_blood_hard_mode",
        "average_label": "average theatre_of_blood_hard_mode per hunt",
        "type": "progress_gained"
    },
    {
        "id": "tombs_of_amascut",
        "total_label": "total tombs_of_amascut",
        "average_label": "average tombs_of_amascut per hunt",
        "type": "progress_gained"
    },
    {
        "id": "tombs_of_amascut_expert",
        "total_label": "total tombs_of_amascut_expert",
        "average_label": "average tombs_of_amascut_expert per hunt",
        "type": "progress_gained"
    },
    {
        "id": "cox",
        "total_label": "total cox",
        "average_label": "average cox per hunt",
        "type": "metric_sum",
        "sources": [
            "chambers_of_xeric",
            "chambers_of_xeric_challenge_mode"
        ]
    },
    {
        "id": "tob",
        "total_label": "total tob",
        "average_label": "average tob per hunt",
        "type": "metric_sum",
        "sources": [
            "theatre_of_blood",
            "theatre_of_blood_hard_mode"
        ]
    },
    {
        "id": "toa",
        "total_label": "total toa",
        "average_label": "average toa per hunt",
        "type": "metric_sum",
        "sources": [
            "tombs_of_amascut",
            "tombs_of_amascut_expert"
        ]
    },
    {
        "id": "raids",
        "total_label": "total raids",
        "average_label": "average raids per hunt",
        "type": "metric_sum",
        "sources": [
            "chambers_of_xeric",
            "chambers_of_xeric_challenge_mode",
            "theatre_of_blood",
            "theatre_of_blood_hard_mode",
            "tombs_of_amascut",
            "tombs_of_amascut_expert"
        ]
    }
]

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

def get_competition_details(competition_id, metric):
    return rate_limited_get(f"{BASE_URL}/competitions/{competition_id}?metric={metric}")


def extract_metric_value(participation, metric_def):
    metric_type = metric_def.get("type")
    if metric_type == "progress_gained":
        return participation.get("progress", {}).get("gained", 0)
    if metric_type == "field_path":
        value = participation
        for key in metric_def.get("path", []):
            if not isinstance(value, dict):
                return 0
            value = value.get(key, 0)
        return value if isinstance(value, (int, float)) else 0
    return 0


def find_winner_team(details, winner_username):
    participations = details.get("participations", [])
    for p in participations:
        player = p.get("player", {})
        username = player.get("username", "")
        if username.lower() == winner_username.lower():
            return p.get("teamName", None)
    return "No Team Found"


def get_unique_metrics(metric_defs):
    seen = set()
    unique = []
    for metric_def in metric_defs:
        if metric_def["type"] == "metric_sum":
            key = (metric_def["type"], tuple(metric_def.get("sources", [])))
        else:
            key = (metric_def["type"], metric_def["id"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(metric_def)
    return unique


def main():
    player_stats = {}
    unique_metrics = get_unique_metrics(METRICS_TO_TRACK)
    for comp_id, comp_config in COMPETITION_CONFIGS.items():
        winner = comp_config["winner"]
        hunt_num = comp_config["hunt"]
        base_details = get_competition_details(comp_id, "ehb")
        if not base_details:
            continue

        participations = base_details.get("participations", [])
        winning_team = find_winner_team(base_details, winner)
        print(f"Hunt {hunt_num}: Winning team is '{winning_team}'")

        for p in participations:
            player = p.get("player", {})
            username = player.get("username", "")
            team = p.get("teamName", None)
            if username not in player_stats:
                player_stats[username] = {
                    "wins": 0,
                    "participated": 0,
                    "won_hunts": [],
                    "lost_hunts": [],
                    "metrics": {m["id"]: 0 for m in unique_metrics}
                }
            player_stats[username]["participated"] += 1
            if team == winning_team:
                player_stats[username]["wins"] += 1
                player_stats[username]["won_hunts"].append(hunt_num)
            else:
                player_stats[username]["lost_hunts"].append(hunt_num)

        # Fetch each progress metric separately and add to totals.
        for metric_def in unique_metrics:
            if metric_def["type"] != "progress_gained":
                continue
            if metric_def["id"] == "ehb":
                metric_details = base_details
            else:
                metric_details = get_competition_details(comp_id, metric_def["id"])
            if not metric_details:
                continue
            for p in metric_details.get("participations", []):
                player = p.get("player", {})
                username = player.get("username", "")
                if username not in player_stats:
                    continue
                metric_value = extract_metric_value(p, metric_def)
                player_stats[username]["metrics"][metric_def["id"]] += metric_value

    # Compute derived metrics such as raids from individual sources.
    for stats in player_stats.values():
        for metric_def in unique_metrics:
            if metric_def["type"] != "metric_sum":
                continue
            stats["metrics"][metric_def["id"]] = sum(
                stats["metrics"].get(source, 0) for source in metric_def.get("sources", [])
            )

    results = []
    for username, stats in player_stats.items():
        win_pct = stats["wins"] / stats["participated"] if stats["participated"] > 0 else 0
        breakdown = f"Won: {stats['won_hunts']}; Lost: {stats['lost_hunts']}"
        row = [
            username,
            f"{win_pct:.2%}",
            stats["wins"],
            stats["participated"]
        ]
        for metric_def in unique_metrics:
            total = stats["metrics"][metric_def["id"]]
            average = total / stats["participated"] if stats["participated"] > 0 else 0
            row.append(f"{total:.2f}")
            row.append(f"{average:.2f}")
        row.append(breakdown)
        results.append(row)

    with open("hunt_player_stats.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = [
            "username",
            "hunt winning percentage",
            "number of hunts won",
            "number of hunts participated"
        ]
        for metric_def in unique_metrics:
            header.append(metric_def["total_label"])
            header.append(metric_def["average_label"])
        header.append("detailed breakdown")
        writer.writerow(header)
        writer.writerows(results)
    print("\nCSV file written to: hunt_player_stats.csv")


if __name__ == "__main__":
    main()
