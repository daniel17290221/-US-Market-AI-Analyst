
import os

path = r'c:\Users\mjang\Downloads\미국 종목 분석\templates\index.html'

try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Rebuild the entire right column starting from ETF Flow for safety
    sidebar_replacement = """
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
                            <p class="text-xs text-center text-gray-600 py-4 italic">데이터 동기화 중...</p>
                        </div>
                    </div>

                    <!-- Macro Analysis -->
                    <div class="glass-card p-6 bg-accent-gradient/5">
                        <h2 class="text-xl font-bold mb-6 flex items-center gap-2">
                            <i class="fas fa-robot text-brand-primary"></i> AI Macro Outlook
                        </h2>
                        <div class="space-y-6">
                            <div class="flex justify-between items-center p-3 bg-white/5 rounded-lg">
                                <span class="text-gray-400 text-sm">Market Mood</span>
                                <span class="font-bold text-brand-success" id="macro-sentiment">Loading...</span>
                            </div>
                            <div class="space-y-2">
                                <p class="text-xs font-bold text-brand-primary uppercase tracking-widest">Key Takeaways</p>
                                <ul class="space-y-2 text-sm text-gray-300" id="macro-takeaways">
                                    <li class="flex items-center gap-2"><div class="w-1.5 h-1.5 rounded-full bg-brand-primary"></div>분석 중...</li>
                                </ul>
                            </div>
                            <div class="pt-4 border-t border-white/5">
                                <p class="text-sm text-gray-400" id="macro-summary">현재 시장은...</p>
                                <div class="mt-4 p-3 bg-brand-primary/10 rounded-lg border border-brand-primary/20">
                                    <p class="text-xs font-bold text-brand-primary mb-1 uppercase">Sector Outlook</p>
                                    <p class="text-xs text-gray-300" id="macro-outlook">전망 로딩 중...</p>
                                </div>
                                <div class="mt-2 p-3 bg-brand-danger/10 rounded-lg border border-brand-danger/20">
                                    <p class="text-xs font-bold text-brand-danger mb-1 uppercase">Risk Factors</p>
                                    <p class="text-xs text-gray-300" id="macro-risk">리스크 로딩 중...</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div> <!-- Close Right Column -->
"""

    start_marker = '<!-- ETF Money Flow -->'
    # Finding where the right column ends
    end_marker = '</div> <!-- Close Right Column -->'
    
    if start_marker in content and end_marker in content:
        parts = content.split(start_marker)
        # We need everything before the start marker
        head = parts[0]
        # Then everything after the end marker
        rest = parts[1].split(end_marker)
        tail = rest[1]
        
        new_content = head + sidebar_replacement + tail
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("SUCCESS: Sidebar rebuilt and balanced.")
    else:
         # Try with the "CLEANED" marker from previous step
         start_marker = '<!-- ETF Money Flow --><!-- CLEANED -->'
         if start_marker in content and end_marker in content:
            parts = content.split(start_marker)
            head = parts[0]
            rest = parts[1].split(end_marker)
            tail = rest[1]
            new_content = head + sidebar_replacement + tail
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("SUCCESS: Sidebar rebuilt (via CLEANED marker).")
         else:
            print("FAILURE: Structural markers not found.")

except Exception as e:
    print(f"ERROR: {e}")
