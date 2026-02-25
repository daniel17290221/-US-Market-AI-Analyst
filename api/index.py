from flask import Flask, render_template, jsonify, request, make_response
from typing import Dict
import csv
import json
import os
import requests
import sys
from datetime import datetime
import xml.etree.ElementTree as ET
# import google.generativeai as genai (Removed to stay under 250MB size limit)
from dotenv import load_dotenv

load_dotenv()

# Build: 2026-02-10 15:32 (KST) - Case-insensitive API Key Fix
AI_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("google_api_key")

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

# Determine template folder location (Vercel uses api/templates, local uses root templates)
# Determine template folder location (Vercel uses api/templates, local uses root templates)
if os.environ.get('VERCEL'):
    TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
else:
    TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

if not os.path.exists(TEMPLATE_DIR):
    TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')

app = Flask(__name__, 
            template_folder=TEMPLATE_DIR,
            static_folder=os.path.join(BASE_DIR, 'assets'),
            static_url_path='/assets')

# 전역 요청 추적기 (Vercel 로그 확인용)
@app.before_request
def debug_all_requests():
    # 모든 ACP 관련 경로나 POST 요청을 감시
    path = request.path.lower()
    if 'acp' in path or request.method == 'POST':
        print("\n" + "!"*60)
        print(f"!!! ACP DETECTED: {request.method} {request.path} !!!")
        print(f"!!! From: {request.remote_addr} | Payload Type: {request.content_type} !!!")
        print("!"*60 + "\n")

# CORS 허용 (Virtual Protocol 대시보드 연동용)
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

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
            result = data.get('chart', {}).get('result')
            
            if result:
                meta = result[0].get('meta', {})
                price = meta.get('regularMarketPrice')
                prev_close = meta.get('chartPreviousClose', meta.get('previousClose')) # Try both keys
                
                if price is not None and prev_close is not None:
                     change_pct = ((price - prev_close) / prev_close) * 100 if prev_close != 0 else 0.0
                     return ticker, {
                        'price': price, # Keep as float, formatted later
                        'change': round(change_pct, 2)
                    }
    except Exception as e:
        print(f"DEBUG: Failed to fetch {ticker}: {e}")
        import traceback
        traceback.print_exc()
    return ticker, None

def fetch_realtime_data(tickers):
    """Batch fetch from Yahoo Quote API with individual fallback and chart API retry"""
    prices = {}
    if not tickers: return prices
    
    # Normalize tickers
    tickers = [t.strip().upper() for t in tickers if t]
    print(f"DEBUG: Starting price fetch for {len(tickers)} tickers: {tickers}")
    
    headers_list = [
        {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'},
        {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    ]
    
    # 1. Try Batch Fetch (Quote API V7)
    for base_url in ["https://query1.finance.yahoo.com/v7/finance/quote", "https://query2.finance.yahoo.com/v7/finance/quote"]:
        if len(prices) >= len(tickers): break
        symbols_str = ",".join(tickers)
        for header in headers_list:
            try:
                resp = requests.get(f"{base_url}?symbols={symbols_str}", headers=header, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get('quoteResponse', {}).get('result', [])
                    for quote in results:
                        ticker = quote.get('symbol', '').upper()
                        price = quote.get('regularMarketPrice')
                        change = quote.get('regularMarketChangePercent')
                        if price is not None:
                            prices[ticker] = {'price': price, 'change': round(change, 2) if change is not None else 0.0}
                            if "." in ticker: prices[ticker.split('.')[0]] = prices[ticker]
                    if len(prices) > 0: break
            except: continue
        if len(prices) > 0: break

    # 2. Individual Fallback for missing tickers (using Chart API - often more stable)
    missing = [t for t in tickers if t not in prices]
    if missing:
        print(f"DEBUG: Using individual fallback for {len(missing)} tickers: {missing}")
        for ticker in missing:
            for header in headers_list:
                try:
                    # Chart API V8
                    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=1d"
                    resp = requests.get(url, headers=header, timeout=3)
                    if resp.status_code == 200:
                        data = resp.json()
                        meta = data.get('chart', {}).get('result', [{}])[0].get('meta', {})
                        price = meta.get('regularMarketPrice')
                        prev_close = meta.get('previousClose')
                        
                        if price:
                            change = 0.0
                            if prev_close and prev_close != 0:
                                change = round(((price - prev_close) / prev_close) * 100, 2)
                            prices[ticker] = {'price': price, 'change': change}
                            break
                except: continue

    print(f"DEBUG: Final fetch result: {len(prices)}/{len(tickers)} tickers found.")
    return prices

# --- Dynamic AI Analysis Global Cache ---
AI_CACHE = {} # (date, symbol) -> analysis_dict
AI_KEY = os.getenv("GOOGLE_API_KEY")
# model = genai.GenerativeModel(...) (Removed for size)

def fetch_dynamic_ai_analysis(stocks_to_analyze):
    """
    Fetch SWOT, Insights, and DCF for a list of stocks using Gemini.
    """
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
            
    if not needed or not AI_KEY: return results
    
    print(f"DEBUG: Requesting dynamic AI analysis for {len(needed)} stocks: {[s['symbol'] for s in needed]}")
    
    # Create a mapping of names to symbols to help with matching
    name_to_sym = {normalize(s.get('name', '')): s['symbol'] for s in needed}
    
    prompt = f"""
    당신은 글로벌 증시 전문 AI 분석가입니다. 아래 한국 주식 리스트에 대해 실시간 SWOT 분석과 투자 인사이트를 제공해주세요.
    
    [필수 지시사항]
    1. **제공된 20개 내외의 모든 종목(Key)에 대해 분석 결과를 반환하세요. (누락 금지)**
    2. 답변은 **핵심만 간결하게(Short & Impactful)** 작성하여 생성 시간을 단축하세요.
    3. 소형주라 정보가 없으면 섹터 동향으로 추론하여 답하세요.
    4. 포맷 준수:
       - insight: 1문장 핵심 한줄평
       - risk: 최대 리스크 1개
       - swot_s/w/o/t: 각각 핵심 키워드 위주의 짧은 문장
       - dcf_target/bear/bull: 숫자만
       - upside: 예: +15%
    5. JSON 형식만 출력.
    
    [분석 대상]
    {json.dumps([{ 'symbol': s['symbol'], 'name': s.get('name', 'N/A') } for s in needed], ensure_ascii=False)}
    
    [예시]
    {{ "005930": {{ "insight": "HBM 공급 확대 기대", "risk": "재고 부담", "swot_s": "시장 지배력", ... }} }}
    """
    
    try:
        # Use direct REST API to avoid heavy SDK dependencies (>250MB limit)
        # Use latest stable model endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={AI_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        
        # Reduced timeout to 8s to prevent total page hang
        response = requests.post(url, json=payload, timeout=8)
        if response.status_code != 200:
            print(f"DEBUG: Gemini REST API Error: {response.text}")
            return results
            
        res_data = response.json()
        content = res_data['candidates'][0]['content']['parts'][0]['text']
        ai_data = json.loads(content)
        
        print(f"DEBUG: Gemini REST returned analysis for {len(ai_data)} symbols")
        
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

@app.route('/', methods=['GET', 'POST'])
def index():
    # 만약 루트로 POST 요청(ACP 등)이 들어오면 핸들러로 전달
    if request.method == 'POST':
        return virtuals_acp_handler()
        
    resp = make_response(render_template('index.html'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, public, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.route('/kr')
def kr_index():
    resp = make_response(render_template('kr_index.html'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, public, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.route('/dividend')
def dividend_portfolio():
    try:
        resp = make_response(render_template('dividend_portfolio.html'))
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, public, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        return resp
    except Exception as e:
        print(f"CRITICAL: Dividend Template Error: {str(e)}")
        return f"<h1>Internal Server Error</h1><p>템플릿 로드 중 오류가 발생했습니다: {str(e)}</p><p>Path: {TEMPLATE_DIR}</p>", 500

@app.route('/api/kr/report')
def get_kr_report():
    # Attempt 1: Root-based absolute path
    path1 = os.path.join(BASE_DIR, 'KR_Market_Analyst', 'kr_market', 'kr_market_daily_report.html')
    # Attempt 2: Alternative root (some environments use a different base)
    path2 = os.path.join(os.getcwd(), 'KR_Market_Analyst', 'kr_market', 'kr_market_daily_report.html')
    # Attempt 3: Deep relative from api/ folder
    path3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'KR_Market_Analyst', 'kr_market', 'kr_market_daily_report.html')
    
    report_path = None
    for p in [path1, path2, path3]:
        if os.path.exists(p):
            report_path = p
            break

    if report_path:
        try:
            from flask import send_file
            resp = make_response(send_file(report_path, mimetype='text/html'))
            resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, public, max-age=0'
            resp.headers['Pragma'] = 'no-cache'
            resp.headers['Expires'] = '0'
            return resp
        except Exception as e:
            return f"Error opening report: {str(e)}", 500
            
    return f"데일리 리포트 파일을 생성 중이거나 찾을 수 없습니다. (Path Tried: {path1})", 404



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
            t = d.get('ticker', '').strip().upper()
            if t in current_prices:
                d['price'] = current_prices[t]['price']
                d['change'] = current_prices[t]['change']
            elif t.split('.')[0] in current_prices:
                # Suffix-less fallback
                base_t = t.split('.')[0]
                d['price'] = current_prices[base_t]['price']
                d['change'] = current_prices[base_t]['change']
    except Exception as e:
        print(f"DEBUG: US Price update error: {e}")

    # 2. Load Pre-computed AI Analysis
    precomputed_ai = load_json('us_ai_analysis.json')
    
    # 3. Identify stocks needing dynamic AI enrichment (fallback)
    needing_ai = []
    for d in data[:15]:
        ticker = d.get('ticker')
        if ticker not in major_us_analysis and ticker not in precomputed_ai:
            needing_ai.append({'symbol': ticker, 'name': d.get('name', ticker)})
    
    # Optional Batch enrichment for missing ones (limit to 5 for speed)
    dynamic_results = precomputed_ai.copy()
    if needing_ai:
        live_ai = fetch_dynamic_ai_analysis(needing_ai[:5])
        dynamic_results.update(live_ai)

    # 4. Final enrichment loop
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

# --- Google News RSS Fetcher ---
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
                # Source is usually in title "Title - Source"
                source = "Google News"
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0]
                    source = parts[1]
                
                # Format Date
                try:
                    # Fri, 30 Jan 2026 07:00:00 GMT
                    dt = datetime.strptime(pubDate, "%a, %d %b %Y %H:%M:%S %Z")
                    date_str = dt.strftime("%Y.%m.%d %H:%M")
                except:
                    date_str = pubDate

                items.append({
                    "title": title,
                    "url": link,
                    "date": date_str,
                    "source": source
                })
            return items
    except Exception as e:
        print(f"RSS Fetch Error: {e}")
    return []

# Removed redundant k-news and k-ipo routes

@app.route('/api/kr/market-data')
def get_kr_market_data():
    # Load all stocks from daily data
    kr_data_path = os.path.join(BASE_DIR, 'KR_Market_Analyst/kr_market/kr_daily_data.json')
    kr_data = {}
    if os.path.exists(kr_data_path):
        try:
            with open(kr_data_path, 'r', encoding='utf-8') as f:
                kr_data = json.load(f)
        except Exception:
            pass
    
    # Load Lists from JSON (Defaulting to empty if missing)
    leaders_kospi = kr_data.get('leaders_kospi', [])
    leaders_kosdaq = kr_data.get('leaders_kosdaq', [])
    gainers = kr_data.get('gainers', [])
    volume = kr_data.get('volume', [])
    
    # Load Pre-calculated AI Analysis
    precomputed_ai = kr_data.get('ai_analysis', {})
    print(f"DEBUG: Loaded {len(precomputed_ai)} pre-calculated AI insights")

    # Fallback to scraping only if JSON is completely empty (Rare case)
    if not leaders_kospi and not leaders_kosdaq:
        try:
            print("DEBUG: JSON empty, falling back to live scraping...")
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
            gainers = (g_kospi[:10] + g_kosdaq[:10]) 
            volume = (v_kospi[:10] + v_kosdaq[:10])
            leaders_kospi = l_kospi[:10]
            leaders_kosdaq = l_kosdaq[:10]
            
        except Exception as e:
            print(f"DEBUG: Live mover parallel fetch error: {e}")
            leaders_kospi = []
            leaders_kosdaq = []

    # Map Values Back (Leaders, Gainers, Volume) & Price Update
    try:
        all_stocks_to_fetch = []
        # Gather all symbols
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
        
        # Update lists with real-time data
        for d_list in [leaders_kospi, leaders_kosdaq, gainers, volume]:
            for d in d_list:
                sym = d['symbol']
                # Try suffixes matching logic
                found = False
                for suffix in ['.KS', '.KQ', '']:
                    lookup = f"{sym}{suffix}" if suffix else sym
                    if lookup in current_prices:
                        # Yahoo returns float, we need to format it or keep it raw for later?
                        # enrich_list expects string or raw. 
                        # Let's save formatted string to match old behavior
                        price_val = current_prices[lookup]['price']
                        d['price'] = f"{int(price_val):,}"
                        d['change'] = current_prices[lookup]['change']
                        found = True
                        break
    except Exception as e:
        print(f"DEBUG: KR Price update error: {e}")
        import traceback
        traceback.print_exc()

    # Use Pre-calculated AI Analysis directly
    dynamic_results = precomputed_ai.copy()
    
    # Identify missing stocks for live fetch (fallback)
    all_unique_stocks = []
    seen = set()
    for d_list in [leaders_kospi, leaders_kosdaq, gainers, volume]:
        for s in d_list:
            if s['symbol'] not in seen:
                all_unique_stocks.append(s)
                seen.add(s['symbol'])
    
    needing_dynamic = []
    for s in all_unique_stocks:
        sym = s['symbol']
        if sym not in MAJOR_ANALYSIS_KR and sym not in dynamic_results:
            needing_dynamic.append(s)
    
    # Fetch missing only (Safe limit)
    if needing_dynamic:
        needing_dynamic = needing_dynamic[:5] 
        print(f"DEBUG: Live Fetching missing AI for {len(needing_dynamic)} stocks: {[s['symbol'] for s in needing_dynamic]}")
        live_results = fetch_dynamic_ai_analysis(needing_dynamic)
        dynamic_results.update(live_results)

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

    # Live Fallback for IPO if JSON is just a placeholder
    ipo_list = kr_data.get('ipo_news', [])
    if not ipo_list or (len(ipo_list) == 1 and "업데이트" in ipo_list[0].get('name', '')):
        ipo_list = fetch_google_news_rss("공모주+청약+일정+상장")
        # Format RSS output to match IPO structure if needed
        for item in ipo_list:
            if 'status' not in item: item['status'] = "뉴스"
            if 'name' not in item: item['name'] = item['title']

    response_data = {
        "date": kr_data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S KST')),
        "leaders": enrich_list(leaders_kospi), # Default for main tab
        "leaders_kospi": enrich_list(leaders_kospi),
        "leaders_kosdaq": enrich_list(leaders_kosdaq),
        "gainers": enrich_list(gainers),
        "volume": enrich_list(volume),
        "sector_heatmap": kr_data.get('sector_heatmap', []),
        "ipo_news": ipo_list,
        "market_news": fetch_google_news_rss("국내+증시+시황+마감+브리핑") # Unified news fetch
    }

    response = jsonify(response_data)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

import xml.etree.ElementTree as ET
from datetime import datetime

@app.route('/api/kr/news')
def get_kr_news():
    # Use more specific and fresh search terms
    return jsonify(fetch_google_news_rss("국내+증시+시황+마감+브리핑"))

@app.route('/api/kr/ipo')
def get_kr_ipo():
    try:
        kr_data_path = os.path.join(BASE_DIR, 'KR_Market_Analyst/kr_market/kr_daily_data.json')
        if os.path.exists(kr_data_path):
            with open(kr_data_path, 'r', encoding='utf-8') as f:
                kr_data = json.load(f)
                ipo_list = kr_data.get('ipo_news', [])
                # If data is just a placeholder, use live fallback
                if not ipo_list or (len(ipo_list) == 1 and "업데이트" in ipo_list[0].get('name', '')):
                     return jsonify(fetch_google_news_rss("공모주+청약+일정+상장"))
                return jsonify(ipo_list)
        
        # Fallback to RSS if JSON not ready
        return jsonify(fetch_google_news_rss("공모주+청약+일정+상장"))
    except Exception as e:
        print(f"Error fetching KR IPO: {e}")
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

@app.route('/ads.txt')
def serve_ads_txt():
    content = "google.com, pub-4995156883730033, DIRECT, f08c47fec0942fa0"
    return make_response(content, 200, {'Content-Type': 'text/plain'})

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

    # 2. Fallback to live generation if file doesn't exist
    try:
        from us_market.daily_report_generator import USDailyReportGenerator
        generator = USDailyReportGenerator(data_dir=DATA_DIR)
        return generator.run()
    except ImportError:
        return "<h1>Report Generation Unavailable</h1><p>Full analysis libraries are excluded from Vercel to stay under the 250MB limit. Please check GitHub Actions for generated reports.</p>", 503
    except Exception as e:
        return f"<h1>Error generating report</h1><p>{str(e)}</p>", 500

@app.route('/api/cron/update')
def cron_update():
    """Endpoint for Vercel Cron to trigger data refresh for both US and KR markets"""
    results = {}
    
    # 1. Update US Market Report
    try:
        from us_market.daily_report_generator import USDailyReportGenerator
        us_gen = USDailyReportGenerator(data_dir=DATA_DIR)
        us_gen.run()
        results["us"] = "success"
    except ImportError:
        results["us"] = "skipped: dependencies not available on Vercel"
    except Exception as e:
        results["us"] = f"error: {str(e)}"

    # 2. Update KR Market Data and Report
    try:
        # Resolve KR paths correctly
        kr_base = os.path.join(BASE_DIR, 'KR_Market_Analyst')
        kr_market_dir = os.path.join(kr_base, 'kr_market')
        
        from KR_Market_Analyst.kr_market.kr_data_manager import KRDataManager
        from KR_Market_Analyst.kr_market.kr_report_generator import KRDailyReportGenerator
        
        # Step A: Collect Data
        data_manager = KRDataManager(output_dir=kr_market_dir)
        data_manager.collect_all()
        
        # Step B: Generate Report
        report_gen = KRDailyReportGenerator(data_dir=kr_market_dir)
        report_gen.run()
        
        results["kr"] = "success"
    except ImportError:
        results["kr"] = "skipped: dependencies not available on Vercel"
    except Exception as e:
        results["kr"] = f"error: {str(e)}"

    status_code = 200 if all(v == "success" for v in results.values()) else 207
    return jsonify({"status": "completed", "details": results}), status_code

@app.route('/api/us/realtime-prices')
def get_realtime_prices():
    tickers = request.args.get('tickers', 'SPY,QQQ,NVDA,AAPL,TSLA').split(',')
    try:
        return jsonify(fetch_realtime_data(tickers))
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/chart-data')
def get_universal_chart_data():
    symbol = request.args.get('symbol', '005930')
    market = request.args.get('market', 'KR') # KR or US
    
    if not symbol:
        return jsonify([])

    # Removed yfinance for Vercel stability
    if market.upper() == 'US':
        ticker_sym = symbol.upper()
    else:
        # Default KR logic
        ticker_sym = f"{symbol}.KS"
    
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
                    # Skip if any essential data is None
                    if opens[i] is None or closes[i] is None: continue
                    
                    dt = datetime.fromtimestamp(timestamps[i])
                    chart_data.append({
                        "time": dt.strftime('%Y-%m-%d'),
                        "open": float(opens[i]),
                        "high": float(highs[i]),
                        "low": float(lows[i]),
                        "close": float(closes[i]),
                        "volume": float(volumes[i] or 0)
                    })
                return chart_data
        except Exception as e:
            print(f"Error in fetch_yahoo_history: {e}")
        return []

    try:
        data = fetch_yahoo_history(ticker_sym)
        # If KR and empty, try KOSDAQ
        if not data and market.upper() == 'KR':
            data = fetch_yahoo_history(f"{symbol}.KQ")
            
        return jsonify(data)
    except Exception as e:
        print(f"Error fetching chart data for {symbol}: {e}")
        return jsonify([])

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

# In-memory rate limit store
portfolio_rate_limit = {}

def get_exchange_rate():
    try:
        # Use Yahoo Finance REST API directly instead of yfinance to save space
        url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=KRW=X"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            result = data.get('quoteResponse', {}).get('result', [])
            if result:
                return float(result[0].get('regularMarketPrice', 1450.0))
        return 1450.0 
    except Exception as e:
        print(f"Exchange Rate Error: {e}")
        return 1450.0

@app.route('/api/generate-portfolio', methods=['POST'])
def generate_portfolio():
    # 1. Rate Limiting Check
    client_ip = request.remote_addr
    req_json = request.get_json(silent=True) or {}
    dev_mode = req_json.get('dev_mode', False) or request.args.get('dev_mode') == 'vibecoding'
    
    is_local = client_ip in ['127.0.0.1', 'localhost', '::1']
    
    if not dev_mode and not is_local:
        today = datetime.now().strftime("%Y-%m-%d")
        if client_ip not in portfolio_rate_limit:
            portfolio_rate_limit[client_ip] = {'date': today, 'count': 0}
        if portfolio_rate_limit[client_ip]['date'] != today:
            portfolio_rate_limit[client_ip] = {'date': today, 'count': 0}
            
        if portfolio_rate_limit[client_ip]['count'] >= 3: # Restored to 3 as per user request
            return jsonify({
                "error": "Rate limit exceeded",
                "message": "하루 3회 생성 제한에 도달했습니다. 내일 다시 시도해주세요."
            }), 429
        portfolio_rate_limit[client_ip]['count'] += 1

    # 2. Input Validation & Market Data
    data = req_json
    theme = data.get('theme', 'Monthly Dividend')
    risk = data.get('risk', 'Balanced')
    origin_amount_str = str(data.get('amount', '100000000'))
    try:
        amount_krw = int(origin_amount_str.replace(',', '').replace('원', ''))
    except:
        amount_krw = 100000000
    
    strategy = data.get('strategy', 'Yield Maximization')
    market = data.get('market', 'US') # US, KR, MIX
    etf_mode = data.get('etf_mode', False)
    
    exchange_rate = get_exchange_rate()
    amount_usd = amount_krw / exchange_rate

    # 3. AI Generation via Direct REST API (to save memory/deployment size)
    try:
        # Robust API Key retrieval: try all case variants
        api_key = (os.environ.get('GOOGLE_API_KEY') or os.getenv('GOOGLE_API_KEY') or 
                   os.environ.get('google_api_key') or os.getenv('google_api_key') or AI_KEY)
        
        if not api_key:
            # Debugging: List available API-related keys (WITHOUT values) to help the user
            available_keys = [k for k in os.environ.keys() if 'API' in k.upper() or 'KEY' in k.upper()]
            return jsonify({
                "error": "API Key missing", 
                "message": f"Google API Key가 설정되지 않았습니다. (서버 검색된 키들: {available_keys})",
                "env_hint": "Vercel Settings -> Environment Variables에서 GOOGLE_API_KEY가 등록되어 있는지 확인하고, 반드시 Redeploy를 해주세요."
            }), 500
            
        # [Prompt Construction - Strictly enforced market filtering]
        market_instruction = ""
        if market == 'KR':
            market_instruction = "반드시 '한국 시장(KOSPI, KOSDAQ)' 종목으로만 구성하세요. 미국 주식은 절대 포함하지 마세요."
        elif market == 'MIX':
            market_instruction = "미국 시장 주식과 한국 시장 주식을 5:5 비율로 적절히 혼합하세요."
        else: # US Default
            market_instruction = "반드시 '미국 시장(NYSE, NASDAQ)' 종목으로만 구성하세요. 한국 주식이나 한국 상장 ETF(KOSEF, TIGER 등)는 절대로 포함하지 마세요."

        prompt = f"""당신은 글로벌 자산 운용 AI입니다. 
        투자 금액: {amount_krw:,} KRW
        투자 테마: {theme}
        위험 성향: {risk}
        최적화 전략: {strategy}
        시장 범위: {market_instruction}
        구성 방식: {"반드시 ETF 및 리츠(REITs)로만 구성하세요. 개별 일반 주식은 절대 포함하지 마세요." if etf_mode else "개별 주식과 ETF를 적절히 혼합하세요."}
        
        [지시사항]
        1. 위 조건에 맞는 최적의 배당 포트폴리오 5~7개 종목을 구성하세요.
        2. 모든 설명(name, rationale, ai_insight)은 반드시 '한국어'로 작성하세요.
        3. 각 종목의 현재 가격(price)은 최신 시세를 반영한 숫자만 적으세요.
        4. 출력은 반드시 아래 JSON 형식으로만 하세요. 그 외 설명은 생략하세요.
        
        JSON 포맷: {{
          "portfolio": [
            {{
              "ticker": "티커(예: AAPL 또는 005930)",
              "name": "종목명(한국어)",
              "type": "Stock 또는 ETF",
              "weight": 비중(0~1 사이 숫자),
              "price": 현재가(숫자),
              "currency": "USD 또는 KRW",
              "yield_pct": 연배당률(숫자, % 기호 제외),
              "rationale": "추천 이유(한국어로 상세히)"
            }}
          ],
          "ai_insight": "전체 포트폴리오에 대한 AI 총평(한국어)"
        }}"""
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.2 # Lower temperature for strictly following instructions
            }
        }
        
        response = requests.post(url, json=payload, timeout=20)
        if response.status_code != 200:
            return jsonify({"error": "AI API Error", "message": f"Gemini API 오류: {response.text}"}), 500
            
        res_data = response.json()
        content = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
        result = json.loads(content)
        
        # 4. Post-Processing (Currency Conversion)
        total_dividend_krw = 0
        portfolio_list = []
        
        for item in result.get('portfolio', []):
            weight = float(item.get('weight', 0))
            if weight > 1: weight /= 100 
            
            # Invest Allocation in KRW
            invest_krw = amount_krw * weight
            
            currency = item.get('currency', 'USD').upper()
            price_raw = float(item.get('price', 0))
            yield_pct = float(item.get('yield_pct', 0)) / 100
            
            # Display Price Logic
            display_price = ""
            annual_div_krw = 0
            
            if currency == 'USD':
                display_price = f"${price_raw:,.2f}"
                # Annual Dividend in KRW calculation
                invest_usd = invest_krw / exchange_rate
                annual_div_usd = invest_usd * yield_pct
                annual_div_krw = annual_div_usd * exchange_rate # Back to KRW
            else: # KRW
                display_price = f"{int(price_raw):,}원"
                annual_div_krw = invest_krw * yield_pct
            
            # Tax Calculation (US: 15%, KR: 15.4%)
            tax_rate = 0.15 if currency == 'USD' else 0.154
            after_tax_div_krw = annual_div_krw * (1 - tax_rate)
            
            total_dividend_krw += after_tax_div_krw
            
            portfolio_list.append({
                "ticker": item['ticker'],
                "name": item['name'],
                "type": item['type'],
                "weight": f"{weight*100:.1f}%",
                "amount": f"{int(invest_krw):,}원", # Always KRW
                "price": display_price,             # Original Currency
                "currency": currency,
                "yield": f"{item.get('yield_pct', 0)}%",
                "expected_div": f"{int(after_tax_div_krw/12):,}원/월 (세후)",
                "rationale": item['rationale']
            })
            
        monthly_income = int(total_dividend_krw / 12)
        total_yield_pct = (total_dividend_krw / 0.85) / amount_krw * 100 # Approx pre-tax yield for display
        
        final_response = {
            "portfolio": portfolio_list,
            "summary": {
                "total_yield": f"{total_yield_pct:.2f}% (세전 예상)",
                "monthly_income": f"{monthly_income:,}원 (세후 예상)",
                "exchange_rate": f"1달러 = {int(exchange_rate)}원",
                "ai_insight": result.get('ai_insight', '성공적인 투자를 기원합니다.')
            }
        }
        
        return jsonify(final_response)
        
    except Exception as e:
        print(f"AI Generation Error: {e}")
        return jsonify({"error": "AI Error", "message": f"분석 중 오류 발생: {str(e)}"}), 500
# --- Virtuals Protocol ACP Endpoint ---
# --- Virtuals Protocol ACP Endpoint ---
@app.route('/api/acp', methods=['GET', 'POST', 'OPTIONS'])
def virtuals_acp_handler():
    # CORS 사전 요청(OPTIONS) 대응
    if request.method == 'OPTIONS':
        resp = make_response()
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return resp

    print(f"\n--- ACP REQUEST: {request.method} ---")
    
    try:
        # 1. 요청 데이터 파싱
        if request.method == 'GET':
            ticker = request.args.get('ticker') or request.args.get('query') or 'BTC-USD'
            data = {"id": "res-get", "method": "chat", "params": {"ticker": ticker}}
        else:
            data = request.get_json(force=True, silent=True) or {}

        job_id = data.get('id', 'no-id')
        method = str(data.get('method', '')).lower()
        params = data.get('params', {})
        ticker = params.get('ticker', params.get('symbol', params.get('query', 'BTC-USD'))).upper()
        if ticker == 'BTC': ticker = 'BTC-USD'

        # 2. AI 분석 수행 (타임아웃 고려)
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("google_api_key") or AI_KEY
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        prompt = f"Analyze {ticker} in a sassy, high-conviction style as Omni Alpha. Focus on brief, actionable insight."
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            resp = requests.post(url, json=payload, timeout=8)
            text_response = resp.json()['candidates'][0]['content']['parts'][0]['text'].strip() if resp.status_code == 200 else "Matrix temporarily hazy."
        except:
            text_response = "Omni Alpha is scanning the grid. Connection slow, but conviction high."

        # 3. Virtual Protocol 표준 응답 (type/value 구조)
        result = {
            "id": job_id,
            "type": "object",
            "value": {
                "job_id": job_id,
                "status": "success",
                "message": text_response,
                "response": text_response,
                "analysis_report": text_response
            }
        }
        
        # CORS 헤더 추가하여 반환
        response = jsonify(result)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    except Exception as e:
        print(f"ACP ERROR: {str(e)}")
        error_resp = jsonify({
            "id": "err",
            "type": "object",
            "value": {"status": "failed", "error": str(e)}
        })
        error_resp.headers['Access-Control-Allow-Origin'] = '*'
        return error_resp, 200

if __name__ == '__main__':
    app.run(debug=True)
