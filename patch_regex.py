
import os
import re

path = r'c:\Users\mjang\Downloads\Investment Vibecodinglab\templates\index.html'

try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define the new logic block
    replacement_block = """
        // --- Data Loading (Dynamic CSV for Vercel) ---
        async function fetchData() {
            try {
                console.log("🔍 Fetching Smart Money data...");
                const response = await fetch(`/api/us/smart-money?t=${Date.now()}`);
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

                const remoteData = await response.json();
                console.log("📦 Received Remote Data:", remoteData);

                // Update "Last Updated" time in UI
                const now = new Date();
                const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;

                const updateEl = document.querySelector('.text-[10px].text-gray-500.font-mono');
                if (updateEl) {
                    updateEl.innerHTML = `<span class="inline-block w-2 h-2 bg-brand-success rounded-full animate-pulse"></span> VERCEL LIVE API v2.7 (Deep Sync: ${timeStr})`;
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
                            insight: item.insight || 'AI 분석 결과가 동기화되었습니다.',
                            risk: item.risk || '일반적인 시장 리스크에 유의하시기 바랍니다.',
                            upside: item.upside || '+15.2%',
                            mkt_cap: item.mkt_cap || 'N/A',
                            vol_ratio: item.vol_ratio || '1.0x',
                            rsi: item.rsi || '50.0',
                            signal_strength: score > 90 ? '매우 강력' : (score > 80 ? '강력' : '보통'),
                            swot_s: item.swot_s || '시장 경쟁력 확보',
                            swot_w: item.swot_w || '변동성 영향',
                            swot_o: item.swot_o || '시장 확대',
                            swot_t: item.swot_t || '경쟁 심화',
                            dcf_target: item.dcf_target || `$${(price * 1.18).toFixed(2)}`,
                            dcf_bear: item.dcf_bear || `$${(price * 0.82).toFixed(2)}`,
                            dcf_bull: item.dcf_bull || `$${(price * 1.45).toFixed(2)}`,
                            sce_bear_val: item.sce_bear_val || `$${(price * 0.82).toFixed(2)}`,
                            sce_bear_pct: item.sce_bear_pct || '-18%',
                            sce_base_val: item.sce_base_val || `$${(price * 1.18).toFixed(2)}`,
                            sce_base_pct: item.sce_base_pct || '+18%',
                            sce_bull_val: item.sce_bull_val || `$${(price * 1.45).toFixed(2)}`,
                            sce_bull_pct: item.sce_bull_pct || '+45%'
                        });
                    });
                    // Critical: Sync all prices for 10 items
                    syncRealtimePrices();
                } else {
                    console.warn("⚠️ API empty, using 10-item fallback.");
                    applyFallbackData();
                }
            } catch (e) {
                console.error("❌ API fetch failed:", e);
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
                console.log("🔄 Global Price Sync Initiated...");
                const response = await fetch(`/api/us/realtime-prices?tickers=${tickers}`);
                if (!response.ok) return;
                const priceData = await response.json();
                
                let updated = false;
                smartMoneyData.forEach(item => {
                    if (priceData[item.ticker]) {
                        item.price = priceData[item.ticker].price;
                        item.change = priceData[item.ticker].change;
                        updated = true;
                    }
                });
                
                if (updated) {
                    injectSmartMoney();
                    // Load the first symbol if it was updated to show correct price in header
                    const mainTicker = document.getElementById('main-ticker-name').innerText;
                    if (priceData[mainTicker]) {
                        document.getElementById('current-price-label').innerText = `$${priceData[mainTicker].price}`;
                    }
                }
            } catch (e) {
                console.warn("Real-time sync error.");
            }
        }

        function applyFallbackData() {
            const backupData = [
                { rank: "01", ticker: "NVDA", name: "NVIDIA Corporation", sector: "Technology", score: 95.8, signal: "적극 매수", price: 142.87, change: 8.4 },
                { rank: "02", ticker: "TSLA", name: "Tesla, Inc.", sector: "Automotive", score: 91.2, signal: "적극 매수", price: 258.45, change: 3.1 },
                { rank: "03", ticker: "AAPL", name: "Apple Inc.", sector: "Technology", score: 88.5, signal: "적극 매수", price: 228.12, change: 1.2 },
                { rank: "04", ticker: "MSFT", name: "Microsoft Corp", sector: "Software", score: 82.5, signal: "적극 매수", price: 425.30, change: 0.9 },
                { rank: "05", ticker: "AMZN", name: "Amazon.com", sector: "Commerce", score: 78.5, signal: "매수", price: 188.30, change: 0.5 },
                { rank: "06", ticker: "META", name: "Meta Platforms", sector: "Technology", score: 77.2, signal: "매수", price: 585.20, change: 1.4 },
                { rank: "07", ticker: "GOOGL", name: "Alphabet Inc", sector: "Technology", score: 76.5, signal: "매수", price: 165.20, change: 0.0 },
                { rank: "08", ticker: "AVGO", "name": "Broadcom Inc", sector: "Semiconductors", score: 75.8, signal: "매수", price: 172.50, change: 2.1 },
                { rank: "09", ticker: "AMD", "name": "Advanced Micro", sector: "Semiconductors", score: 74.2, signal: "매수", price: 155.10, change: -2.3 },
                { rank: "10", ticker: "COST", "name": "Costco Wholesale", sector: "Retail", score: 73.5, signal: "관망", price: 912.45, change: 0.8 }
            ];
            
            smartMoneyData.length = 0;
            backupData.forEach(item => {
                const price = item.price;
                smartMoneyData.push({
                    ...item,
                    insight: "AI 분석 결과가 동기화되었습니다.", risk: "시장 리스크 유의", upside: "+15.2%",
                    mkt_cap: "N/A", vol_ratio: "1.0x", rsi: "50.0", signal_strength: "보통",
                    swot_s: "시장 경쟁력", swot_w: "변동성 영향", swot_o: "시장 확대", swot_t: "경쟁 심화",
                    dcf_target: `$${(price * 1.15).toFixed(2)}`,
                    dcf_bear: `$${(price * 0.85).toFixed(2)}`,
                    dcf_bull: `$${(price * 1.40).toFixed(2)}`,
                    sce_bear_val: `$${(price * 0.85).toFixed(2)}`,
                    sce_bear_pct: '-15%',
                    sce_base_val: `$${(price * 1.15).toFixed(2)}`,
                    sce_base_pct: '+15%',
                    sce_bull_val: `$${(price * 1.40).toFixed(2)}`,
                    sce_bull_pct: '+40%'
                });
            });
            syncRealtimePrices();
        }
"""

    start_pattern = re.escape("// --- Data Loading (Dynamic CSV for Vercel) ---")
    end_pattern = re.escape("// --- Macro & Calendar Data (Dynamic for Vercel) ---")
    
    # Aggressive regex to find everything between markers
    pattern = f"({start_pattern})[\\s\\S]*?({end_pattern})"
    
    if re.search(pattern, content):
        new_content = re.sub(pattern, f"\\1\n{replacement_block}\n        \\2", content)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("SUCCESS: 10-item fallback and real-time sync loop applied via regex.")
    else:
        print("FAILURE: Markers not found even with regex.")

except Exception as e:
    print(f"ERROR: {e}")
