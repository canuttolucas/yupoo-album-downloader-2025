
import os
import sys
# Add current dir to path
sys.path.append(os.getcwd())
from photo_organizer import PhotoOrganizer

organizer = PhotoOrganizer()

def test_classify(filename):
    print(f"\n--- FILE: {filename} ---")
    res = organizer.classify_file(filename)
    print(f"  Team: {res['team_name']}")
    print(f"  Season: {res['season']}")
    print(f"  Product Type: {res['product_type']}")
    print(f"  Target Folder: {res['target_folder']}")

test_files = [
    "Spain 2018 Home.png",
    "Spain 2026 Home Retro.png",
    "Spain 2026 Home Stadium.png",
    "Portugal 1998 Away.png"
]

for f in test_files:
    test_classify(f)
