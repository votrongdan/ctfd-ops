"""
Generate a sample CSV file for testing the Account Provisioning plugin.
Run this script directly to create sample_players.csv in the sample/ directory.
"""

import csv
from pathlib import Path


def create_sample_csv(output_path=None):
    """Create a sample CSV file with player names."""
    if output_path is None:
        output_path = Path(__file__).parent / "sample" / "sample_players.csv"

    # Sample Vietnamese and English names
    names = [
        "Nguyễn Văn An",
        "Trần Thị Bình",
        "Lê Quốc Việt",
        "Đặng Thị Hương",
        "Phạm Minh Đức",
        "Hoàng Thị Lan",
        "Võ Thanh Tùng",
        "Bùi Thị Ngọc",
        # English names
        "John Smith",
        "Alice Johnson",
        "Bob Williams",
        # Duplicate name to test dedup
        "Nguyễn Văn An",
    ]

    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Player ID", "Name"])
        for i, name in enumerate(names, start=1):
            writer.writerow([f"P{i:03d}", name])

    return output_path


if __name__ == "__main__":
    path = create_sample_csv()
    print(f"Sample CSV file created at: {path}")
