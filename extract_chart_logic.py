import sys
import os

repo_path = r'c:\Users\oopsy\OneDrive\Desktop\Investment Vibecodinglab'
api_file = os.path.join(repo_path, 'api', 'index.py')

# Since I just pushed the new one, I'll use git show to see the previous commit content
import subprocess
try:
    content = subprocess.check_output(['git', 'show', 'HEAD^:api/index.py'], cwd=repo_path).decode('utf-8', 'replace')
    lines = content.splitlines()
    # Looking for lines 1401 to 1464 based on Step 3837
    # 0-indexed: 1400 up to 1464
    slice = lines[1400:1470]
    out = "\n".join(slice)
    with open('chart_logic.txt', 'w', encoding='utf-8') as f:
        f.write(out)
    print("Saved to chart_logic.txt")
except Exception as e:
    print(f"Error: {e}")
