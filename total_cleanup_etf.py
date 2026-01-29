
import os
import re

path = r'c:\Users\mjang\Downloads\Investment Vibecodinglab\templates\index.html'

try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Surgical purge of static items inside etf-flow-container
    # Pattern: match from id="etf-flow-container"> until the next section's close div
    # Re-reading the file view from 1102:
    # 586:  <div class="space-y-3" id="etf-flow-container">
    # 587:      <!-- ETF Flow Items will be injected here -->
    # 588:      <div ... (SPY)
    
    # I want to keep the container div but clear its contents.
    pattern = r'(<div class="space-y-3" id="etf-flow-container">)[\s\S]*?(?=</div>\s*</div>\s*</div>\s*<!-- Macro Analysis -->)'
    # Wait, Macro analysis is the NEXT section.
    
    # Looking at the full structure:
    # <div class="glass-card p-6"> ... etf ... </div>
    # </div> <!-- Close Right Column -->
    
    # Let's find the specific static items.
    static_items_pattern = r'<!-- ETF Flow Items will be injected here -->[\s\S]*?(?=</div>\s*</div>\s*</div>\s*<!-- Macro Analysis -->|</div>\s*</div>\s*<!-- Macro Analysis -->)'
    # If Macro analysis doesn't follow, then it's etc.
    
    # I'll just look for the first 5 SPY, QQQ, VOO, VTI, XLK blocks and remove them.
    for ticker_to_kill in ["SPY", "QQQ", "VOO", "VTI", "XLK", "BND"]:
        ticker_pattern = rf'<div[^>]*>[\s\S]*?{ticker_to_kill}[\s\S]*?</div>\s*</div>\s*</div>'
        # Actually SPY block is very specific.
        
    # Definitive approach: Replace the whole ETF sidebar card again with a fresh clean one.
    sidebar_etf_block = """                    <!-- ETF Money Flow --><!-- CLEANED -->
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
                    </div>"""
    
    # Find the range from <!-- ETF Money Flow --> to the end of the card
    current_etf_section_pattern = r'<!-- ETF Money Flow -->[\s\S]*?(?=<!-- Macro Analysis -->|<div class="glass-card p-6 bg-accent-gradient/5">)'
    
    if re.search(current_etf_section_pattern, content):
        content = re.sub(current_etf_section_pattern, sidebar_etf_block + "\n\n                    ", content)
        print("SUCCESS: sidebar ETF card fully cleaned and dynamicized.")
    else:
        print("FAILURE: Could not isolate sidebar ETF card for replacement.")

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

except Exception as e:
    print(f"ERROR: {e}")
