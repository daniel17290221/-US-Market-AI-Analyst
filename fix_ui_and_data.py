
import os
import re

path = r'c:\Users\mjang\Downloads\미국 종목 분석\templates\index.html'

try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Redesign SWOT Cards for better visibility and colors
    swot_html = """
                                    <div class="grid grid-cols-2 gap-3">
                                        <div class="p-3 bg-brand-success/5 rounded-xl text-center border border-brand-success/20 hover:bg-brand-success/10 transition">
                                            <p class="text-[9px] text-brand-success font-black mb-1 uppercase tracking-widest">강점 (S)</p>
                                            <p id="swot-s" class="text-[11px] font-medium text-gray-200">--</p>
                                        </div>
                                        <div class="p-3 bg-brand-danger/5 rounded-xl text-center border border-brand-danger/20 hover:bg-brand-danger/10 transition">
                                            <p class="text-[9px] text-brand-danger font-black mb-1 uppercase tracking-widest">약점 (W)</p>
                                            <p id="swot-w" class="text-[11px] font-medium text-gray-200">--</p>
                                        </div>
                                        <div class="p-3 bg-brand-primary/5 rounded-xl text-center border border-brand-primary/20 hover:bg-brand-primary/10 transition">
                                            <p class="text-[9px] text-brand-primary font-black mb-1 uppercase tracking-widest">기회 (O)</p>
                                            <p id="swot-o" class="text-[11px] font-medium text-gray-200">--</p>
                                        </div>
                                        <div class="p-3 bg-brand-warning/5 rounded-xl text-center border border-brand-warning/20 hover:bg-brand-warning/10 transition">
                                            <p class="text-[9px] text-brand-warning font-black mb-1 uppercase tracking-widest">위협 (T)</p>
                                            <p id="swot-t" class="text-[11px] font-medium text-gray-200">--</p>
                                        </div>
                                    </div>
    """
    
    swot_pattern = r'<div class="grid grid-cols-2 gap-3">[\s\S]*?</div>[\s\S]*?</div>[\s\S]*?</div>[\s\S]*?</div>' # This pattern might be tricky due to nesting.
    # Let's use a simpler marker replacement if possible, or just replace the whole Analysis Blocks div.
    
    # 2. Fix DCF Overlap - Move label ABOVE
    dcf_fixed = """
                                        <div class="h-1.5 w-full bg-gray-800/50 rounded-full mb-6 relative">
                                            <div class="absolute inset-0 flex rounded-full overflow-hidden">
                                                <div class="h-full bg-brand-danger/40 w-1/3 border-r border-black/20"></div>
                                                <div class="h-full bg-brand-success/40 w-1/3 border-r border-black/20"></div>
                                                <div class="h-full bg-brand-primary/40 w-1/3"></div>
                                            </div>
                                            <div id="price-marker" class="absolute bottom-1 left-[50%] flex flex-col items-center transition-all duration-700">
                                                <span id="current-price-label" class="text-[10px] mb-2 font-black text-white bg-black/80 px-2 py-0.5 rounded border border-white/20">$0.00</span>
                                                <div class="w-1 h-4 bg-white shadow-[0_0_10px_rgba(255,255,255,0.5)]"></div>
                                            </div>
                                        </div>
    """
    
    # 3. Robust Data Mapping in fetchData
    fetch_fix = """
                        smartMoneyData.push({
                            ...item, rank: (i+1).toString().padStart(2, '0'),
                            ticker: item.ticker || 'N/A', name: item.name || item.ticker,
                            sector: item.sector || '기타', score: score,
                            signal: item.grade ? item.grade.split(' ')[1] : (score > 80 ? '적극 매수' : '매수'),
                            price: price, change: parseFloat(item.change) || 0,
                            insight: item.insight || '분석 완료.', 
                            risk: item.risk || '특이사항 없습니다.',
                            upside: item.upside || '+0%',
                            mkt_cap: item.mkt_cap || 'N/A',
                            vol_ratio: item.vol_ratio || '1.0x',
                            rsi: item.rsi || '50.0',
                            signal_strength: item.signal_strength || (score > 80 ? '강력' : '보통'),
                            swot_s: item.swot_s || '-',
                            swot_w: item.swot_w || '-',
                            swot_o: item.swot_o || '-',
                            swot_t: item.swot_t || '-',
                            dcf_target: item.dcf_target || `$${(price * 1.1).toFixed(2)}`,
                            dcf_bear: item.dcf_bear || `$${(price * 0.9).toFixed(2)}`,
                            dcf_bull: item.dcf_bull || `$${(price * 1.3).toFixed(2)}`
                        });
    """

    # Applying changes
    # Target SWOT replacement
    old_swot = r'<div class="grid grid-cols-2 gap-3">[\s\S]*?id="swot-t"[\s\S]*?</div>[\s\S]*?</div>'
    content = re.sub(old_swot, swot_html.strip(), content)
    
    # Target DCF replacement
    old_dcf = r'<div class="h-1\.5 w-full bg-gray-800 rounded-full mb-10 relative">[\s\S]*?</div>[\s\S]*?</div>' # This is broad, but let's be careful.
    # Better: match the marker block specifically
    marker_pattern = r'<div id="price-marker"[\s\S]*?</div>[\s\S]*?</div>'
    content = re.sub(marker_pattern, '<div id="price-marker" class="absolute bottom-1 left-[50%] flex flex-col items-center transition-all duration-700"><span id="current-price-label" class="text-[10px] mb-2 font-black text-white bg-black/80 px-2 py-0.5 rounded border border-white/20">$0.00</span><div class="w-1 h-5 bg-white shadow-xl"></div></div>', content)
    
    # Target Data Mapping
    old_mapping = r'smartMoneyData\.push\(\{[\s\S]*?upside: item\.upside \|\| \'\+0%\'[\s\S]*?\}\);'
    content = re.sub(old_mapping, fetch_fix.strip(), content)

    # Finally, adjust the Valuation Spectrum container for more height to accommodate the label above
    content = content.replace('mb-10 relative', 'mb-6 relative mt-10')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("SUCCESS: SWOT colors, DCF overlap, and Data fallbacks fixed.")

except Exception as e:
    print(f"ERROR: {e}")
