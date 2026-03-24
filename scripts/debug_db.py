from database import get_all_jobs
import os
import sys
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))
jobs = get_all_jobs()
print('jobs len', len(jobs))
for j in jobs[:10]:
    print(j.get('id')[:8], '|', j.get('title'), '|', j.get('location'))
