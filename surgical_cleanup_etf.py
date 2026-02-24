
import os

path = r'c:\Users\mjang\Downloads\Investment Vibecodinglab\templates\index.html'

try:
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find the start and end indices
    start_idx = -1
    end_idx = -1
    
    for i, line in enumerate(lines):
        if '<!-- ETF Money Flow --><!-- CLEANED -->' in line:
            start_idx = i
        # The card ends after the last DIA item (around line 721)
        # We look for the closing of the space-y-3 and the glass-card
        if start_idx != -1 and 'id="etf-flow-container"' in line:
            # We found the container, now find the closing of the card
            # Looking at the file, the next thing is <!-- Close Right Column --> or similar
            pass
            
    # Based on view_file:
    # 721:                                     </div>
    # 722:                         </div>
    # 723:                     </div>

    # I'll look for the first </div></div> after the start_idx that matches the structure.
    # Actually, I'll just use the line numbers from the last view_file (574 to 723)
    # But since previous edits changed line numbers, I'll be careful.
    
    new_sidebar_card = """                    <!-- ETF Money Flow --><!-- CLEANED -->
                    <div class="glass-card p-6">
                        <div class="flex justify-between items-center mb-4">
                            <h2 class="text-base font-bold uppercase text-gray-400 tracking-wider">ETF 자금 흐름</h2>
                            <div class="flex gap-2 text-xs" id="etf-toggle-buttons">
                                <button onclick="setETFFlowType('inflow')" id="etf-btn-inflow"
                                    class="px-3 py-1.5 bg-brand-primary/20 text-brand-primary rounded font-bold transition">유입</button>
                                <button onclick="setETFFlowType('outflow')" id="etf-btn-outflow"
                                    class="px-3 py-1.5 bg-gray-800 text-gray-400 rounded transition">유출</button>
                            </div>
                        </div>
                        <div class="space-y-3" id="etf-flow-container">
                            <p class="text-xs text-center text-gray-600 py-4 italic">데이터 동기화 중...</p>
                        </div>
                    </div>
"""

    # Better logic: find <!-- ETF Money Flow --><!-- CLEANED -->
    # Then find the first occurrence of '<div class="glass-card p-6 bg-accent-gradient/5">' which is the Macro section.
    # The stuff in between (minus some closings) is the ETF section.
    
    content = "".join(lines)
    marker = '<!-- ETF Money Flow --><!-- CLEANED -->'
    next_section = '<!-- Macro Analysis -->'
    
    if marker in content and next_section in content:
        parts = content.split(marker)
        rest = parts[1].split(next_section)
        
        # We need to preserve the closing divs for the column
        # The ETF card is inside a column.
        # Structure: <div class="col-span-12 lg:col-span-4 space-y-6"> <ETF CARD> </div>
        
        new_content = parts[0] + marker + "\n" + new_sidebar_card + "\n\n                    " + next_section + rest[1]
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("SUCCESS: Sidebar cleaned surgically.")
    else:
        print(f"FAILURE: Marker ({marker in content}) or Next Section ({next_section in content}) not found.")

except Exception as e:
    print(f"ERROR: {e}")
