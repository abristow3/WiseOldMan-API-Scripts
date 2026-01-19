import requests
import time
import csv
from collections import defaultdict
from requests.exceptions import HTTPError

BASE_URL = "https://api.wiseoldman.net/v2"
GROUP_ID = 141  # Flux WOM Group ID

# WOM has a 20 requests / minute rate limit
RATE_LIMIT = 20          # requests
RATE_WINDOW = 60         # seconds
REQUEST_SPACING = 3.2    # seconds between requests (20/min safe)

# Retry behavior
MAX_RETRIES = 3

request_count = 0
window_start = time.time()
last_request_time = 0.0


def rate_limited_get(url):
    global request_count, window_start, last_request_time

    for attempt in range(1, MAX_RETRIES + 1):
        now = time.time()

        # Enforce spacing between requests
        elapsed = now - last_request_time
        if elapsed < REQUEST_SPACING:
            sleep_time = REQUEST_SPACING - elapsed
            print(f"Waiting {sleep_time:.2f}s to respect pacing...")
            time.sleep(sleep_time)

        now = time.time()

        # Reset rate window if needed
        if now - window_start >= RATE_WINDOW:
            request_count = 0
            window_start = now

        # Hard rate-limit fallback
        if request_count >= RATE_LIMIT:
            wait_time = RATE_WINDOW - (now - window_start)
            wait_time = max(wait_time, 0)
            print(f"\nRate limit window reached. Waiting {wait_time:.1f}s...\n")
            time.sleep(wait_time)
            request_count = 0
            window_start = time.time()

        try:
            response = requests.get(url)
            last_request_time = time.time()
            request_count += 1

            if response.status_code == 500:
                raise HTTPError("500 Server Error", response=response)

            response.raise_for_status()
            return response.json()

        except HTTPError:
            if response.status_code == 500 and attempt < MAX_RETRIES:
                print(
                    f"500 error on {url} "
                    f"(attempt {attempt}/{MAX_RETRIES}), retrying..."
                )
                time.sleep(2)
            else:
                print(f"Failed to fetch {url} — skipping.")
                return None


def get_group_competitions(group_id):
    return rate_limited_get(f"{BASE_URL}/groups/{group_id}/competitions")


def get_competition_details(competition_id):
    return rate_limited_get(f"{BASE_URL}/competitions/{competition_id}")


def write_csv(results, filename="sotw_wins.csv"):
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["username", "wins"])

        for username, wins in results:
            writer.writerow([username, wins])

    print(f"\nCSV file written to: {filename}")


def main():
    competitions = get_group_competitions(GROUP_ID)
    if not competitions:
        print("Failed to load group competitions.")
        return

    sotw_wins = defaultdict(int)

    print(f"Loaded {len(competitions)} competitions\n")

    for comp in competitions:
        title = comp.get("title", "")
        title_lower = title.lower()

        if not any(k in title_lower for k in ("sotw", "skill of the week")):
            continue

        comp_id = comp["id"]
        print(f"Checking SOTW competition: {title}")

        details = get_competition_details(comp_id)
        if not details:
            print("  Skipped due to API error\n")
            continue

        participations = details.get("participations", [])
        if not participations:
            print("  No participations found\n")
            continue

        winner = max(
            participations,
            key=lambda p: p.get("progress", {}).get("gained", 0)
        )

        player = winner.get("player")
        if not player:
            print("  Winner has no player data\n")
            continue

        username = player["username"]
        sotw_wins[username] += 1
        print(f"  Winner: {username} (total wins: {sotw_wins[username]})\n")

    sorted_results = sorted(
        sotw_wins.items(),
        key=lambda x: x[1],
        reverse=True
    )

    print("\nFinal SOTW Win Totals:")
    for username, wins in sorted_results:
        print(f"{username}: {wins}")

    write_csv(sorted_results)


if __name__ == "__main__":
    main()
