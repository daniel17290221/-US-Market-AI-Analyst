
import os
import re

path = r'c:\Users\mjang\Downloads\Investment Vibecodinglab\templates\index.html'

try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # The goal is to have a clean Sidebar (Right Column)
    # Market Heatmap (516) -> Macro (518) -> Calendar (552) -> ETF (574)
    # The current state is messy around 588.
    
    # I will replace the block from <!-- ETF Money Flow --> to the end of the col-span-4 div.
    # Looking at the code, it ends before "<!-- Placeholder Tabs -->"
    
    clean_etf_section = """
                    <!-- ETF Money Flow (Dynamic) -->
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
                            <p class="text-xs text-center text-gray-600 py-4">데이터 동기화 중...</p>
                        </div>
                    </div>
                </div> <!-- Close Right Column -->
"""

    # Identify the messy range.
    # From <!-- ETF Money Flow --><!-- CLEANED --> (line 574)
    # To the end of the sidebar before <!-- Placeholder Tabs --> (around line 722)
    
    pattern = r'<!-- ETF Money Flow --><!-- CLEANED -->[\s\S]*?(?=<!-- Placeholder Tabs)'
    
    if re.search(pattern, content):
        new_content = re.sub(pattern, clean_etf_section + "\n        " , content)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("SUCCESS: ETF Section and Sidebar structure fixed.")
    else:
        print("FAILURE: Sidebar range not found.")

except Exception as e:
    print(f"ERROR: {e}")
