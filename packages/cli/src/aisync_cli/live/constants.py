from pathlib import Path


SUITS_DIR = Path(__file__).resolve().parents[3] / "core" / "suits"

if __name__ == "__main__":
    print(SUITS_DIR)
