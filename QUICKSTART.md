# 🚀 Quick Start Guide - US Market Analysis System

## 빠른 시작 (3단계)

### 1️⃣ 의존성 설치
```bash
pip install -r requirements.txt
```

### 2️⃣ 데이터 수집 및 분석 실행
```bash
python us_market/update_all.py
```
> ⏱️ 첫 실행 시 10-15분 소요 (S&P 500 전체 데이터 다운로드)

### 3️⃣ 웹 대시보드 시작
```bash
python flask_app.py
```
> 🌐 브라우저에서 http://localhost:5000 접속

---

## 📊 주요 기능

### Smart Money Screener
- 기관 투자자 + 거래량 분석 결합
- 0-100점 복합 점수 시스템
- S급(80+), A급(70+), B급(60+), C급(60 미만)

### AI 매크로 분석
- Gemini/GPT 기반 시장 심리 분석
- Fear/Neutral/Greed 지표
- 한국어 핵심 요약 제공

### 실시간 데이터
- SPY, QQQ, NVDA 실시간 가격
- 10초마다 자동 업데이트
- 섹터별 성과 히트맵

---

## 🔧 선택사항: AI API 설정

더 정확한 AI 분석을 원하면:

```bash
# .env 파일 생성
cp .env.example .env

# API 키 추가 (선택)
GOOGLE_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
```

> 💡 API 키 없이도 작동합니다 (모의 데이터 사용)

---

## 📁 생성되는 파일

`us_market/` 폴더에 다음 파일들이 생성됩니다:

- `us_daily_prices.csv` - S&P 500 가격 데이터
- `smart_money_picks_v2.csv` - 스마트 머니 추천 종목
- `us_macro_analysis.json` - AI 매크로 분석
- `sector_heatmap.json` - 섹터 성과 데이터

---

## ⚠️ 문제 해결

### "Price file not found" 오류
```bash
python us_market/create_us_daily_prices.py
```

### 의존성 설치 실패
```bash
# ta-lib 제외하고 설치 (선택 사항)
pip install pandas numpy yfinance flask python-dotenv requests tqdm google-generativeai openai
```

---

## 📞 추가 도움말

자세한 내용은 [README.md](README.md) 참조

---

**시스템 상태**: ✅ 완료 및 사용 준비 완료
