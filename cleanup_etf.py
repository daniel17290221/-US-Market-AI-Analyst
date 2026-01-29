
import os
import re

path = r'c:\Users\mjang\Downloads\Investment Vibecodinglab\templates\index.html'

try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Clean up the ETF Flow container
    # We want to replace everything from the start of the section to the end of the container
    start_tag = '<!-- ETF Money Flow -->'
    # Find the next section start to know where to stop cleaning
    end_tag = '</div>\r\n\r\n                </div> <!-- Close Right Column -->'
    if end_tag not in content:
        end_tag = '</div>\n\n                </div> <!-- Close Right Column -->'

    if start_tag in content:
        parts = content.split(start_tag)
        # The remainder contains the whole right column
        rest = parts[1]
        
        # New clean section
        new_section = """
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
                            <p class="text-xs text-center text-gray-600 py-4 italic">데이터를 동기화 중입니다...</p>
                        </div>
                    </div>
"""
        # Find where the Right Column actually ends to preserve it
        # We need to find the balance of divs or use a marker
        
        # Looking at the file, after the ETF flows there is the closing of col-span-4
        # Let's try to find the last item's closing and the container's closing.
        # The static list ended with a bunch of divs.
        
        # Alternative: use regex to replace from start_tag to the first occurrence of "</div>\s*</div>\s*</div>" 
        # which usually closes the card, sidebar section, and main container part.
        
        # Actually, I'll just look for the start of the next section if there was one, 
        # but ETF flow is the LAST thing in the sidebar.
        
        pattern = re.escape(start_tag) + r'[\s\S]*?(?=\s*</div>\s*</div>\s*<!-- Close Right Column -->)'
        if re.search(pattern, content):
            content = re.sub(pattern, start_tag + new_section, content)
            print("SUCCESS: Static ETF items removed.")
        else:
            # Fallback search
            content = content.replace(start_tag, start_tag + "<!-- CLEANED -->")
            print("WARNING: Could not find end pattern, partial update applied.")

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

except Exception as e:
    print(f"ERROR: {e}")
