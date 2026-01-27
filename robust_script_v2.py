
import os
import re

path = r'c:\Users\mjang\Downloads\미국 종목 분석\templates\index.html'

robust_script = """
    <script>
        // --- State Management ---
        const state = {
            currentTab: 'market',
            symbols: {
                'SPY': { price: 5842.10, change: 0.52 },
                'QQQ': { price: 18650.32, change: 1.12 },
                'BTC': { price: 86500.00, change: 4.25 },
            },
            chartData: []
        };

        // --- Tab Navigation ---
        function switchTab(tabId) {
            state.currentTab = tabId;
            document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
            const target = document.getElementById(`tab-${tabId}`);
            if (target) target.classList.remove('hidden');

            document.querySelectorAll('nav a').forEach(a => {
                a.classList.remove('tab-active');
                a.classList.add('tab-inactive');
            });
            const activeLink = document.querySelector(`nav a[onclick*="${tabId}"]`);
            if (activeLink) {
                activeLink.classList.remove('tab-inactive');
                activeLink.classList.add('tab-active');
            }
        }

        // --- UI Injections (Smart Money) ---
        const smartMoneyData = [];

        async function loadSymbol(index) {
            const data = smartMoneyData[index];
            if (!data) return;

            updateTradingView('D', data.ticker);

            try {
                const priceRes = await fetch(`/api/us/realtime-prices?tickers=${data.ticker}`);
                if (priceRes.ok) {
                    const priceData = await priceRes.json();
                    if (priceData[data.ticker]) {
                        data.price = priceData[data.ticker].price;
                        document.getElementById('current-price-label').innerText = `$${data.price}`;
                    }
                }
            } catch (e) {
                console.warn("Real-time price error for symbol:", data.ticker);
            }

            document.getElementById('main-ticker-name').innerText = data.ticker;
            document.getElementById('main-full-name').innerText = data.name;

            const scorePill = document.getElementById('ai-score-pill');
            if (scorePill) {
                scorePill.innerText = `점수: ${data.score} / 100`;
                scorePill.className = `score-pill ${data.score > 80 ? 'score-high' : 'score-mid'}`;
            }

            const signalPill = document.getElementById('ai-signal-pill');
            if (signalPill) {
                signalPill.innerText = `AI ${data.signal}`;
                signalPill.className = `score-pill ${data.signal.includes('적극') ? 'text-brand-success bg-brand-success/10 border-brand-success/30' : 'text-brand-primary bg-brand-primary/10 border-brand-primary/30'} border`;
            }

            const elements = {
                'detail-mkt-cap': data.mkt_cap,
                'detail-vol-ratio': data.vol_ratio,
                'detail-rsi': data.rsi,
                'detail-score': data.score,
                'detail-signal-strength': data.signal_strength,
                'ai-insight': data.insight,
                'ai-risk': data.risk,
                'ai-upside': `${data.upside} 상승 여력`,
                'swot-s': data.swot_s,
                'swot-w': data.swot_w,
                'swot-o': data.swot_o,
                'swot-t': data.swot_t,
                'dcf-target': data.dcf_target,
                'dcf-bear': data.dcf_bear,
                'dcf-bull': data.dcf_bull,
                'sce-bear-val': data.sce_bear_val,
                'sce-bear-pct': data.sce_bear_pct,
                'sce-base-val': data.sce_base_val,
                'sce-base-pct': data.sce_base_pct,
                'sce-bull-val': data.sce_bull_val,
                'sce-bull-pct': data.sce_bull_pct
            };

            for (const [id, val] of Object.entries(elements)) {
                const el = document.getElementById(id);
                if (el) el.innerText = val || '-';
            }

            if (data.dcf_bear && data.dcf_bull) {
                const bear = parseFloat(data.dcf_bear.toString().replace('$', ''));
                const bull = parseFloat(data.dcf_bull.toString().replace('$', ''));
                if (!isNaN(bear) && !isNaN(bull) && bull > bear) {
                    const pos = ((data.price - bear) / (bull - bear)) * 100;
                    const marker = document.getElementById('price-marker');
                    if (marker) marker.style.left = `${Math.min(Math.max(pos, 5), 95)}%`;
                }
            }

            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        function injectSmartMoney() {
            const tbody = document.getElementById('smart-money-tbody');
            if (!tbody) return;
            if (smartMoneyData.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="px-6 py-12 text-center text-gray-500 italic">데이터를 불러오는 중이거나 분석된 종목이 없습니다.</td></tr>';
                return;
            }
            tbody.innerHTML = smartMoneyData.map((item, index) => `
                <tr onclick="loadSymbol(${index})" class="border-b border-white/5 hover:bg-white/5 transition group cursor-pointer">
                    <td class="px-6 py-4 font-mono text-gray-600">${item.rank}</td>
                    <td class="px-6 py-4 font-bold text-white group-hover:text-brand-primary">${item.ticker}</td>
                    <td class="px-6 py-4 text-gray-400">${item.sector}</td>
                    <td class="px-6 py-4"><span class="score-pill ${item.score > 80 ? 'score-high' : 'score-mid'}">${item.score}</span></td>
                    <td class="px-6 py-4 font-bold ${item.signal.includes('적극') ? 'text-brand-success' : 'text-brand-primary'}">${item.signal}</td>
                    <td class="px-6 py-4 text-right font-mono">$${item.price}</td>
                    <td class="px-6 py-4 text-right font-mono ${item.change >= 0 ? 'text-brand-success' : 'text-brand-danger'}">${item.change > 0 ? '+' : ''}${item.change}%</td>
                </tr>
            `).join('');
        }

        let currentTicker = "NASDAQ:NVDA";

        function updateTradingView(resolution = 'D', ticker = null) {
            if (ticker) {
                const prefix = ['NVDA', 'GEHC', 'TSLA', 'AAPL', 'MSFT', 'AVGO', 'META', 'AMZN', 'GOOGL', 'AMD'].includes(ticker) ? 'NASDAQ:' : 'NYSE:';
                currentTicker = prefix + ticker;
            }
            const container = document.getElementById('tradingview_main');
            if (!container) return;
            container.innerHTML = '';
            new TradingView.widget({
                "autosize": true,
                "symbol": currentTicker,
                "interval": resolution,
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1",
                "locale": "kr",
                "toolbar_bg": "#f1f3f6",
                "enable_publishing": false,
                "hide_top_toolbar": false,
                "allow_symbol_change": true,
                "container_id": "tradingview_main"
            });
        }

        async function fetchData() {
            try {
                console.log("🔍 Fetching Smart Money data...");
                const response = await fetch(`/api/us/smart-money?t=${Date.now()}`);
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

                const remoteData = await response.json();
                const now = new Date();
                const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;

                const updateEl = document.querySelector('.text-[10px].text-gray-500.font-mono');
                if (updateEl) {
                    updateEl.innerHTML = `<span class="inline-block w-2 h-2 bg-brand-success rounded-full animate-pulse"></span> VERCEL LIVE API v3.1 (Sync Path: ${timeStr})`;
                }

                if (remoteData && Array.isArray(remoteData) && remoteData.length > 0) {
                    smartMoneyData.length = 0;
                    remoteData.forEach((item, i) => {
                        const price = parseFloat(item.price || item.current_price) || 0;
                        const score = parseFloat(item.composite_score || item.score) || 0;
                        smartMoneyData.push({
                            rank: (i + 1).toString().padStart(2, '0'),
                            ticker: item.ticker || 'N/A',
                            name: item.name || item.ticker,
                            sector: item.sector || '기타',
                            score: score,
                            signal: item.grade ? item.grade.split(' ')[1] : (score > 80 ? '적극 매수' : '매수'),
                            price: price,
                            change: parseFloat(item.change) || 0.0,
                            insight: item.insight || '분석 중...', risk: item.risk || '리스크 점검 중.', 
                            upside: item.upside || '+0%', mkt_cap: item.mkt_cap || 'N/A', 
                            vol_ratio: item.vol_ratio || '1.0x', rsi: item.rsi || '50.0', 
                            signal_strength: score > 80 ? '강력' : '보통',
                            swot_s: item.swot_s || '-', swot_w: item.swot_w || '-',
                            swot_o: item.swot_o || '-', swot_t: item.swot_t || '-',
                            dcf_target: item.dcf_target || `$${(price * 1.1).toFixed(2)}`,
                            dcf_bear: item.dcf_bear || `$${(price * 0.9).toFixed(2)}`,
                            dcf_bull: item.dcf_bull || `$${(price * 1.3).toFixed(2)}`,
                            sce_bear_val: item.sce_bear_val || `$${(price * 0.9).toFixed(2)}`,
                            sce_bear_pct: '-10%', sce_base_val: item.sce_base_val || `$${(price * 1.1).toFixed(2)}`,
                            sce_base_pct: '+10%', sce_bull_val: item.sce_bull_val || `$${(price * 1.3).toFixed(2)}`,
                            sce_bull_pct: '+30%'
                        });
                    });
                    syncRealtimePrices();
                } else {
                    applyFallbackData();
                }
            } catch (e) {
                console.error("❌ Smart Money fetch failed:", e);
                if (smartMoneyData.length === 0) applyFallbackData();
            } finally {
                injectSmartMoney();
                if (!window.initialLoadDone && smartMoneyData.length > 0) {
                    loadSymbol(0);
                    window.initialLoadDone = true;
                }
            }
        }

        async function syncRealtimePrices() {
            if (smartMoneyData.length === 0) return;
            const tickers = smartMoneyData.map(d => d.ticker).join(',');
            try {
                const response = await fetch(`/api/us/realtime-prices?tickers=${tickers}`);
                if (response.ok) {
                    const priceData = await response.json();
                    let updated = false;
                    smartMoneyData.forEach(item => {
                        if (priceData[item.ticker]) {
                            item.price = priceData[item.ticker].price;
                            item.change = priceData[item.ticker].change;
                            updated = true;
                        }
                    });
                    if (updated) injectSmartMoney();
                }
            } catch (e) {}
        }

        function applyFallbackData() {
            const backupData = [
                { rank: "01", ticker: "NVDA", name: "NVIDIA Corporation", sector: "Technology", score: 96.5, signal: "적극 매수", price: 143.00, change: 8.5 },
                { rank: "02", ticker: "TSLA", name: "Tesla, Inc.", sector: "Automotive", score: 92.0, signal: "적극 매수", price: 259.00, change: 3.2 },
                { rank: "03", ticker: "AAPL", name: "Apple Inc.", sector: "Technology", score: 89.0, signal: "적극 매수", price: 228.50, change: 1.3 },
                { rank: "04", ticker: "MSFT", name: "Microsoft Corp", sector: "Software", score: 83.0, signal: "적극 매수", price: 426.00, change: 1.0 },
                { rank: "05", ticker: "AMZN", name: "Amazon.com", sector: "Commerce", score: 79.0, signal: "매수", price: 189.00, change: 0.6 },
                { rank: "06", ticker: "META", name: "Meta Platforms", sector: "Technology", score: 78.0, signal: "매수", price: 586.00, change: 1.5 },
                { rank: "07", ticker: "GOOGL", name: "Alphabet Inc", sector: "Technology", score: 77.0, signal: "매수", price: 166.00, change: 0.1 },
                { rank: "08", ticker: "AVGO", "name": "Broadcom Inc", sector: "Semiconductors", score: 75.8, signal: "매수", price: 172.50, change: 2.1 },
                { rank: "09", ticker: "AMD", "name": "Advanced Micro", sector: "Semiconductors", score: 74.2, signal: "매수", price: 155.10, change: -2.3 },
                { rank: "10", ticker: "COST", "name": "Costco Wholesale", sector: "Retail", score: 73.5, signal: "관망", price: 912.45, change: 0.8 }
            ];
            smartMoneyData.length = 0;
            backupData.forEach(item => {
                smartMoneyData.push({
                    ...item, insight: "동기화 모드.", risk: "양호.", upside: "+15%",
                    mkt_cap: "N/A", vol_ratio: "1.0x", rsi: "50", signal_strength: "보통",
                    swot_s: "-", swot_w: "-", swot_o: "-", swot_t: "-",
                    dcf_target: `$${(item.price * 1.1).toFixed(2)}`, dcf_bear: `$${(item.price * 0.9).toFixed(2)}`,
                    dcf_bull: `$${(item.price * 1.2).toFixed(2)}`, sce_bear_val: `$${(item.price * 0.9).toFixed(2)}`,
                    sce_bear_pct: '-10%', sce_base_val: `$${(item.price * 1.1).toFixed(2)}`,
                    sce_base_pct: '+10%', sce_bull_val: `$${(item.price * 1.2).toFixed(2)}`,
                    sce_bull_pct: '+20%'
                });
            });
            injectSmartMoney();
            syncRealtimePrices();
        }

        // --- ETF Flow Data ---
        let etfFlowData = [];
        let currentETFFlowType = 'inflow';

        async function fetchETFFlows() {
            try {
                console.log("🔍 Fetching ETF flows...");
                const response = await fetch(`/api/us/etf-flows?t=${Date.now()}`);
                if (response.ok) {
                    etfFlowData = await response.json();
                } else {
                    console.warn("ETF API returned error status");
                }
            } catch (e) {
                console.error("ETF Flow fetch failure:", e);
            } finally {
                renderETFFlows();
                syncETFPrices();
            }
        }

        async function syncETFPrices() {
            if (etfFlowData.length === 0) return;
            const tickers = etfFlowData.map(d => d.ticker).join(',');
            try {
                const response = await fetch(`/api/us/realtime-prices?tickers=${tickers}`);
                if (response.ok) {
                    const priceData = await response.json();
                    etfFlowData.forEach(item => {
                        if (priceData[item.ticker]) {
                            item.current_price = priceData[item.ticker].price;
                        }
                    });
                    renderETFFlows();
                }
            } catch (e) {}
        }

        function setETFFlowType(type) {
            currentETFFlowType = type;
            const inBtn = document.getElementById('etf-btn-inflow');
            const outBtn = document.getElementById('etf-btn-outflow');
            if (inBtn && outBtn) {
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
            }
            renderETFFlows();
        }

        function renderETFFlows() {
            const container = document.getElementById('etf-flow-container');
            if (!container) return;
            
            let filtered = etfFlowData.filter(d => {
                const score = parseFloat(d.flow_score);
                return currentETFFlowType === 'inflow' ? score >= 55 : score < 55;
            });
            filtered.sort((a, b) => currentETFFlowType === 'inflow' ? b.flow_score - a.flow_score : a.flow_score - b.flow_score);
            
            if (filtered.length === 0) {
                container.innerHTML = '<p class="text-xs text-center text-gray-600 py-6 italic border border-dashed border-white/10 rounded-xl">데이터가 없습니다.</p>';
                return;
            }

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
        }

        async function fetchMacroData() {
            try {
                const response = await fetch(`/api/us/macro-analysis?t=${Date.now()}`);
                if (response.ok) {
                    const data = await response.json();
                    const sentEl = document.getElementById('macro-sentiment');
                    const summEl = document.getElementById('macro-summary');
                    const takeEl = document.getElementById('macro-takeaways');
                    const outEl = document.getElementById('macro-outlook');
                    const riskEl = document.getElementById('macro-risk');
                    
                    if (sentEl) sentEl.innerText = `${data.market_mood} (${data.mood_score})`;
                    if (summEl) summEl.innerText = `현재 시장은 ${data.market_mood} 단계를 보이고 있습니다.`;
                    if (takeEl) takeEl.innerHTML = (data.key_takeaways || []).map(t => `<li class="flex items-center gap-2"><div class="w-1.5 h-1.5 rounded-full bg-brand-primary"></div>${t}</li>`).join('');
                    if (outEl) outEl.innerText = `전망: ${data.sector_outlook}`;
                    if (riskEl) riskEl.innerText = `리스크: ${data.risk_factors}`;
                }
            } catch (e) {}
        }

        async function fetchCalendarData() {
            try {
                const response = await fetch(`/api/us/economic-calendar?t=${Date.now()}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.events && data.events.length > 0) {
                        const miniList = document.getElementById('calendar-mini-list');
                        if (miniList) {
                            miniList.innerHTML = data.events.slice(0, 3).map(ev => `
                                <div class="flex justify-between items-start group cursor-pointer p-2 hover:bg-white/5 rounded-lg transition">
                                    <div>
                                        <h4 class="text-sm font-bold group-hover:text-brand-primary">${ev.event}</h4>
                                        <p class="text-[10px] text-gray-500 font-mono">${ev.date} ${ev.time}</p>
                                    </div>
                                    <div class="text-right">
                                        <span class="bg-${ev.impact === 'High' ? 'brand-danger' : 'brand-primary'}/10 text-${ev.impact === 'High' ? 'brand-danger' : 'brand-primary'} text-[10px] font-bold px-2 py-0.5 rounded border border-${ev.impact === 'High' ? 'brand-danger' : 'brand-primary'}/30">${ev.impact}</span>
                                        <p class="text-[10px] text-gray-500 mt-1 font-mono">Fcst: ${ev.forecast}</p>
                                    </div>
                                </div>
                            `).join('');
                        }
                    }
                }
            } catch (e) {}
        }

        document.addEventListener('DOMContentLoaded', () => {
            fetchData();
            fetchMacroData();
            fetchCalendarData();
            fetchETFFlows();
            setInterval(fetchData, 5 * 60 * 1000);
            console.log("🚀 Premium Dashboard Restored");
        });
    </script>
"""

try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replacement with ultra-safety
    pattern = r'<script>\s*// --- State Management ---[\s\S]*?</script>'
    
    if re.search(pattern, content):
        new_content = re.sub(pattern, robust_script, content)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("SUCCESS: Robust script deployed.")
    else:
        print("FAILURE: Script block not found.")

except Exception as e:
    print(f"ERROR: {e}")
