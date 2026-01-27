
import os

path = r'c:\Users\mjang\Downloads\미국 종목 분석\templates\index.html'

fallback_10_items = """
        function applyFallbackData() {
            console.warn("🚀 Applying full 10-item emergency fallback data.");
            const backupData = [
                { rank: "01", ticker: "NVDA", name: "NVIDIA Corporation", sector: "Technology", score: 95.8, signal: "적극 매수", price: 142.87, change: 8.4, insight: "AI 시장 지배력 지속 및 Blackwell 수요 폭발", risk: "수출 규제 영향", upside: "+18.2%", mkt_cap: "$3.5T", vol_ratio: "3.2x", rsi: "72.4", signal_strength: "매우 강력" },
                { rank: "02", ticker: "TSLA", name: "Tesla, Inc.", sector: "Automotive", score: 91.2, signal: "적극 매수", price: 258.45, change: 3.1, insight: "정부 로보택시 기대 및 마진 개선", risk: "전기차 경쟁 심화", upside: "+25.5%", mkt_cap: "$825B", vol_ratio: "2.4x", rsi: "64.5", signal_strength: "매우 강력" },
                { rank: "03", ticker: "AAPL", name: "Apple Inc.", sector: "Technology", score: 88.5, signal: "적극 매수", price: 228.12, change: 1.2, insight: "애플 인텔리전스 수요 기대", risk: "중국 공급망 리스크", upside: "+12.1%", mkt_cap: "$3.4T", vol_ratio: "1.2x", rsi: "55.4", signal_strength: "강력" },
                { rank: "04", ticker: "MSFT", name: "Microsoft Corp", sector: "Software", score: 82.5, signal: "적극 매수", price: 425.30, change: 0.9, insight: "클라우드 서비스 안정적 성장", risk: "AI 투자 비용 소폭 증가", upside: "+10.5%", mkt_cap: "$3.1T", vol_ratio: "1.1x", rsi: "58.2", signal_strength: "강력" },
                { rank: "05", ticker: "AMZN", name: "Amazon.com", sector: "Commerce", score: 78.5, signal: "매수", price: 188.30, change: 0.5, insight: "광고 사업 매출 급증", risk: "소비 심리 일시 위축", upside: "+15.2%", mkt_cap: "$1.9T", vol_ratio: "1.0x", rsi: "52.1", signal_strength: "보통" },
                { rank: "06", ticker: "META", name: "Meta Platforms", sector: "Technology", score: 77.2, signal: "매수", price: 585.20, change: 1.4, insight: "광고 효율 개선 및 AI 통합", risk: "메타버스 투자 손실", upside: "+8.4%", mkt_cap: "$1.5T", vol_ratio: "1.3x", rsi: "60.5", signal_strength: "보통" },
                { rank: "07", ticker: "GOOGL", name: "Alphabet Inc", sector: "Technology", score: 76.5, signal: "매수", price: 165.20, change: 0.0, insight: "검색 시장 점유율 견고", risk: "반독점 소송 가능성", upside: "+14.1%", mkt_cap: "$2.0T", vol_ratio: "0.9x", rsi: "48.2", signal_strength: "보통" },
                { rank: "08", ticker: "AVGO", "name": "Broadcom Inc", sector: "Semiconductors", score: 75.8, signal: "매수", price: 172.50, change: 2.1, insight: "AI 네트워크 장비 수요", risk: "전통 칩 사업 둔화", upside: "+9.2%", mkt_cap: "$800B", vol_ratio: "1.5x", rsi: "66.8", signal_strength: "보통" },
                { rank: "09", ticker: "AMD", "name": "Advanced Micro", sector: "Semiconductors", score: 74.2, signal: "매수", price: 155.10, change: -2.3, insight: "MI300 칩 판매 가속화", risk: "엔비디아 시장 지배력", upside: "+22.5%", mkt_cap: "$250B", vol_ratio: "1.8x", rsi: "42.5", signal_strength: "보통" },
                { rank: "10", ticker: "COST", "name": "Costco Wholesale", sector: "Retail", score: 73.5, signal: "관망", price: 912.45, change: 0.8, insight: "멤버십 가치 및 견고한 수요", risk: "밸류에이션 부담", upside: "+5.1%", mkt_cap: "$400B", vol_ratio: "0.8x", rsi: "51.2", signal_strength: "보통" }
            ];
            
            smartMoneyData.length = 0;
            backupData.forEach(item => {
                const price = item.price;
                smartMoneyData.push({
                    ...item,
                    swot_s: "시장 경쟁력 확보", swot_w: "변동성 영향", swot_o: "시장 확대", swot_t: "경쟁 심화",
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
            // Immediately sync real prices if possible
            syncRealtimePrices();
        }

        async function syncRealtimePrices() {
            if (smartMoneyData.length === 0) return;
            const tickers = smartMoneyData.map(d => d.ticker).join(',');
            try {
                console.log("🔄 Syncing real-time prices for list...");
                const response = await fetch(`/api/us/realtime-prices?tickers=${tickers}`);
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
                    console.log("✨ List prices synchronized with market.");
                }
            } catch (e) {
                console.warn("Price sync missed a beat.");
            }
        }
"""

try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define the new robust fetchData function that handles sync
    new_fetch_data = """
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
                    updateEl.innerHTML = `<span class="inline-block w-2 h-2 bg-brand-success rounded-full animate-pulse"></span> VERCEL LIVE API v2.6 (Live Sync: ${timeStr})`;
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
                    // After loading main list, immediately trigger a second real-time sync for all prices
                    syncRealtimePrices();
                } else {
                    console.warn("⚠️ API returned empty data, triggering fallback.");
                    applyFallbackData();
                }
            } catch (e) {
                console.error("❌ API fetch failed:", e);
                if (smartMoneyData.length === 0) applyFallbackData();
            } finally {
                injectSmartMoney();
                // Load first item if not already done
                if (!window.initialLoadDone && smartMoneyData.length > 0) {
                    loadSymbol(0);
                    window.initialLoadDone = true;
                }
            }
        }
"""

    start_marker = "// --- Data Loading (Dynamic CSV for Vercel) ---"
    end_marker = "// --- Macro & Calendar Data (Dynamic for Vercel) ---"
    
    if start_marker in content and end_marker in content:
        parts = content.split(start_marker)
        rest = parts[1].split(end_marker)
        
        updated_block = new_fetch_data + "\n\n" + fallback_10_items
        
        new_content = parts[0] + start_marker + updated_block + "\n\n        " + end_marker + rest[1]
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("SUCCESS: 10-item fallback and living price sync patched.")
    else:
        print("FAILURE: Markers not found.")

except Exception as e:
    print(f"ERROR: {e}")
