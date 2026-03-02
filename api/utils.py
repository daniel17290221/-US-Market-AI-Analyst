import os
import sys
import json
import csv
import logging
import requests
import xml.etree.ElementTree as ET
import concurrent.futures
from datetime import datetime
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Build: 2026-02-10 15:32 (KST) - Case-insensitive API Key Fix
AI_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("google_api_key")

# Robust path resolution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Robust data directory resolution (Handles nested folder structures)
def get_data_dir(name):
    # Try multiple common patterns
    paths = [
        os.path.join(BASE_DIR, name, name), # Nested like 'us_market/us_market'
        os.path.join(BASE_DIR, name),       # Standard like 'us_market/'
        os.path.join(os.path.dirname(__file__), '..', name, name),
        os.path.join(os.path.dirname(__file__), '..', name)
    ]
    for p in paths:
        if os.path.isdir(p):
            # Check for key markers (csv, json)
            if any(f.endswith('.json') or f.endswith('.csv') for f in os.listdir(p)):
                # print(f"DEBUG: Found {name} data at {p}")
                return p
    # print(f"DEBUG: Falling back to default data dir for {name}")
    return os.path.join(BASE_DIR, name)

DATA_DIR = get_data_dir('us_market')
KR_DATA_DIR = get_data_dir('KR_Market_Analyst')

# --- Shared Data Cache ---
AI_CACHE = {} 
portfolio_rate_limit = {}

# --- Persistent Knowledge: Major KR Analysis ---
MAJOR_ANALYSIS_KR = {
    "005930": {
        "insight": "DRAM 가격 반등과 HBM3E 공급 확대가 실적 개선을 견인할 것으로 예상됩니다.",
        "risk": "글로벌 스마트폰 수요 둔화 및 파운드리 점유율 확대 지연.",
        "upside": "+25%", "mkt_cap": "$450B", "vol_ratio": "1.5x ↑", "rsi": "58.4",
        "swot_s": "글로벌 메모리 반도체 1위 지배력", "swot_w": "기술 격차 축소 우려 (HBM 등)",
        "swot_o": "AI 서버향 고부가가치 제품 수요 폭증", "swot_t": "경쟁 심화 및 미중 갈등",
        "dcf_target": "205,000", "dcf_bear": "140,000", "dcf_bull": "240,000"
    },
    "000660": {
        "insight": "NVIDIA향 HBM 공급 독점적 지위가 유지되며 AI 모멘텀의 최대 수혜주입니다.",
        "risk": "메모리 업황의 높은 변동성과 과도한 하이엔드 제품 의존도.",
        "upside": "+18%", "mkt_cap": "$62B", "vol_ratio": "2.8x ↑", "rsi": "72.1",
        "swot_s": "HBM 시장 내 압도적 기술 우위", "swot_w": "상대적으로 취약한 비메모리 포트폴리오",
        "swot_o": "AI 반도체 시장의 기하급수적 성장", "swot_t": "빅테크 기업들의 자체 칩 개발",
        "dcf_target": "1,150,000", "dcf_bear": "820,000", "dcf_bull": "1,350,000"
    },
    "005380": {
        "insight": "전기차와 하이브리드 투트랙 전략이 주효하며 사상 최대 이익 기조를 유지하고 있습니다.",
        "risk": "글로벌 전기차 수요 캐즘(Chasm) 현상 및 지정학적 리스크.",
        "upside": "+15%", "mkt_cap": "$48B", "vol_ratio": "1.1x", "rsi": "52.4",
        "swot_s": "믹스 개선을 통한 수익성 극대화", "swot_w": "내수 시장 점유율 방어 필요성",
        "swot_o": "북미 메타플랜트 가동 및 수소 생태계", "swot_t": "금리 인상에 따른 소비 심리 위축",
        "dcf_target": "620,000", "dcf_bear": "480,000", "dcf_bull": "710,000"
    },
    "207940": {
        "insight": "압도적인 생산 능력을 바탕으로 한 CMO/CDMO 수주 확대가 견조한 성장을 뒷받침합니다.",
        "risk": "미국 생물보안법 영향 가능성 및 후발주자들의 추격.",
        "upside": "+12%", "mkt_cap": "$55B", "vol_ratio": "0.9x", "rsi": "48.2",
        "swot_s": "글로벌 1위의 바이오 생산 캐파", "swot_w": "높은 위탁 생산 의존도",
        "swot_o": "자체 신약 파이프라인 상업화 가시화", "swot_t": "글로벌 공급망 재편 및 단가 경쟁",
        "dcf_target": "2,150,000", "dcf_bear": "1,650,000", "dcf_bull": "2,400,000"
    },
    "373220": {
        "insight": "LFP 배터리 및 차세대 제품군 확대를 통해 전기차 수요 둔화 국면을 정면 돌파 중입니다.",
        "risk": "완성차 업체들의 배터리 내재화 추진 및 원자재 가격 변동성.",
        "upside": "+20%", "mkt_cap": "$82B", "vol_ratio": "1.3x", "rsi": "55.1",
        "swot_s": "북미 시장 내 압도적 점유율과 파트너십", "swot_w": "수익성 개선 속도 지연 우려",
        "swot_o": "에너지저장장치(ESS) 시장의 고성장", "swot_t": "중국 LFP 배터리 기업의 글로벌 확장",
        "dcf_target": "580,000", "dcf_bear": "360,000", "dcf_bull": "680,000"
    },
    "000270": {
        "insight": "EV9 등 프리미엄 모델 비중 확대와 환율 효과로 강력한 현금 흐름을 창출하고 있습니다.",
        "risk": "주주 환원 정책 기대감 소멸 및 피크 아웃 논란.",
        "upside": "+22%", "mkt_cap": "$35B", "vol_ratio": "1.8x", "rsi": "61.5",
        "swot_s": "브랜드 인지도 상승 및 디자인 경쟁력", "swot_w": "전동화 전환 초기 비용 부담",
        "swot_o": "주주 환원 정책 강화(자사주 소각 등)", "swot_t": "글로벌 보호무역주의 강화 추세",
        "dcf_target": "195,000", "dcf_bear": "145,000", "dcf_bull": "230,000"
    },
    "068270": {
        "insight": "합병 이후 원가율 개선과 짐펜트라의 미국 시장 안착이 실적 성장의 핵심 동력입니다.",
        "risk": "바이오시밀러 경쟁 심화에 따른 약가 인하 압박.",
        "upside": "+15%", "mkt_cap": "$32B", "vol_ratio": "1.2x", "rsi": "54.2",
        "swot_s": "바이오시밀러 시장 내 선도적 입지", "swot_w": "높은 램시마 의존도 및 합병 후 초기 비용",
        "swot_o": "신약 짐펜트라의 미국 매출 본격화", "swot_t": "글로벌 대형 제약사들의 시장 진입",
        "dcf_target": "320,000", "dcf_bear": "250,000", "dcf_bull": "380,000"
    },
    "035420": {
        "insight": "AI 검색 서비스 '큐:' 도입과 클라우드 부문의 견조한 성장세가 주가 반등의 촉매제가 될 전망입니다.",
        "risk": "C-커머스 공세에 따른 커머스 수익성 둔화 우려.",
        "upside": "+28%", "mkt_cap": "$25B", "vol_ratio": "1.4x", "rsi": "56.8",
        "swot_s": "국내 최대 검색 플랫폼 및 방대한 유저 데이터", "swot_w": "글로벌 확장성 부족 및 마케팅 비용 부담",
        "swot_o": "B2B AI 시장 선점 및 자회사 상장 모멘텀", "swot_t": "유튜브/구글 등 글로벌 플랫폼의 국내 점유율 확대",
        "dcf_target": "285,000", "dcf_bear": "180,000", "dcf_bull": "340,000"
    },
    "035720": {
        "insight": "광고 매출의 회복과 AI 사업 조직 통합을 통한 경영 효율화가 가시화되고 있습니다.",
        "risk": "사법 리스크 및 계열사들의 실적 부진 장기화.",
        "upside": "+22%", "mkt_cap": "$18B", "vol_ratio": "1.1x", "rsi": "51.2",
        "swot_s": "압도적인 플랫폼 접근성(카카오톡)", "swot_w": "사법 리스크에 따른 신사업 추진 지연",
        "swot_o": "카카오톡 내 AI 에이전트 도입 시너지", "swot_t": "플랫폼 규제 강화 및 경쟁 앱들의 약진",
        "dcf_target": "75,000", "dcf_bear": "45,000", "dcf_bull": "92,000"
    },
    "005490": {
        "insight": "리튬 가격 저점 통과 기대감과 철강 업황의 완만한 회복세가 투자 심리를 개선 중입니다.",
        "risk": "전기차 수요 둔화에 따른 이차전지 소재 부문 실적 지연.",
        "upside": "+18%", "mkt_cap": "$30B", "vol_ratio": "1.3x", "rsi": "49.5",
        "swot_s": "철강에서 이차전지 소재로의 완벽한 체질 개선", "swot_w": "원재료(리튬 등) 가격 변동에 높은 노출도",
        "swot_o": "북미 리튬 생산 시설 가동 및 폐배터리 리사이클링", "swot_t": "중국발 철강 공급 과잉 및 저가 공세",
        "dcf_target": "580,000", "dcf_bear": "380,000", "dcf_bull": "680,000"
    },
    "105560": {
        "insight": "강력한 주주 환원 정책과 밸류업 프로그램의 직접적인 수혜가 기대되는 저평가 우량주입니다.",
        "risk": "부동산 PF 관련 충당금 적립 부담 및 금리 인하 국면 진입 시 마진 축소.",
        "upside": "+15%", "mkt_cap": "$22B", "vol_ratio": "1.0x", "rsi": "62.4",
        "swot_s": "국내 1위 금융지주의 압도적인 자산 건전성", "swot_w": "비은행 부문의 상대적 낮은 기여도",
        "swot_o": "적극적인 자사주 매입 및 소각 로드맵", "swot_t": "금융 당국의 대출 규제 및 상생 금융 압박",
        "dcf_target": "95,000", "dcf_bear": "68,000", "dcf_bull": "110,000"
    }
}

# --- Persistent Knowledge: Major US Analysis ---
major_us_analysis = {
    "NVDA": {
        "insight": "NVIDIA는 AI 가속기 시장에서 독보적 지위를 유지하고 있으며, Blackwell 출시로 매출 성장이 가속화될 전망입니다.",
        "risk": "중국 수출 규제 영향 및 경쟁사 AMD MI300 대항 전략.",
        "upside": "+18.2%", "mkt_cap": "$3.5T", "vol_ratio": "3.2x ↑", "rsi": "72.4",
        "swot_s": "AI 시장 80%+ 점유율 및 CUDA 생태계", "swot_w": "빅테크 고객 집중도 및 높은 의존도",
        "swot_o": "자율주행 및 엣지 AI 시장 확대", "swot_t": "중국 수출 규제 및 경쟁 심화",
        "dcf_target": "165.00", "dcf_bear": "125.00", "dcf_bull": "190.00"
    },
    "AAPL": {
        "insight": "Apple Intelligence를 통한 교체 수요 자극과 서비스 부문의 고마진 성장이 밸류에이션을 지지합니다.",
        "risk": "아이폰 판매량 둔화 및 하드웨어 혁신 속도에 대한 시장의 의구심.",
        "upside": "+12.5%", "mkt_cap": "$3.4T", "vol_ratio": "0.9x", "rsi": "58.2",
        "swot_s": "강력한 브랜드 로열티 및 생태계 락인 효과", "swot_w": "하드웨어 매출 의존도 및 규제 리스크",
        "swot_o": "AI 통합을 이용한 프리미엄 기기 수요 창출", "swot_t": "스마트폰 시장 성숙 및 미중 갈등",
        "dcf_target": "265.00", "dcf_bear": "210.00", "dcf_bull": "310.00"
    },
    "TSLA": {
        "insight": "자율주행 기술력 우위와 로보택시 비즈너지 모델 구체화가 주가의 핵심 변수입니다.",
        "risk": "전기차 수요 캐즘 현상 및 글로벌 가격 경쟁 심화.",
        "upside": "+22.8%", "mkt_cap": "$820B", "vol_ratio": "2.4x ↑", "rsi": "64.5",
        "swot_s": "압도적인 자율주행 데이터 축적 및 브랜드 리딩", "swot_w": "생산 효율화 한계 및 CEO 리스크",
        "swot_o": "에너지 저장 장치(ESS) 및 옵티머스 로봇 사업 가속화", "swot_t": "중국산 저가 전기차 공세 강화",
        "dcf_target": "350.00", "dcf_bear": "220.00", "dcf_bull": "480.00"
    },
    "MSFT": {
        "insight": "Azure와 Copilot의 결합으로 기업용 AI 시장의 실질적인 수익화가 가장 빠르게 진행되고 있습니다.",
        "risk": "인프라 투자 비용(CAPEX) 급증에 따른 수익성 일시 하락 우려.",
        "upside": "+15.4%", "mkt_cap": "$3.1T", "vol_ratio": "1.1x", "rsi": "55.8",
        "swot_s": "독보적인 B2B 영업망 및 클라우드 기술력", "swot_w": "높은 인수로 인한 부채 및 통합 과제",
        "swot_o": "생성형 AI의 전 제품군 통합 시너지", "swot_t": "클라우드 시장 내 구글/아마존의 추격",
        "dcf_target": "500.00", "dcf_bear": "410.00", "dcf_bull": "560.00"
    },
    "AMZN": {
        "insight": "AWS의 견조한 성장세 회복과 광고 부문의 폭발적인 성장이 수익성 개선을 주도하고 있습니다.",
        "risk": "전자상거래 부문의 경쟁 심화 및 물류 비용 증가 리스크.",
        "upside": "+20.1%", "mkt_cap": "$1.9T", "vol_ratio": "1.5x ↑", "rsi": "62.4",
        "swot_s": "글로벌 클라우드 1위(AWS) 및 막강한 물류망", "swot_w": "낮은 리테일 마진 및 반독점 규제",
        "swot_o": "AI를 활용한 물류 최적화 및 광고 사업 확장", "swot_t": "Temu, Shein 등 저가 이커머스 공세",
        "dcf_target": "230.00", "dcf_bear": "180.00", "dcf_bull": "270.00"
    },
    "META": {
        "insight": "광고 효율 개선과 AI 추천 엔진 강화로 인스타그램/페이스북의 사용자 체류 시간이 늘어나고 있습니다.",
        "risk": "메타버스 부문의 대규모 적자 지속 및 규제 강화.",
        "upside": "+18.5%", "mkt_cap": "$1.4T", "vol_ratio": "1.8x ↑", "rsi": "68.2",
        "swot_s": "압도적인 소셜 미디어 점유율 및 광고 정밀 타겟팅", "swot_w": "현금 창출원의 애플 플랫폼 의존성",
        "swot_o": "릴스(Reels) 수익화 가속 및 Llama 통한 AI 주도권", "swot_t": "틱톡 경쟁 및 가짜 뉴스 관련 사회적 책임",
        "dcf_target": "650.00", "dcf_bear": "520.00", "dcf_bull": "760.00"
    },
    "GOOGL": {
        "insight": "검색 광고 시장의 지배력 유지와 제미나이(Gemini) 고도화를 통한 AI 반격이 기대됩니다.",
        "risk": "생성형 AI 검색 도입에 따른 기존 검색 광고 모델 잠식(Cannibalization) 우려.",
        "upside": "+14.2%", "mkt_cap": "$2.1T", "vol_ratio": "1.3x", "rsi": "51.4",
        "swot_s": "유튜브 및 안드로이드 등 방대한 데이터 생태계", "swot_w": "AI 대응 속도에 대한 시장의 의구심",
        "swot_o": "구글 클라우드의 가파른 성장 및 웨이모 상용화", "swot_t": "브라우저 점유율 및 검색 반독점 소송 리스크",
        "dcf_target": "210.00", "dcf_bear": "165.00", "dcf_bull": "245.00"
    }
}

def load_json(filename):
    possible_paths = [
        os.path.join(DATA_DIR, filename),
        os.path.join(os.getcwd(), 'us_market', filename),
        os.path.join(os.getcwd(), filename),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'us_market', filename))
    ]
    
    data = {}
    path_to_use = None
    for path in possible_paths:
        if os.path.exists(path):
            path_to_use = path
            break
            
    if path_to_use:
        try:
            with open(path_to_use, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Error reading {filename} from {path_to_use}: {e}")
    
    if not data and filename == 'us_macro_analysis.json':
        return {
            "market_mood": "Greed",
            "mood_score": 78,
            "key_takeaways": ["AI 주도 빅테크 랠리 지속", "국채 금리 하락세로 성장주 모멘텀 강화", "소비자 심리 지수 예상치 상회"],
            "sector_outlook": "반도체 및 기술 섹터 비중 확대 권고",
            "risk_factors": "인플레이션 재점화 가능성 및 지정학적 리스크"
        }
    return data or {}

def load_csv(filename):
    possible_paths = [
        os.path.join(DATA_DIR, filename),
        os.path.join(os.getcwd(), 'us_market', filename),
        os.path.join(os.getcwd(), filename),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'us_market', filename))
    ]
    
    data = []
    path_to_use = None
    for path in possible_paths:
        if os.path.exists(path):
            path_to_use = path
            break
            
    if path_to_use:
        for enc in ['utf-8-sig', 'utf-8', 'cp949']:
            try:
                with open(path_to_use, 'r', encoding=enc) as f:
                    reader = csv.DictReader(f)
                    reader.fieldnames = [f.strip() for f in reader.fieldnames] if reader.fieldnames else []
                    temp_data = []
                    for row in reader:
                        row = {k.strip() if k else k: v.strip() if isinstance(v, str) else v for k, v in row.items()}
                        if 'composite_score' in row and 'score' not in row:
                            row['score'] = row['composite_score']
                        try:
                            row['score'] = float(row.get('score', 0))
                            row['price'] = float(row.get('price', row.get('current_price', 0)))
                            row['change'] = float(row.get('change', 0))
                        except Exception: pass
                        temp_data.append(row)
                    if temp_data:
                        data = temp_data
                        break
            except Exception: pass
    
    if not data and filename == 'smart_money_picks_v2.csv':
        return [
            {
                "rank": "01", "ticker": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology", 
                "composite_score": "95.8", "grade": "🔥 S급 (즉시 매수)", "price": "142.87", "change": "8.4",
                "insight": "NVIDIA는 AI 가속기 시장에서 독보적 지위를 유지하고 있으며, Blackwell 출시로 매출 성장이 가속화될 전망입니다.",
                "risk": "중국 수출 규제 영향 및 경쟁사 AMD MI300 대항 전략.",
                "upside": "+18.2%", "mkt_cap": "$3.5T", "vol_ratio": "3.2x ↑", "rsi": "72.4",
                "swot_s": "AI 시장 80%+ 점유율 및 CUDA 생태계", "swot_w": "빅테크 고객 집중도 및 높은 의존도",
                "swot_o": "자율주행 및 엣지 AI 시장 확대", "swot_t": "중국 수출 규제 및 경쟁 심화",
                "dcf_target": "$165.00", "dcf_bear": "$125.00", "dcf_bull": "$190.00"
            }
        ]
    return data

def fetch_naver_movers(mover_type='rise', sosok=None):
    try:
        url = f"https://finance.naver.com/sise/sise_{mover_type}.nhn"
        if sosok is not None:
             url += f"?sosok={sosok}"
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code != 200: return []
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, 'lxml')
        items = []
        table = soup.find('table', {'class': 'type_2'})
        if not table: return []
        
        for tr in table.find_all('tr')[2:]:
            tds = tr.find_all('td')
            if len(tds) < 6: continue
            name_tag = tds[1].find('a')
            if not name_tag: continue
            
            name = name_tag.text.strip()
            link = name_tag['href']
            # Extraction of 6-digit code: /item/main.nhn?code=005930
            import re
            code_match = re.search(r'code=(\d+)', link)
            code = code_match.group(1) if code_match else ""
            
            price = tds[2].text.replace(',', '').strip()
            change = tds[4].text.strip()
            # If it's rise, we might need to check if it's up or down
            img = tds[3].find('img')
            if img and 'down' in img.get('src', '').lower():
                 change = "-" + change
            
            items.append({
                "name": name,
                "symbol": code,
                "price": price,
                "change": change,
                "market": "KOSPI" if sosok == 0 else "KOSDAQ"
            })
        return items
    except Exception as e:
        logger.error(f"Naver Fetch Error: {e}")
        return []

def fetch_single_ticker(ticker, headers):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=1d"
        r = requests.get(url, headers=headers, timeout=4)
        if r.status_code == 200:
            res = r.json()['chart']['result'][0]['meta']
            curr = res.get('regularMarketPrice')
            prev = res.get('previousClose')
            change = ((curr - prev) / prev * 100) if prev else 0
            return ticker, {"price": curr, "change": round(change, 2)}
    except: pass
    return ticker, None

def fetch_realtime_data(tickers):
    headers = {'User-Agent': 'Mozilla/5.0'}
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_single_ticker, t, headers) for t in tickers]
        for f in concurrent.futures.as_completed(futures):
            ticker, data = f.result()
            if data: results[ticker] = data
    return results

def fetch_dynamic_ai_analysis(stocks_to_analyze):
    if not stocks_to_analyze: return {}
    results = {}
    today = datetime.now().strftime("%Y-%m-%d")
    
    def normalize(sym):
        if sym.endswith('.KS') or sym.endswith('.KQ'): return sym
        return sym.split('.')[0]

    api_key = AI_KEY
    if not api_key: return {}
    
    try:
        payload_items = []
        for s in stocks_to_analyze:
            sym = normalize(s['symbol'])
            name = s.get('name', sym)
            # Check cache
            if (today, sym) in AI_CACHE:
                results[sym] = AI_CACHE[(today, sym)]
                continue
            payload_items.append(f"{name} ({sym})")
            
        if not payload_items: return results
        
        logger.info(f"Fetching dynamic AI analysis for: {', '.join(payload_items)}")

        prompt = f"""Analyze the following stocks for {today}. Return ONLY a JSON object where keys are exactly the symbols provided.
        Stocks: {', '.join(payload_items)}
        Format: {{ "SYMBOL": {{ "insight": "...", "risk": "...", "upside": "+X%", "mkt_cap": "...", "vol_ratio": "...", "rsi": "...", "swot_s": "...", "swot_w": "...", "swot_o": "...", "swot_t": "...", "dcf_target": "...", "dcf_bear": "...", "dcf_bull": "..." }} }}
        Language: Korean.
        """
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}, timeout=30)
        
        if resp.status_code == 200:
            raw_data = resp.json()['candidates'][0]['content']['parts'][0]['text']
            data = json.loads(raw_data)
            for raw_sym, analysis in data.items():
                # Extract ticker symbol from potentially "Name (SYMBOL)" format
                import re
                match = re.search(r'\((.*?)\)', str(raw_sym))
                if match: 
                    final_sym = match.group(1).split('.')[0].strip().upper()
                else:
                    final_sym = str(raw_sym).split('(')[0].split('.')[0].strip().upper()
                
                AI_CACHE[(today, final_sym)] = analysis
                results[final_sym] = analysis
        return results
    except Exception as e:
        logger.error(f"Gemini AI Error: {e}")
        return results

def fetch_google_news_rss(query):
    try:
        url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            items = []
            for item in root.findall('.//item')[:5]:
                title = item.find('title').text
                link = item.find('link').text
                pubDate = item.find('pubDate').text
                source = "Google News"
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0]
                    source = parts[1]
                try:
                    dt = datetime.strptime(pubDate, "%a, %d %b %Y %H:%M:%S %Z")
                    date_str = dt.strftime("%Y.%m.%d %H:%M")
                except: date_str = pubDate
                items.append({"title": title, "url": link, "date": date_str, "source": source})
            return items
    except Exception as e:
        logger.error(f"RSS error: {e}")
    return []

def fetch_yahoo_history(sym, period="6mo"):
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range={period}"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            result = data.get('chart', {}).get('result')
            if not result: return []
            
            res = result[0]
            timestamps = res.get('timestamp', [])
            quotes = res.get('indicators', {}).get('quote', [{}])[0]
            
            opens = quotes.get('open', [])
            highs = quotes.get('high', [])
            lows = quotes.get('low', [])
            closes = quotes.get('close', [])
            volumes = quotes.get('volume', [])
            
            chart_data = []
            for i in range(len(timestamps)):
                if i >= len(opens) or i >= len(closes): break
                if opens[i] is None or closes[i] is None: continue
                
                dt = datetime.fromtimestamp(timestamps[i])
                chart_data.append({
                    "time": dt.strftime('%Y-%m-%d'),
                    "open": float(opens[i]),
                    "high": float(highs[i] if highs[i] is not None else opens[i]),
                    "low": float(lows[i] if lows[i] is not None else opens[i]),
                    "close": float(closes[i]),
                    "volume": float(volumes[i] or 0)
                })
            return chart_data
    except Exception as e:
        logger.error(f"Error in fetch_yahoo_history for {sym}: {e}")
    return []

def get_exchange_rate():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/USDKRW=X?interval=1d&range=1d"
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if resp.status_code == 200:
            return float(resp.json()['chart']['result'][0]['meta']['regularMarketPrice'])
    except: pass
    return 1350.0 # Robust fallback
