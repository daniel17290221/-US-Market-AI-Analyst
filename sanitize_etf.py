
import os

path = r'c:\Users\mjang\Downloads\미국 종목 분석\templates\index.html'

try:
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # We want to clear the content BETWEEN line 587 and the end of the container.
    # Looking at the last view_file:
    # 586: <div class="space-y-3" id="etf-flow-container">
    # 587:     <!-- ETF Flow Items will be injected here -->
    # ...
    # And it should end before the Macro analysis section.
    
    start_found = False
    new_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if 'id="etf-flow-container"' in line:
            new_lines.append(line)
            new_lines.append('                            <p class="text-xs text-center text-gray-600 py-4 italic">데이터를 동기화 중입니다...</p>\n')
            start_found = True
            # Skip until we find the end of the sidebar column or the next section
            i += 1
            while i < len(lines) and '<!-- Macro Analysis -->' not in lines[i] and '</div>\n' != lines[i].strip() + '\n':
                 # This is tricky without knowing exact div balance.
                 # Let's search for the start of the next card section.
                 if '<div class="glass-card p-6 bg-accent-gradient/5">' in lines[i] or '<!-- Macro Analysis -->' in lines[i]:
                     break
                 i += 1
            continue
            
        new_lines.append(line)
        i += 1

    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("SUCCESS: ETF container emptied and sanitized.")

except Exception as e:
    print(f"ERROR: {e}")
