# US Market AI Analyst

프리미엄 미국 시장 분석 대시보드

## 🚀 Features

- **실시간 시장 데이터**: S&P 500, Nasdaq, Dow Jones 등 주요 지수
- **AI 분석**: Gemini 1.5 Pro 기반 시장 분석
- **스마트머니 추적**: 기관 투자자 자금 흐름 분석
- **섹터 히트맵**: 실시간 섹터별 성과 추적
- **ETF 자금 흐름**: 주요 ETF 유입/유출 모니터링
- **경제 캘린더**: 주요 경제 지표 일정
- **데일리 리포트**: 매일 자동 생성되는 프리미엄 분석 리포트

## 📦 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys
```

## 🔧 Configuration

`.env` 파일에 다음 API 키를 설정하세요:

```
GOOGLE_API_KEY=your_gemini_api_key_here
DATA_DIR=./us_market
```

## 🏃 Running Locally

```bash
# Run all analysis scripts
python us_market/update_all.py

# Generate daily report
python us_market/daily_report_generator.py

# Open index.html in your browser
```

## 🌐 Deploy to Vercel

1. GitHub에 프로젝트 푸시
2. Vercel에서 Import Project
3. Environment Variables 설정:
   - `GOOGLE_API_KEY`: Your Gemini API key
4. Deploy!

## 📁 Project Structure

```
├── index.html              # Main dashboard
├── us_market/
│   ├── update_all.py      # Run all analysis scripts
│   ├── daily_report_generator.py  # Generate daily report
│   ├── macro_analyzer.py  # Macro analysis
│   ├── sector_heatmap.py  # Sector performance
│   └── ...
├── requirements.txt        # Python dependencies
└── vercel.json            # Vercel configuration
```

## 🎨 Tech Stack

- **Frontend**: HTML, TailwindCSS, JavaScript
- **Backend**: Python
- **AI**: Google Gemini 1.5 Pro
- **Data**: yfinance, pandas
- **Deployment**: Vercel

## 📝 License

MIT License
