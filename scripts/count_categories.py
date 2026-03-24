from database import get_all_jobs
from api import _categorise
import os
import sys
from collections import Counter

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


jobs = get_all_jobs()
counts = Counter()
for j in jobs:
    cat = _categorise(j.get('title') or '')
    counts[cat] += 1

for cat, n in counts.most_common():
    print(f"{cat}: {n}")

print('\nTotal:', sum(counts.values()))
