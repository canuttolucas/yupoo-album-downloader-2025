
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
    print(f"  Target Filename: {res['target_filename']}")

test_files = [
    "Spain 2026 Home Stadium Pre-sale 1.1 Quality S-4XL_CAPA_HQ.png",
    "Spain 2026 Home Kids Kit Jersey Size 16-28_CAPA_HQ.png",
    "Spain 2026 Home Player Version Jersey S-4XL_CAPA_HQ.png",
    "Spain 2026 Home Women Jersey S-XXL_CAPA_HQ.png",
    "Spain 2026 Home Shorts S-XXL_CAPA_HQ.png"
]

for f in test_files:
    test_classify(f)
