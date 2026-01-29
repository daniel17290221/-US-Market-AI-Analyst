
import os
import re

path = r'c:\Users\mjang\Downloads\Investment Vibecodinglab\templates\index.html'

try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update the HTML structure for ETF Flows
    etf_html_old = """                    <!-- ETF Money Flow -->
                    <div class="glass-card p-6">
                        <div class="flex justify-between items-center mb-4">
                            <h2 class="text-base font-bold uppercase text-gray-400 tracking-wider">ETF 자금 흐름</h2>
                            <div class="flex gap-2 text-xs">
                                <button
                                    class="px-3 py-1.5 bg-brand-primary/20 text-brand-primary rounded font-bold">유입</button>
                                <button class="px-3 py-1.5 bg-gray-800 text-gray-400 rounded">유출</button>
                            </div>
                        </div>

                        <div class="space-y-3">
                            <!-- ETF Flow Item -->"""
    
    etf_html_new = """                    <!-- ETF Money Flow -->
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
                            <!-- ETF Flow Items will be injected here -->"""

    # Replace the old HTML block (including the static items)
    # We need to find the whole block until the closing div of the container
    etf_section_pattern = r'<!-- ETF Money Flow -->[\s\S]*?<div class="space-y-3">[\s\S]*?<!-- ETF Flow Item -->[\s\S]*?</div>\s*</div>\s*</div>'
    
    # Let's be more surgical with the replacement
    content = content.replace(etf_html_old, etf_html_new)
    
    # Remove the hardcoded items (they are between the new etf-flow-container and the next section)
    # The next section starts with <!-- Close Right Column --> usually or just the end of the script
    # Looking at step 1061, it ends around line 650.
    
    # 2. Add ETF JS logic
    etf_js = """
        // --- ETF Flow Data ---
        let etfFlowData = [];
        let currentETFFlowType = 'inflow';

        async function fetchETFFlows() {
            try {
                console.log("🔍 Fetching ETF Flow data...");
                const response = await fetch(`/api/us/etf-flows?t=${Date.now()}`);
                if (!response.ok) throw new Error('ETF flow API error');
                etfFlowData = await response.json();
                console.log("📦 ETF Flow Data:", etfFlowData);
                renderETFFlows();
                
                // Real-time sync for ETF prices too
                syncETFPrices();
            } catch (e) {
                console.warn("⚠️ ETF Flow fallback:", e.message);
            }
        }

        async function syncETFPrices() {
            if (etfFlowData.length === 0) return;
            const tickers = etfFlowData.map(d => d.ticker).join(',');
            try {
                const response = await fetch(`/api/us/realtime-prices?tickers=${tickers}`);
                if (!response.ok) return;
                const priceData = await response.json();
                etfFlowData.forEach(item => {
                    if (priceData[item.ticker]) {
                        item.current_price = priceData[item.ticker].price;
                    }
                });
                renderETFFlows();
            } catch (e) {}
        }

        function setETFFlowType(type) {
            currentETFFlowType = type;
            // Update UI buttons
            const inBtn = document.getElementById('etf-btn-inflow');
            const outBtn = document.getElementById('etf-btn-outflow');
            if (type === 'inflow') {
                inBtn.classList.add('bg-brand-primary/20', 'text-brand-primary', 'font-bold');
                inBtn.classList.remove('bg-gray-800', 'text-gray-400');
                outBtn.classList.add('bg-gray-800', 'text-gray-400');
                outBtn.classList.remove('bg-brand-primary/20', 'text-brand-primary', 'font-bold');
            } else {
                outBtn.classList.add('bg-brand-primary/20', 'text-brand-primary', 'font-bold');
                outBtn.classList.remove('bg-gray-800', 'text-gray-400');
                inBtn.classList.add('bg-gray-800', 'text-gray-400');
                inBtn.classList.remove('bg-brand-primary/20', 'text-brand-primary', 'font-bold');
            }
            renderETFFlows();
        }

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

            container.innerHTML = filtered.slice(0, 5).map(item => `
                <div class="flex items-center justify-between p-2 hover:bg-white/5 rounded-lg transition group">
                    <div class="flex-1">
                        <div class="flex items-center gap-2">
                            <span class="text-sm font-bold text-white">${item.ticker}</span>
                            <span class="text-[10px] text-gray-500">${item.name || ''}</span>
                        </div>
                        <div class="flex gap-3 mt-1 text-[11px] font-mono">
                            <span class="${item.flow_score >= 55 ? 'text-brand-success' : 'text-brand-danger'}">
                                ${item.flow_score >= 55 ? '유입' : '유출'} Score: ${item.flow_score}
                            </span>
                            <span class="text-gray-400">$${item.current_price || '--'}</span>
                        </div>
                    </div>
                    <div class="text-right">
                         <span class="text-[10px] ${item.price_change_20d >= 0 ? 'text-brand-success' : 'text-brand-danger'} font-bold">
                            ${item.price_change_20d >= 0 ? '+' : ''}${item.price_change_20d}%
                         </span>
                    </div>
                </div>
            `).join('');
            
            if (filtered.length === 0) {
                container.innerHTML = '<p class="text-xs text-center text-gray-600 py-4">데이터가 없습니다.</p>';
            }
        }
"""

    # Insert JS before the end of the script tag or near other fetch functions
    # Using the Macro & Calendar marker as an anchor
    js_anchor = "// --- Macro & Calendar Data (Dynamic for Vercel) ---"
    if js_anchor in content:
        content = content.replace(js_anchor, etf_js + "\n\n        " + js_anchor)
    
    # 3. Add to init
    init_anchor = "fetchCalendarData();"
    if init_anchor in content:
        content = content.replace(init_anchor, init_anchor + "\n            fetchETFFlows();")

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: ETF Flow UI and JS integrated.")

except Exception as e:
    print(f"ERROR: {e}")
