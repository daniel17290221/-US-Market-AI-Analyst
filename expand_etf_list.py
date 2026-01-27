
import os
import re

path = r'c:\Users\mjang\Downloads\미국 종목 분석\templates\index.html'

try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Expand items to 10 in JS
    new_render_function = """
        function renderETFFlows() {
            const container = document.getElementById('etf-flow-container');
            if (!container) return;

            // Filter data based on flow_score (Inflow >= 55, Outflow < 55)
            let filtered = etfFlowData.filter(d => {
                const score = parseFloat(d.flow_score);
                return currentETFFlowType === 'inflow' ? score >= 55 : score < 55;
            });

            // Sort by flow score
            filtered.sort((a, b) => currentETFFlowType === 'inflow' ? b.flow_score - a.flow_score : a.flow_score - b.flow_score);

            // Increased slice from 5 to 10 for more info
            container.innerHTML = filtered.slice(0, 10).map(item => `
                <div class="flex items-center justify-between p-2 hover:bg-white/5 rounded-lg transition group border-b border-white/[0.02]">
                    <div class="flex-1">
                        <div class="flex items-center gap-2">
                            <span class="text-sm font-bold text-white">${item.ticker}</span>
                            <span class="text-[9px] text-gray-500 uppercase tracking-tighter">${item.category || ''}</span>
                        </div>
                        <div class="flex gap-3 mt-1 text-[11px] font-mono">
                            <span class="${item.flow_score >= 55 ? 'text-brand-success' : 'text-brand-danger'} font-bold">
                                ${item.flow_score >= 55 ? 'IN' : 'OUT'} ${item.flow_score}
                            </span>
                            <span class="text-gray-400">$${item.current_price || '--'}</span>
                        </div>
                    </div>
                    <div class="text-right">
                         <span class="text-[11px] ${item.price_change_20d >= 0 ? 'text-brand-success' : 'text-brand-danger'} font-bold font-mono">
                            ${item.price_change_20d >= 0 ? '+' : ''}${item.price_change_20d}%
                         </span>
                         <p class="text-[8px] text-gray-600">20D Trend</p>
                    </div>
                </div>
            `).join('');
            
            if (filtered.length === 0) {
                container.innerHTML = '<p class="text-xs text-center text-gray-600 py-6 italic border border-dashed border-white/10 rounded-xl">동기화된 데이터가 없습니다.</p>';
            }
        }
"""
    
    # Replace the old render function
    # Pattern to match the whole function
    pattern = r'function renderETFFlows\(\) \{[\s\S]*?\}'
    if re.search(pattern, content):
        content = re.sub(pattern, new_render_function.strip(), content)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("SUCCESS: ETF rendering expanded to Top 10.")
    else:
        print("FAILURE: renderETFFlows function not found.")

except Exception as e:
    print(f"ERROR: {e}")
