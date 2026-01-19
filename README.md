# Wise Old Man SOTW Tracker

This project analyzes **Skill of the Week (SOTW)** competitions for a Wise Old Man group and calculates total SOTW wins per player.

It uses the **Wise Old Man public API** and includes built-in rate limiting and retry handling to safely respect API limits.

---

## Features

- Fetches all competitions for a Wise Old Man group
- Filters competitions by **Skill of the Week**
- Determines winners based on highest XP gained
- Aggregates total SOTW wins per player
- Handles API rate limits and retries automatically

---

## Requirements

- Python 3.8+
- Internet connection

---

## Installation

### 1. Clone the repository
```bash
# Clone the repo
git clone git@github.com:abristow3/SOTW-Winners.git
cd SOTW-Winners
```
### 2. Create the Python virtual environment
```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```
### 3. Install the Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run
```bash
python3 sotw_winners.py
```

The winner details can be found in the `sotw_wins.csv` file that gets generated from the script and placed in the root directory of the project.