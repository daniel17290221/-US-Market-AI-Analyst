
import os
import re

path = r'c:\Users\mjang\Downloads\Investment Vibecodinglab\templates\index.html'

# I will rebuild from <main> to </main> for certainty.
# This avoids any missing/extra divs from previous surgical edits.

main_content = """
    <main class="px-6 pb-12">
        <!-- SPA Tab Content: US Market (Default) -->
        <div id="tab-market" class="tab-content">
            <div class="grid grid-cols-12 gap-6">
                <!-- Left Column: Top Analysis -->
                <div class="col-span-12 lg:col-span-8 space-y-6">
                    <!-- 1. Main Featured Stock (Chart Area) -->
                    <div class="glass-card p-6 min-h-[800px] flex flex-col">
                        <div class="flex justify-between items-start mb-6">
                            <div class="flex items-center gap-4">
                                <div class="p-3 bg-gray-800/50 rounded-2xl border border-white/5">
                                    <i class="fas fa-stethoscope text-3xl text-brand-primary"></i>
                                </div>
                                <div>
                                    <h2 class="text-3xl font-bold flex items-center gap-3">
                                        <span id="main-ticker-name">Loading...</span> 
                                        <span id="main-full-name" class="text-gray-400 text-lg font-normal">Please wait...</span>
                                    </h2>
                                    <div class="flex gap-3 mt-2">
                                        <span id="ai-score-pill" class="score-pill score-mid text-base py-1.5 px-4">Score: --</span>
                                        <span id="ai-signal-pill" class="score-pill bg-gray-800 text-gray-400 border border-white/10 text-base py-1.5 px-4 font-bold">Signal: --</span>
                                    </div>
                                </div>
                            </div>
                            <div class="flex gap-2 bg-gray-900/50 p-1 rounded-lg">
                                <button onclick="changeInterval('1D')" class="px-3 py-1 text-xs rounded hover:bg-gray-800">1D</button>
                                <button onclick="changeInterval('1W')" class="px-3 py-1 text-xs rounded hover:bg-gray-800">1W</button>
                                <button onclick="changeInterval('1M')" class="px-3 py-1 text-xs rounded bg-brand-primary text-black font-bold">1M</button>
                                <button onclick="changeInterval('1Y')" class="px-3 py-1 text-xs rounded hover:bg-gray-800">1Y</button>
                            </div>
                        </div>

                        <!-- Chart -->
                        <div class="w-full h-[500px] rounded-xl overflow-hidden mb-6 bg-black/20" id="tradingview_container">
                            <div id="tradingview_main" style="height:100%;width:100%"></div>
                            <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
                        </div>

                        <!-- Analysis Report Part -->
                        <div class="mt-8 pt-6 border-t border-white/10 space-y-8">
                             <!-- Metics Grid -->
                             <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
                                <div class="p-4 bg-white/5 rounded-xl border border-white/10 text-center">
                                    <p class="text-[10px] text-gray-500 font-bold uppercase mb-1">시가 총액</p>
                                    <p id="detail-mkt-cap" class="text-base font-mono font-bold">--</p>
                                </div>
                                <div class="p-4 bg-white/5 rounded-xl border border-white/10 text-center">
                                    <p class="text-[10px] text-gray-500 font-bold uppercase mb-1">거래량</p>
                                    <p id="detail-vol-ratio" class="text-base font-mono font-bold">--</p>
                                </div>
                                <div class="p-4 bg-white/5 rounded-xl border border-white/10 text-center">
                                    <p class="text-[10px] text-gray-500 font-bold uppercase mb-1">RSI(14)</p>
                                    <p id="detail-rsi" class="text-base font-mono font-bold">--</p>
                                </div>
                                <div class="p-4 bg-white/5 rounded-xl border border-white/10 text-center">
                                    <p class="text-[10px] text-gray-500 font-bold uppercase mb-1">AI 점수</p>
                                    <p id="detail-score" class="text-base font-mono font-bold">--</p>
                                </div>
                                <div class="p-4 bg-white/5 rounded-xl border border-white/10 text-center">
                                    <p class="text-[10px] text-gray-500 font-bold uppercase mb-1">신호</p>
                                    <p id="detail-signal-strength" class="text-base font-mono font-bold">--</p>
                                </div>
                             </div>

                             <!-- Insight & Valuation -->
                             <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                                <div class="space-y-4">
                                    <div class="p-6 bg-brand-secondary/5 rounded-2xl border border-brand-secondary/20">
                                        <h4 class="text-sm font-bold mb-3 flex items-center gap-2"><i class="fas fa-brain text-brand-secondary"></i> AI Insight</h4>
                                        <p id="ai-insight" class="text-sm leading-relaxed text-gray-300">데이터 수집 중...</p>
                                    </div>
                                    <div class="p-6 bg-brand-danger/5 rounded-2xl border border-brand-danger/20">
                                        <h4 class="text-sm font-bold mb-3 flex items-center gap-2"><i class="fas fa-exclamation-triangle text-brand-danger"></i> 핵심 리스크</h4>
                                        <p id="ai-risk" class="text-sm leading-relaxed text-gray-400">데이터 수집 중...</p>
                                        <p id="ai-upside" class="mt-4 text-xs font-bold text-brand-success"></p>
                                    </div>
                                </div>

                                <div class="space-y-4">
                                    <div class="p-6 bg-gray-900/50 rounded-2xl border border-white/5">
                                        <h4 class="text-sm font-bold mb-4 uppercase tracking-widest text-gray-500">Valuation Spectrum</h4>
                                        <div class="h-2 w-full bg-gray-800 rounded-full mb-8 relative">
                                            <div class="absolute inset-0 flex rounded-full overflow-hidden">
                                                <div class="h-full bg-brand-danger/40 w-1/3 border-r border-black/30"></div>
                                                <div class="h-full bg-brand-success/40 w-1/3 border-r border-black/30"></div>
                                                <div class="h-full bg-brand-primary/40 w-1/3"></div>
                                            </div>
                                            <div id="price-marker" class="absolute top-4 left-[50%] flex flex-col items-center">
                                                <div class="w-1 h-4 bg-white"></div>
                                                <span id="current-price-label" class="text-[10px] mt-1 font-bold text-white">$0</span>
                                            </div>
                                        </div>
                                        <div class="flex justify-between text-[10px] font-mono text-gray-500">
                                            <div class="text-center"><p>BEAR</p><p id="dcf-bear" class="text-white">--</p></div>
                                            <div class="text-center"><p class="text-brand-primary">TARGET</p><p id="dcf-target" class="text-brand-primary font-bold">--</p></div>
                                            <div class="text-center"><p>BULL</p><p id="dcf-bull" class="text-white">--</p></div>
                                        </div>
                                    </div>
                                    
                                    <div class="grid grid-cols-2 gap-2">
                                        <div class="p-3 bg-white/5 rounded-lg text-center"><p class="text-[8px] text-gray-500">SWOT S</p><p id="swot-s" class="text-[10px]">--</p></div>
                                        <div class="p-3 bg-white/5 rounded-lg text-center"><p class="text-[8px] text-gray-500">SWOT W</p><p id="swot-w" class="text-[10px]">--</p></div>
                                        <div class="p-3 bg-white/5 rounded-lg text-center"><p class="text-[8px] text-gray-500">SWOT O</p><p id="swot-o" class="text-[10px]">--</p></div>
                                        <div class="p-3 bg-white/5 rounded-lg text-center"><p class="text-[8px] text-gray-500">SWOT T</p><p id="swot-t" class="text-[10px]">--</p></div>
                                    </div>
                                </div>
                             </div>
                        </div>
                    </div>

                    <!-- 2. Smart Money Table -->
                    <div class="glass-card p-6 overflow-hidden">
                        <div class="flex justify-between items-center mb-6">
                            <h2 class="text-xl font-bold flex items-center gap-2">
                                <i class="fas fa-fire text-brand-danger"></i> 실시간 스마트 머니 Top 10
                            </h2>
                            <div class="text-[10px] text-gray-500 font-mono">
                                VERCEL ENGINE v3.1 ACTIVE
                            </div>
                        </div>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left border-collapse">
                                <thead>
                                    <tr class="text-xs text-gray-500 font-bold uppercase tracking-wider border-b border-white/5">
                                        <th class="px-6 py-4">순위</th>
                                        <th class="px-6 py-4">티커</th>
                                        <th class="px-6 py-4">섹터</th>
                                        <th class="px-6 py-4">AI 점수</th>
                                        <th class="px-6 py-4">상태</th>
                                        <th class="px-6 py-4">현재가</th>
                                        <th class="px-6 py-4 text-right">등락</th>
                                    </tr>
                                </thead>
                                <tbody id="smart-money-tbody" class="text-sm">
                                    <!-- Dynamic rows -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Right Column: Sidebar -->
                <div class="col-span-12 lg:col-span-4 space-y-6">
                    <!-- Market Heatmap -->
                    <div class="glass-card p-6">
                        <h2 class="text-sm font-bold uppercase text-gray-400 tracking-wider mb-4">시장 섹터 흐름</h2>
                        <div id="market-heatmap-container" class="grid grid-cols-2 gap-2">
                            <!-- Simple heatmap fallback -->
                            <div class="p-4 bg-brand-success/20 rounded-lg text-center border border-brand-success/30"><p class="text-xs font-bold">TECH</p><p class="text-[10px]">+2.4%</p></div>
                            <div class="p-4 bg-brand-danger/20 rounded-lg text-center border border-brand-danger/30"><p class="text-xs font-bold">FINANCE</p><p class="text-[10px]">-0.8%</p></div>
                        </div>
                    </div>

                    <!-- Macro Analysis -->
                    <div class="glass-card p-6 bg-accent-gradient/5">
                        <h2 class="text-base font-bold mb-4 flex items-center gap-2"><i class="fas fa-microchip text-brand-secondary"></i> Macro Outlook</h2>
                        <div class="space-y-4">
                            <div class="p-3 bg-gray-900/50 rounded-xl border border-white/5">
                                <div class="flex justify-between items-center mb-1">
                                    <span class="text-[8px] text-gray-500 font-bold">심리 지수</span>
                                    <span id="macro-sentiment" class="text-[10px] font-mono text-brand-secondary font-bold">--</span>
                                </div>
                                <p id="macro-summary" class="text-xs font-bold">로딩 중...</p>
                            </div>
                            <div id="macro-takeaways" class="space-y-1 text-[10px] text-gray-400">
                                <!-- Takeaways -->
                            </div>
                        </div>
                    </div>

                    <!-- Economic Calendar -->
                    <div class="glass-card p-6">
                        <h2 class="text-sm font-bold uppercase text-gray-400 mb-4">주요 일정</h2>
                        <div id="calendar-mini-list" class="space-y-2">
                            <!-- Events -->
                        </div>
                    </div>

                    <!-- ETF Money Flow -->
                    <div class="glass-card p-6">
                        <div class="flex justify-between items-center mb-4">
                            <h2 class="text-sm font-bold uppercase text-gray-400">ETF 자금 흐름</h2>
                            <div class="flex gap-1" id="etf-toggle-buttons">
                                <button onclick="setETFFlowType('inflow')" id="etf-btn-inflow" class="px-2 py-1 bg-brand-primary/20 text-brand-primary rounded text-[10px] font-bold">유입</button>
                                <button onclick="setETFFlowType('outflow')" id="etf-btn-outflow" class="px-2 py-1 bg-gray-800 text-gray-400 rounded text-[10px]">유출</button>
                            </div>
                        </div>
                        <div class="space-y-2" id="etf-flow-container">
                            <p class="text-[10px] text-center text-gray-600 py-4">동기화 중...</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Placeholder Tabs (hidden by default) -->
        <div id="tab-calendar" class="tab-content hidden glass-card p-6">
             <div class="h-[600px] flex items-center justify-center italic text-gray-500">Live Calendar Widget Integration Active</div>
        </div>
        <div id="tab-historical" class="tab-content hidden glass-card p-6">
             <div class="h-[600px] flex items-center justify-center italic text-gray-500">Historical Patterns Engine Offline</div>
        </div>
    </main>
"""

try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define the pattern to replace everything from <main> to </main>
    pattern = r'<main[\s\S]*?</main>'
    
    if re.search(pattern, content):
        new_content = re.sub(pattern, main_content.strip(), content)
        
        # Also clean up the header navigation to match the switchTab IDs
        nav_pattern = r'<!-- Mobile Menu Button -->[\s\S]*?<!-- Settings Button -->'
        clean_nav = """<!-- Mobile Menu Button -->
        <div class="hidden lg:flex items-center gap-8 mr-12">
            <a onclick="switchTab('market')"
                class="tab-active py-1 text-sm font-semibold hover:text-gray-300 transition cursor-pointer">실시간 스마트 머니</a>
            <a onclick="switchTab('calendar')"
                class="tab-inactive py-1 text-sm font-semibold hover:text-gray-300 transition cursor-pointer">경제 캘린더</a>
        </div>\n\n        <!-- Settings Button -->"""
        
        if re.search(nav_pattern, new_content):
            new_content = re.sub(nav_pattern, clean_nav, new_content)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("SUCCESS: Body structure and navigation fully rebuilt.")
    else:
        print("FAILURE: <main> tag not found.")

except Exception as e:
    print(f"ERROR: {e}")
