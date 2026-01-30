from flask import Flask, render_template, jsonify, request, make_response
import csv
import json
import os
import requests
import sys
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Adjust path for Vercel subdirectory deployment
# BASE_DIR should be the root of the project (where templates and us_market are)
# In Vercel, this is usually the parent of 'api/'
# Robust path resolution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

try:
    import us_market
    DATA_DIR = os.path.dirname(us_market.__file__)
except:
    DATA_DIR = os.path.join(BASE_DIR, 'us_market')

# from us_market.daily_report_generator import USDailyReportGenerator (Moved inside function)

# KR Report functionality temporarily disabled for Vercel deployment
KR_REPORT_AVAILABLE = False

app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'assets'),
            static_url_path='/assets')

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
        "insight": "자율주행 기술력 우위와 로보택시 비즈니스 모델 구체화가 주가의 핵심 변수입니다.",
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

print(f"DEBUG: BASE_DIR={BASE_DIR}")
print(f"DEBUG: DATA_DIR={DATA_DIR}")

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    data = {}
    print(f"DEBUG: Trying to load JSON from {path}")
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"DEBUG: Successfully loaded JSON {filename}")
        except Exception as e:
            print(f"DEBUG: Error reading {filename}: {e}")
    else:
        print(f"DEBUG: JSON NOT FOUND at {path}")
    
    # Provide default macro data if missing or empty
    if not data and filename == 'us_macro_analysis.json':
        return {
            "market_mood": "Greed",
            "mood_score": 78,
            "key_takeaways": [
                "AI 주도 빅테크 랠리 지속",
                "국채 금리 하락세로 성장주 모멘텀 강화",
                "소비자 심리 지수 예상치 상회"
            ],
            "sector_outlook": "반도체 및 기술 섹터 비중 확대 권고",
            "risk_factors": "인플레이션 재점화 가능성 및 지정학적 리스크"
        }
    return data or {}

def load_csv(filename):
    # Try multiple potential paths to be robust against different execution environments
    possible_paths = [
        os.path.join(DATA_DIR, filename),                      # Derived from package/file location
        os.path.join(os.getcwd(), 'us_market', filename),       # From root if run as 'python app.py'
        os.path.join(os.getcwd(), filename),                   # If run from inside 'us_market/'
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'us_market', filename)) # Relative to api/
    ]
    
    data = []
    path_to_use = None
    
    for path in possible_paths:
        print(f"DEBUG: Checking path: {path}")
        if os.path.exists(path):
            path_to_use = path
            print(f"DEBUG: Found file at {path}, size={os.path.getsize(path)}")
            # Even if size is small, we try to load it (removed > 100 check)
            break
            
    if path_to_use:
        # Try multiple encodings for Korean Windows compatibility
        for enc in ['utf-8-sig', 'utf-8', 'cp949']:
            try:
                with open(path_to_use, 'r', encoding=enc) as f:
                    reader = csv.DictReader(f)
                    # Strip whitespace from field names
                    reader.fieldnames = [f.strip() for f in reader.fieldnames] if reader.fieldnames else []
                    data = []
                    for row in reader:
                        # Cleanup values and normalize field names
                        row = {k.strip() if k else k: v.strip() if isinstance(v, str) else v for k, v in row.items()}
                        
                        if 'composite_score' in row and 'score' not in row:
                            row['score'] = row['composite_score']
                        
                        # Ensure numeric types for sorting/display
                        try:
                            row['score'] = float(row.get('score', 0))
                            row['price'] = float(row.get('price', row.get('current_price', 0)))
                            row['change'] = float(row.get('change', 0))
                        except Exception:
                            # Silent conversion error to prevent encoding issues with 'e'
                            pass
                            
                        data.append(row)
                        
                    if data:
                        print(f"DEBUG: Successfully loaded {len(data)} rows from {path_to_use}")
                        # print(f"DEBUG: First row preview: {data[0]}") # Causes UnicodeEncodeError on Windows with emojis
                        break
            except Exception:
                # Silent read failure to try next encoding/fallback
                pass
    else:
        print(f"DEBUG: Could not find a valid CSV file for {filename} in any searched location.")
    
    # Provide default smart money data if missing OR empty
    if not data and filename == 'smart_money_picks_v2.csv':
        return [
            {
                "rank": "01", "ticker": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology", 
                "composite_score": "95.8", "grade": "🔥 S급 (즉시 매수)", "price": "142.87", "change": "8.4",
                "insight": "NVIDIA는 AI 가속기 시장에서 독보적 지위를 유지하고 있으며, Blackwell 아키텍처 출시로 매출 성장이 가속화될 전망입니다.",
                "risk": "중국 수출 규제 영향 및 경쟁사 AMD MI300 대항 전략.",
                "upside": "+18.2%", "mkt_cap": "$3.5T", "vol_ratio": "3.2x ↑", "rsi": "72.4",
                "swot_s": "AI 시장 80%+ 점유율 및 CUDA 생태계", "swot_w": "빅테크 고객 집중도 및 높은 의존도",
                "swot_o": "자율주행 및 엣지 AI 시장 확대", "swot_t": "중국 수출 규제 및 경쟁 심화",
                "dcf_target": "$165.00", "dcf_bear": "$125.00", "dcf_bull": "$190.00"
            },
            {
                "rank": "02", "ticker": "TSLA", "name": "Tesla, Inc.", "sector": "Automotive", 
                "composite_score": "91.2", "grade": "🌟 A급 (적극 매수)", "price": "258.45", "change": "3.1",
                "insight": "FSD v12 및 로보택시 기대감이 강력한 모멘텀을 형성하고 있으며, 비용 절감 노력이 마진을 방어 중입니다.",
                "risk": "전기차 시장의 경쟁 심화와 중국 시장 점유율 둔화 가능성.",
                "upside": "+25.5%", "mkt_cap": "$825B", "vol_ratio": "2.4x ↑", "rsi": "64.5",
                "swot_s": "자율주행 데이터 우위 및 브랜드 파워", "swot_w": "CEO 리스크 및 생산 효율화 과제",
                "swot_o": "옵티머스 로봇 및 에너지 저장 사업", "swot_t": "중국산 저가 전기차 공세",
                "dcf_target": "$320.00", "dcf_bear": "$210.00", "dcf_bull": "$410.00"
            },
            {
                "rank": "03", "ticker": "AAPL", "name": "Apple Inc.", "sector": "Technology", 
                "composite_score": "88.5", "grade": "🌟 A급 (적극 매수)", "price": "228.12", "change": "1.2",
                "insight": "애플 인텔리전스(AI)가 차기 아이폰 교체 수요의 핵심 동력으로 작용할 것으로 분석됩니다.",
                "risk": "앱스토어 반독점 규제 및 중국 내 판매 둔화 리스크.",
                "upside": "+12.1%", "mkt_cap": "$3.4T", "vol_ratio": "1.2x ↑", "rsi": "55.4",
                "swot_s": "충성도 높은 생태계 및 강력한 현금흐름", "swot_w": "하드웨어 혁신 속도 둔화",
                "swot_o": "AI 기반 서비스 부문 매출 확대", "swot_t": "글로벌 규제 당국의 반독점 조사",
                "dcf_target": "$255.00", "dcf_bear": "$205.00", "dcf_bull": "$285.00"
            },
            {
                "rank": "04", "ticker": "MSFT", "name": "Microsoft Corp", "sector": "Software", 
                "composite_score": "82.5", "grade": "🌟 A급 (적극 매수)", "price": "425.30", "change": "0.9",
                "insight": "Azure 클라우드와 OpenAI 파트너십을 통한 기업용 AI 시장 지배력이 수익성 개선을 견인하고 있습니다.",
                "risk": "성장 둔화 우려 및 클라우드 부문 마진 압박 가능성.",
                "upside": "+17.5%", "mkt_cap": "$3.1T", "vol_ratio": "1.1x", "rsi": "52.3",
                "swot_s": "클라우드 및 기업용 소프트웨어 독점력", "swot_w": "높은 밸류에이션 부담",
                "swot_o": "생성형 AI 서비스의 전사적 통합", "swot_t": "AWS와 구글의 클라우드 추격",
                "dcf_target": "$505.00", "dcf_bear": "$410.00", "dcf_bull": "$580.00"
            },
            {
                "rank": "05", "ticker": "AMZN", "name": "Amazon.com", "sector": "Commerce", 
                "composite_score": "78.5", "grade": "📈 B급 (매수 고려)", "price": "188.30", "change": "0.5",
                "insight": "물류 효율화와 AWS 수익성 개선이 성장의 핵심입니다. 마진율이 점진적으로 상승하고 있습니다.",
                "risk": "소비 심리 위축 및 반독점 규제 강화.",
                "upside": "+22.1%", "mkt_cap": "$1.9T", "vol_ratio": "1.5x", "rsi": "58.7",
                "swot_s": "이커머스 압도적 점유율 및 AWS", "swot_w": "인건비 등 비용 관리 부담",
                "swot_o": "광업 부문 고성장 및 AI 클라우드", "swot_t": "중국계 쇼핑앱과의 경쟁 심화",
                "dcf_target": "$230.00", "dcf_bear": "$175.00", "dcf_bull": "$275.00"
            },
            {
                "rank": "06", "ticker": "META", "name": "Meta Platforms", "sector": "Technology", 
                "composite_score": "77.2", "grade": "📈 B급 (매수 고려)", "price": "585.20", "change": "1.4",
                "insight": "광고 매출 회복세가 뚜렷하며, Llama AI 모델 기반 서비스 최적화가 긍정적입니다.",
                "risk": "리얼리티 랩스의 막대한 적자 및 규제 리스크.",
                "upside": "+16.2%", "mkt_cap": "$1.4T", "vol_ratio": "1.8x", "rsi": "61.2",
                "swot_s": "페이스북/인스타그램 거대한 사용자 층", "swot_w": "메타버스 사업부문의 지속적 손실",
                "swot_o": "AI 타겟팅 광고를 통한 수익성 제고", "swot_t": "틱톡과의 사용자 점유율 경쟁",
                "dcf_target": "$680.00", "dcf_bear": "$550.00", "dcf_bull": "$780.00"
            },
            {
                "rank": "07", "ticker": "GOOGL", "name": "Alphabet Inc", "sector": "Technology", 
                "composite_score": "76.5", "grade": "📈 B급 (매수 고려)", "price": "165.20", "change": "0.0",
                "insight": "검색 광고 시장의 견고함과 구글 클라우드 흑자 전환이 긍정적이나 AI 검색 경쟁이 변수입니다.",
                "risk": "반독점 소송 리스크 및 AI 검색 시장의 경쟁 심화.",
                "upside": "+24.2%", "mkt_cap": "$2.1T", "vol_ratio": "0.9x", "rsi": "49.5",
                "swot_s": "글로벌 검색 시장 점유율 1위", "swot_w": "AI 대응 속도에 대한 시장 우려",
                "swot_o": "유튜브 쇼츠 수익화 및 제미나이 AI", "swot_t": "오픈AI 등 생성형 검색의 침공",
                "dcf_target": "$205.00", "dcf_bear": "$160.00", "dcf_bull": "$245.00"
            },
            {
                "rank": "08", "ticker": "AVGO", "name": "Broadcom Inc", "sector": "Semiconductors", 
                "composite_score": "75.8", "grade": "📈 B급 (매수 고려)", "price": "172.50", "change": "2.1",
                "insight": "커스텀 AI 가속기 및 네트워킹 장비 수요가 폭발적입니다. VMware 인수를 통한 소프트웨어 성장도 기대됩니다.",
                "risk": "하이엔드 네트워킹 시장의 경쟁 증가.",
                "upside": "+21.7%", "mkt_cap": "$800B", "vol_ratio": "2.1x", "rsi": "67.8",
                "swot_s": "네트워킹 칩 및 무선 통신 기술력", "swot_w": "VMware 통합 과정의 불확실성",
                "swot_o": "빅테크향 커스텀 AI 가속기 시장 확대", "swot_t": "반도체 사이클의 하강 가능성",
                "dcf_target": "$210.00", "dcf_bear": "$165.00", "dcf_bull": "$250.00"
            },
            {
                "rank": "09", "ticker": "AMD", "name": "Advanced Micro Devices", "sector": "Semiconductors", 
                "composite_score": "74.2", "grade": "📈 B급 (매수 고려)", "price": "155.10", "change": "-2.3",
                "insight": "MI300 AI 가속기 출시를 통해 시장 점유율을 확대 중입니다. PC 및 데이터센터 수요 회복 수혜가 예상됩니다.",
                "risk": "NVIDIA와의 시장 점유율 경쟁 및 마진 압박.",
                "upside": "+35.4%", "mkt_cap": "$250B", "vol_ratio": "1.4x", "rsi": "45.2",
                "swot_s": "CPU 및 GPU 라인업의 강력한 경쟁력", "swot_w": "엔비디아 대비 낮은 AI 생태계 영향력",
                "swot_o": "AI 가속기 시장의 2순위 공급자 지위", "swot_t": "시장 성장이 공급 증가를 못 따라갈 리스크",
                "dcf_target": "$210.00", "dcf_bear": "$145.00", "dcf_bull": "$280.00"
            },
            {
                "rank": "10", "ticker": "COST", "name": "Costco Wholesale", "sector": "Retail", 
                "composite_score": "73.5", "grade": "📊 C급 (관망)", "price": "912.45", "change": "0.8",
                "insight": "멤버십 기반의 강력한 고객 충성도와 이커머스 성장이 안정적인 수익을 창출하고 있습니다.",
                "risk": "높은 PER 밸류에이션 수준 및 경쟁 심화.",
                "upside": "+10.7%", "mkt_cap": "$400B", "vol_ratio": "0.8x", "rsi": "51.1",
                "swot_s": "멤버십 모델을 통한 현금 흐름 안정성", "swot_w": "저성장 산업군의 특성",
                "swot_o": "글로벌 매장 확대 및 온라인 채널 강화", "swot_t": "월마트 등 대형 할인점의 멤버십 강화",
                "dcf_target": "$1010.00", "dcf_bear": "$880.00", "dcf_bull": "$1150.00"
            }
        ]
    # Provide default ETF flow data if missing
    if not data and filename == 'us_etf_flows.csv':
        return [
            {"ticker": "SPY", "name": "SPDR S&P 500", "flow_score": "82.5", "price_change_20d": "2.1"},
            {"ticker": "QQQ", "name": "Invesco QQQ", "flow_score": "78.4", "price_change_20d": "3.2"},
            {"ticker": "XLK", "name": "Technology", "flow_score": "91.2", "price_change_20d": "5.5"},
            {"ticker": "XLU", "name": "Utilities", "flow_score": "32.5", "price_change_20d": "-2.1"}
        ]
    return data or []

import re

def fetch_naver_movers(mover_type='rise', sosok=None):
    """
    Scrape Naver Finance for real-time market movers.
    types: 'rise' (gainers), 'volume' (quant), 'cap' (market sum)
    sosok: 0 for KOSPI, 1 for KOSDAQ (only for 'cap')
    """
    urls = {
        'rise': "https://finance.naver.com/sise/sise_rise.naver",
        'volume': "https://finance.naver.com/sise/sise_quant.naver",
        'cap': "https://finance.naver.com/sise/sise_market_sum.naver"
    }
    url = urls.get(mover_type, urls['rise'])
    if sosok is not None:
        url += f"?sosok={sosok}"
        
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # ETF brand names and keywords to exclude
    IGNORE_KEYWORDS = [
        'KODEX', 'TIGER', 'KBSTAR', 'ACE', 'SOL', 'HANARO', 'RISE', 'ARIRANG', 'KOSEF', 'WOORI', 'FOCUS', 'PLUS',
        '레버리지', '인버스', '2X', '선물', 'ETN', 'ETP'
    ]
    
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code != 200: return []
        
        # Simple regex parsing
        html = resp.text
        pattern = r'code=(\d{6})".*?class="tltle">(.*?)</a>'
        matches = re.findall(pattern, html)
        
        results = []
        count = 0
        # Process up to 50 matches to allow for filtering
        for code, name in matches[:50]:
            name_upper = name.upper()
            is_etf = any(kw in name_upper for kw in IGNORE_KEYWORDS)
            if is_etf and mover_type != 'cap': # Don't filter out market cap leaders, mostly stocks anyway
                continue
                
            results.append({
                "symbol": code,
                "name": name,
                "price": "0",
                "change": 0.0,
                "market": "KOSPI" if sosok == 0 else ("KOSDAQ" if sosok == 1 else "KOSPI"),
                "rank": str(count + 1)
            })
            count += 1
            if count >= 15: break # Keep top 15 after filtering
            
        return results
    except Exception as e:
        print(f"DEBUG: Naver scraping failed ({mover_type}): {e}")
        return []

import concurrent.futures

def fetch_single_ticker(ticker, headers):
    """Helper for parallel fetching"""
    try:
        # Handle KR stocks (6 digits) for Yahoo Finance if no suffix provided
        fetch_ticker = ticker
        if len(ticker) == 6 and ticker.isdigit() and "." not in ticker:
            fetch_ticker = f"{ticker}.KS"
        
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{fetch_ticker}?interval=1m&range=1d"
        resp = requests.get(url, headers=headers, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            meta = data.get('chart', {}).get('result', [{}])[0].get('meta', {})
            price = meta.get('regularMarketPrice')
            prev_close = meta.get('previousClose')
            
            if price is not None:
                return ticker, {
                    'price': round(price, 2),
                    'change': round(((price - prev_close) / prev_close) * 100, 2) if prev_close else 0
                }
    except Exception as e:
        print(f"DEBUG: Failed to fetch {ticker}: {e}")
    return ticker, None

def fetch_realtime_data(tickers):
    """Parallel fetch for Yahoo Finance v8 (Stable and fast)"""
    prices = {}
    if not tickers: return prices
    
    print(f"DEBUG: Parallel fetching prices for {len(tickers)} tickers")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }
    
    # Use ThreadPoolExecutor for parallel requests (Max 20 threads to avoid rate limiting)
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_ticker = {executor.submit(fetch_single_ticker, t, headers): t for t in tickers}
        for future in concurrent.futures.as_completed(future_to_ticker):
            ticker, result = future.result()
            if result:
                prices[ticker] = result
                # Support suffix lookups if needed
                if len(ticker) == 6 and ticker.isdigit():
                    prices[f"{ticker}.KS"] = result
                    prices[f"{ticker}.KQ"] = result
            
    return prices

# --- Dynamic AI Analysis Global Cache ---
AI_CACHE = {} # (date, symbol) -> analysis_dict
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    print(f"DEBUG: Gemini Config Error: {e}")
    model = None

def fetch_dynamic_ai_analysis(stocks_to_analyze):
    """
    Fetch SWOT, Insights, and DCF for a list of stocks using Gemini.
    """
    if not stocks_to_analyze or model is None: return {}
    
    today = datetime.now().strftime("%Y-%m-%d")
    results = {}
    
    # helper to normalize symbols for lookup
    def normalize(sym):
        return str(sym).split('.')[0].upper().strip()
    
    # Filter out what's already in cache
    needed = []
    for s in stocks_to_analyze:
        sym = s['symbol']
        norm_sym = normalize(sym)
        key = (today, norm_sym)
        if key in AI_CACHE:
            results[sym] = AI_CACHE[key]
            results[norm_sym] = AI_CACHE[key]
        else:
            needed.append(s)
            
    if not needed: return results

    print(f"DEBUG: Requesting dynamic AI analysis for {len(needed)} stocks: {[s['symbol'] for s in needed]}")
    
    # Create a mapping of names to symbols to help with matching
    name_to_sym = {normalize(s.get('name', '')): s['symbol'] for s in needed}
    
    prompt = f"""
    당신은 글로벌 증시 전문 AI 분석가입니다. 아래 제공된 한국 주식(KOSPI/KOSDAQ) 리스트에 대해 실시간 SWOT 분석과 투자 인사이트를 제공해주세요.
    
    [필수 지시사항]
    1. **제공된 모든 종목(Key)에 대해 빠짐없이 분석 결과를 반환하세요.**
    2. 소형주라 정보가 부족하다면, 해당 종목의 **섹터(업종) 동향이나 기술적 위치**를 기반으로 추론하여 작성하세요. (분석 포기 금지)
    3. 반드시 제공된 **6자리 종목코드**를 JSON 키로 사용하세요.
    4. 각 종목에 대해 아래 포맷을 엄수하세요:
       - insight: 최근 주가 흐름이나 수급 특징을 반영한 한줄평 (구체적일수록 좋음)
       - risk: 재무적 리스크 또는 차익실현 매물 가능성 등
       - swot_s, swot_w, swot_o, swot_t: 각각 1문장의 핵심 요약
       - dcf_target, dcf_bear, dcf_bull: 현재가 대비 현실적인 목표가 설정 (숫자만)
       - upside: 예상 상승 여력 (예: +15%)
    5. 결과는 오직 JSON 형식으로만 출력하세요.
    
    [분석 대상 리스트]
    {json.dumps([{ 'symbol': s['symbol'], 'name': s.get('name', 'N/A') } for s in needed], ensure_ascii=False)}
    
    [출력 예시]
    {{
        "005930": {{
            "insight": "반도체 업황 회복과 HBM 기대감으로 상승 추세가 지속되고 있습니다.",
            "risk": "외국인 매도세 전환 가능성",
            ...
        }}
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        content = response.text.replace('```json', '').replace('```', '').strip()
        ai_data = json.loads(content)
        
        print(f"DEBUG: Gemini returned analysis for {len(ai_data)} symbols (Target: {len(needed)})")
        
        for key, data in ai_data.items():
            norm_key = normalize(key)
            norm_key = normalize(key)
            
            # Map back to provided 6-digit symbol if AI used a name or dotted symbol
            final_sym = norm_key
            if norm_key in name_to_sym:
                final_sym = name_to_sym[norm_key]
            
            # Update cache and results
            cache_key = (today, final_sym)
            AI_CACHE[cache_key] = data
            results[final_sym] = data
            results[norm_key] = data 
            
        return results
    except Exception as e:
        print(f"DEBUG: Gemini AI Analysis Error (Parsing or request): {e}")
        return results

@app.route('/')
def index():
    resp = make_response(render_template('index.html'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.route('/kr')
def kr_index():
    resp = make_response(render_template('kr_index.html'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp

@app.route('/api/kr/report')
def get_kr_report():
    report_path = os.path.join(BASE_DIR, 'KR_Market_Analyst', 'kr_market', 'kr_market_daily_report.html')
    if os.path.exists(report_path):
        from flask import send_file
        return send_file(report_path)
    return "Report not found", 404



# --- Major US Analysis Persistent Knowledge (already defined globally at top) ---

@app.route('/api/us/smart-money')
def get_smart_money():
    data = load_csv('smart_money_picks_v2.csv')
    if not data: return jsonify([])

    # 1. Update prices
    try:
        top_tickers = [d['ticker'] for d in data[:15]]
        current_prices = fetch_realtime_data(top_tickers)
        for d in data:
            t = d['ticker']
            if t in current_prices:
                d['price'] = current_prices[t]['price']
                d['change'] = current_prices[t]['change']
    except Exception as e:
        print(f"DEBUG: US Price update error: {e}")

    # 2. Identify stocks needing AI enrichment
    needing_ai = []
    # Mix of ticker and symbol for robust lookup
    for d in data[:15]:
        ticker = d.get('ticker')
        if ticker not in major_us_analysis:
            needing_ai.append({'symbol': ticker, 'name': d.get('name', ticker)})
    
    # Batch enrichment
    dynamic_results = fetch_dynamic_ai_analysis(needing_ai)

    # 3. Final enrichment loop
    enriched = []
    for i, d in enumerate(data[:15]):
        ticker = d['ticker']
        norm_ticker = ticker.split('.')[0].upper()
        
        # Try major_us_analysis -> dynamic_results -> generic fallback
        details = major_us_analysis.get(ticker)
        if not details:
            details = dynamic_results.get(ticker)
            if not details:
                details = dynamic_results.get(norm_ticker)
        
        if not details:
            details = {
                "insight": f"{ticker} - 시장 지배력과 기술적 모멘텀이 유효한 구간입니다.",
                "risk": "거시 경제 변동성 및 금리 시나리오 영향.",
                "upside": "+15~20%", "mkt_cap": "-", "vol_ratio": "1.0x", "rsi": "55-60",
                "swot_s": "브랜드 파워 및 시장 지배력", "swot_w": "높은 밸류에이션 부담",
                "swot_o": "AI 및 디지털 전환 수혜", "swot_t": "규제 강화 및 경쟁 심화",
                "dcf_target": d.get('price', '0'), "dcf_bear": "-", "dcf_bull": "-"
            }
        
        # Merge and clean
        stock_obj = {**d, **details}
        stock_obj['rank'] = str(i+1).zfill(2)
        stock_obj['score'] = float(d.get('score', d.get('composite_score', 85)))
        stock_obj['signal'] = "적극 매수" if i < 3 else ("매수" if i < 8 else "중립")
        
        enriched.append(stock_obj)

    response = jsonify(enriched)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/api/kr/smart-money')
def get_kr_smart_money():
    # Load all stocks from daily data
    kr_data_path = os.path.join(BASE_DIR, 'KR_Market_Analyst/kr_market/kr_daily_data.json')
    kr_data = {}
    if os.path.exists(kr_data_path):
        try:
            with open(kr_data_path, 'r', encoding='utf-8') as f:
                kr_data = json.load(f)
        except Exception:
            pass
    
    # Initialize lists (may be empty if file missing)
    leaders = kr_data.get('leaders', [])
    gainers = kr_data.get('gainers', [])
    volume = kr_data.get('volume', [])

    # Parallel Scrape if data is missing (Primary Logic for Vercel)
    if not gainers or not volume or not leaders:
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # Submit all scraping tasks
                f1 = executor.submit(fetch_naver_movers, 'rise', 0)   # Gainers KOSPI
                f2 = executor.submit(fetch_naver_movers, 'rise', 1)   # Gainers KOSDAQ
                f3 = executor.submit(fetch_naver_movers, 'volume', 0) # Volume KOSPI
                f4 = executor.submit(fetch_naver_movers, 'volume', 1) # Volume KOSDAQ
                f5 = executor.submit(fetch_naver_movers, 'cap', 0)    # Leaders KOSPI
                f6 = executor.submit(fetch_naver_movers, 'cap', 1)    # Leaders KOSDAQ
                
                # Collect results
                g_kospi = f1.result() or []
                g_kosdaq = f2.result() or []
                v_kospi = f3.result() or []
                v_kosdaq = f4.result() or []
                l_kospi = f5.result() or []
                l_kosdaq = f6.result() or []

            # Merge and assign
            gainers = (g_kospi[:5] + g_kosdaq[:5])
            volume = (v_kospi[:5] + v_kosdaq[:5])
            leaders_kospi = l_kospi[:10]
            leaders_kosdaq = l_kosdaq[:10]
            
            # Use Leaders KOSPI as default 'leaders' list
            leaders = leaders_kospi
            
        except Exception as e:
            print(f"DEBUG: Live mover parallel fetch error: {e}")
            leaders_kospi = []
            leaders_kosdaq = []
    else:
        # If loaded from JSON, just split leaders if not already split
        leaders_kospi = leaders
        leaders_kosdaq = leaders # Fallback if no specific data

    # Try to fetch real-time prices for ALL active lists
    try:
        all_stocks_to_fetch = []
        for s in leaders_kospi: all_stocks_to_fetch.append(f"{s['symbol']}.KS")
        for s in leaders_kosdaq: all_stocks_to_fetch.append(f"{s['symbol']}.KQ")
        for s in gainers: 
            suffix = ".KS" if s.get('market') == "KOSPI" else (".KQ" if s.get('market') == "KOSDAQ" else ".KS")
            all_stocks_to_fetch.append(f"{s['symbol']}{suffix}")
        for s in volume:
            suffix = ".KS" if s.get('market') == "KOSPI" else (".KQ" if s.get('market') == "KOSDAQ" else ".KS")
            all_stocks_to_fetch.append(f"{s['symbol']}{suffix}")
        
        all_tickers = list(set(all_stocks_to_fetch))
        current_prices = fetch_realtime_data(all_tickers)
        
        # Map values back
        for d_list in [leaders_kospi, leaders_kosdaq, gainers, volume, leaders]:
            for d in d_list:
                sym = d['symbol']
                # Try with .KS then .KQ then raw
                for suffix in ['.KS', '.KQ', '']:
                    lookup = f"{sym}{suffix}" if suffix else sym
                    if lookup in current_prices:
                        d['price'] = f"{int(current_prices[lookup]['price']):,}"
                        d['change'] = current_prices[lookup]['change']
                        break
    except Exception as e:
        print(f"DEBUG: KR Price update error: {e}")

    # PRE-FETCH AI ANALYSIS
    try:
        all_unique_stocks = []
        seen = set()
        # PRIORITIZE Gainers and Volume stocks for AI analysis
        for d_list in [gainers, volume, leaders_kospi, leaders_kosdaq]:
            for s in d_list:
                if s['symbol'] not in seen:
                    all_unique_stocks.append(s)
                    seen.add(s['symbol'])
        
        # Filters based on MAJOR_ANALYSIS_KR
        needing_dynamic = [s for s in all_unique_stocks if s['symbol'] not in MAJOR_ANALYSIS_KR]
        
        # Safe limit for Vercel timeout (Increased back to 20 as parallel scraping saved time)
        needing_dynamic = needing_dynamic[:20]
        print(f"DEBUG: KR AI processing {len(needing_dynamic)} stocks dynamically. Symbols: {[s['symbol'] for s in needing_dynamic]}")
        dynamic_results = fetch_dynamic_ai_analysis(needing_dynamic)
        print(f"DEBUG: KR AI Results Count: {len(dynamic_results)}")
    except Exception as e:
        print(f"DEBUG: KR AI Batch Analysis Error: {e}")
        dynamic_results = {}

    def enrich_list(stock_list):
        enriched = []
        for i, s in enumerate(stock_list):
            symbol = s['symbol']
            # Try MAJOR_ANALYSIS_KR -> dynamic_results -> absolute fallback
            details = MAJOR_ANALYSIS_KR.get(symbol)
            if not details:
                # Try flexible mapping for dynamic results
                details = dynamic_results.get(symbol)
                if not details:
                    # Try stripped symbol
                    details = dynamic_results.get(symbol.split('.')[0])
            
            if not details:
                is_gainer = any(s['symbol'] == g['symbol'] for g in gainers)
                details = {
                    "insight": f"{s['name']}: { '수급 집중으로 인한 강세 흐름이 포착되었습니다.' if is_gainer else '안정적인 실적 기반의 우상향 기조가 유효합니다.' }",
                    "risk": "단기 급등에 따른 차익 실현 및 변동성 유의.",
                    "upside": "+10~15%", "mkt_cap": "-", "vol_ratio": "1.2x", "rsi": "50-60",
                    "swot_s": "견고한 시장 지위", "swot_w": "원자재 및 거시 경제 민감도",
                    "swot_o": "신성장 동력 확보 기회", "swot_t": "업황 경쟁 심화",
                    "dcf_target": s['price'], "dcf_bear": "-", "dcf_bull": "-"
                }

            # Safe parsing for price/change if they come as strings with commas/symbols
            try:
                price_clean = s['price']
                change_clean = float(str(s.get('change', '0')).replace('%', '').replace('+', ''))
            except:
                price_clean = s.get('price', '0')
                change_clean = 0.0

            enriched.append({
                "rank": str(i+1).zfill(2),
                "ticker": s['name'],
                "symbol": symbol,
                "name": s['name'],
                "sector": s.get('market', 'KOSPI'),
                "score": round(90.0 - (i * 0.5), 1), # Mock score based on rank
                "signal": "적극 매수" if i < 3 else ("매수" if i < 7 else "중립"),
                "price": price_clean,
                "change": change_clean,
                **details
            })
        return enriched

    response_data = {
        "leaders": enrich_list(leaders_kospi), # Default for main tab
        "leaders_kospi": enrich_list(leaders_kospi),
        "leaders_kosdaq": enrich_list(leaders_kosdaq),
        "gainers": enrich_list(gainers),
        "volume": enrich_list(volume)
    }

    response = jsonify(response_data)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

import xml.etree.ElementTree as ET
from datetime import datetime

@app.route('/api/kr/news')
def get_kr_news():
    try:
        # Google News RSS for "주식" (Stocks) in Korean
        url = "https://news.google.com/rss/search?q=%EC%A3%BC%EC%8B%9D&hl=ko&gl=KR&ceid=KR:ko"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return jsonify([])

        root = ET.fromstring(response.content)
        news_items = []
        
        for item in root.findall('.//item')[:15]:
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            source = item.find('source').text if item.find('source') is not None else "뉴스"
            description = item.find('description').text if item.find('description') is not None else ""
            
            # Clean description (remove HTML tags)
            if description:
                description = ET.fromstring(f"<root>{description}</root>").itertext()
                description = "".join(description).strip()
                # Limit length
                if len(description) > 100:
                    description = description[:100] + "..."
            
            # Clean title
            if " - " in title:
                title = title.rsplit(" - ", 1)[0]
                
            news_items.append({
                "title": title,
                "url": link,
                "date": pub_date,
                "source": source,
                "summary": description
            })
            
        return jsonify(news_items)
    except Exception as e:
        print(f"Error fetching news: {e}")
        return jsonify([])

@app.route('/api/kr/ipo')
def get_kr_ipo():
    try:
        # Fetching IPO info from a public source or using a structured real-time mock for demo
        # In a real production, we'd scrape kind.krx.co.kr or use a finance API
        # For now, providing structured data that can be easily connected to a scraper
        ipo_data = [
            {
                "name": "에이치비인베스트먼트",
                "status": "청약종료",
                "manager": "NH투자증권",
                "price": "3,400원",
                "date": "01.29"
            },
            {
                "name": "우진엔텍",
                "status": "상장예정",
                "manager": "KB증권",
                "price": "5,300원",
                "date": "01.30"
            },
            {
                "name": "포스뱅크",
                "status": "청약중",
                "manager": "하나증권",
                "price": "18,000원",
                "date": "01.29"
            },
            {
                "name": "현대힘스",
                "status": "청약예정",
                "manager": "미래에셋증권",
                "price": "7,300원",
                "date": "02.05"
            }
        ]
        return jsonify(ipo_data)
    except Exception as e:
        return jsonify([])

@app.route('/api/us/macro-analysis')
def get_macro_analysis():
    # Defensive import inside function to avoid start-up crash
    try:
        from us_market.macro_analyzer import MacroAnalyzer
        macro = MacroAnalyzer(data_dir=DATA_DIR)
        # If the file exists, we can return it, or use the generator
        return jsonify(load_json('us_macro_analysis.json'))
    except Exception as e:
        print(f"DEBUG: Macro analysis import error: {e}")
        return jsonify(load_json('us_macro_analysis.json'))

@app.route('/api/us/sector-heatmap')
def get_sector_heatmap():
    return jsonify(load_json('sector_heatmap.json'))

@app.route('/api/us/etf-flows')
def get_etf_flows():
    return jsonify(load_csv('us_etf_flows.csv'))

@app.route('/api/us/options-flow')
def get_options_flow():
    return jsonify(load_json('options_flow.json'))

@app.route('/api/us/economic-calendar')
def get_calendar():
    return jsonify(load_json('economic_calendar.json'))

@app.route('/api/us/ai-summary/<ticker>')
def get_ai_summary(ticker):
    summaries = load_json('ai_stock_summaries.json')
    summary = summaries.get(ticker, "No summary available.")
    return jsonify({'ticker': ticker, 'summary': summary})

@app.route('/api/us/daily-report')
@app.route('/daily-report')
def get_daily_report():
    report_path = os.path.join(DATA_DIR, 'us_market_morning_report.html')
    
    # 1. First, check if the pre-generated file exists
    if os.path.exists(report_path):
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                resp = make_response(f.read())
                resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                resp.headers['Pragma'] = 'no-cache'
                resp.headers['Expires'] = '0'
                return resp
        except Exception as e:
            print(f"DEBUG: Error reading existing report: {e}")

    # 2. Fallback to live generation if file doesn't exist or failed to read
    try:
        from us_market.daily_report_generator import USDailyReportGenerator
        generator = USDailyReportGenerator(data_dir=DATA_DIR)
        return generator.run()
    except Exception as e:
        return f"<h1>Error generating report</h1><p>{str(e)}</p>", 500

@app.route('/api/us/realtime-prices')
def get_realtime_prices():
    tickers = request.args.get('tickers', 'SPY,QQQ,NVDA,AAPL,TSLA').split(',')
    try:
        return jsonify(fetch_realtime_data(tickers))
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/debug')
def debug_server():
    smart_money_data = load_csv('smart_money_picks_v2.csv')
    debug_info = {
        "BASE_DIR": BASE_DIR,
        "DATA_DIR": DATA_DIR,
        "CWD": os.getcwd(),
        "csv_exists": os.path.exists(os.path.join(DATA_DIR, 'smart_money_picks_v2.csv')),
        "smart_money_keys": list(smart_money_data[0].keys()) if smart_money_data else [],
        "smart_money_count": len(smart_money_data),
        "first_ticker": smart_money_data[0].get('ticker') if smart_money_data else None,
        "first_exchange": smart_money_data[0].get('exchange') if smart_money_data else None
    }
    return jsonify(debug_info)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
