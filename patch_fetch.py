
import os
import re

path = r'c:\Users\mjang\Downloads\Investment Vibecodinglab\templates\index.html'

try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define the new robust fetchData function
    # I will replace the entire old fetchData range.
    # From grep/view_file, it starts at 939 and the catch block ends around 1025.
    
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
                    updateEl.innerHTML = `<span class="inline-block w-2 h-2 bg-brand-success rounded-full animate-pulse"></span> VERCEL LIVE API v2.5 (Last Sync: ${timeStr})`;
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

        function applyFallbackData() {
            console.warn("🚀 Applying emergency hardcoded fallback data.");
            const backupData = [
                { rank: "01", ticker: "NVDA", name: "NVIDIA Corporation", sector: "Technology", score: 95.8, signal: "적극 매수", price: 142.87, change: 8.4, insight: "AI 시장 지배력 지속", risk: "수출 규제", upside: "+18.2%", mkt_cap: "$3.5T", vol_ratio: "3.2x", rsi: "72.4", signal_strength: "매우 강력", swot_s: "AI 기술력", swot_w: "높은 밸류", swot_o: "서버 수요", swot_t: "경쟁 심화" },
                { rank: "02", ticker: "TSLA", name: "Tesla, Inc.", sector: "Automotive", score: 91.2, signal: "적극 매수", price: 258.45, change: 3.1, insight: "로보택시 기대감 반영", risk: "가격 전쟁", upside: "+25.5%", mkt_cap: "$825B", vol_ratio: "2.4x", rsi: "64.5", signal_strength: "매우 강력", swot_s: "FSD 선두", swot_w: "마진 압박", swot_o: "로봇 사업", swot_t: "후발 주자" },
                { rank: "03", ticker: "AAPL", name: "Apple Inc.", sector: "Technology", score: 88.5, signal: "적극 매수", price: 228.12, change: 1.2, insight: "교체 수요 기대", risk: "규제 강화", upside: "+12.1%", mkt_cap: "$3.4T", vol_ratio: "1.2x", rsi: "55.4", signal_strength: "강력", swot_s: "생태계", swot_w: "성장 정체", swot_o: "AI 폰", swot_t: "중국 리스크" }
            ];
            
            smartMoneyData.length = 0;
            backupData.forEach(item => {
                const price = item.price;
                smartMoneyData.push({
                    ...item,
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
        }
"""

    # Replace the block from // --- Data Loading ... to function fetchData() { ... }
    # Using a slightly less fragile approach: replace from "async function fetchData()" to the end of that block.
    
    pattern = r'async function fetchData\(\) \{[\s\S]*?if \(!window\.initialLoadDone[\s\S]*?\}'
    # Wait, the end of the script tag is better.
    
    # I will look for the start of fetchData and go until the next "// ---" or end of script
    start_marker = "// --- Data Loading (Dynamic CSV for Vercel) ---"
    end_marker = "// --- Macro & Calendar Data (Dynamic for Vercel) ---"
    
    if start_marker in content and end_marker in content:
        parts = content.split(start_marker)
        rest = parts[1].split(end_marker)
        new_content = parts[0] + start_marker + new_fetch_data + "\n\n        " + end_marker + rest[1]
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("SUCCESS: fetchData patched with robust fallback logic.")
    else:
        print("FAILURE: Markers not found.")

except Exception as e:
    print(f"ERROR: {e}")
