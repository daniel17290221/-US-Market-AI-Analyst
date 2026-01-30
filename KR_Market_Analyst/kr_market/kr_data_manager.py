
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime
import os
import json
import traceback

class KRDataManager:
    def __init__(self, output_dir='KR_Market_Analyst/kr_market'):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def get_real_market_movers(self, market_type='ALL'):
        """
        Fetch real-time market movers (Gainers, Volume) using FinanceDataReader.
        market_type: 'KOSPI', 'KOSDAQ', or 'ALL'
        """
        try:
            print(f"Fetching market data for {market_type}...")
            # For comprehensive rankings, we fetch the full listing
            # fdr.StockListing('KRX') returns KOSPI, KOSDAQ, KONEX
            df = fdr.StockListing('KRX')
            
            # Filter by market if needed
            if market_type == 'KOSPI':
                df = df[df['Market'] == 'KOSPI']
            elif market_type == 'KOSDAQ':
                df = df[df['Market'].isin(['KOSDAQ', 'KOSDAQ GLOBAL'])]

            # Ensure numeric columns
            df['ChagesRatio'] = pd.to_numeric(df['ChagesRatio'], errors='coerce')
            df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
            df['Marcap'] = pd.to_numeric(df['Marcap'], errors='coerce')
            
            # Remove minor stocks (penny stocks or low volume) to ensure quality data
            df = df[df['Volume'] > 0]
            
            return df
        except Exception as e:
            print(f"Error fetching real market movers: {e}")
            traceback.print_exc()
            return pd.DataFrame()

    def get_top_lists(self):
        """Generate formatted Top 10 lists for Gainers, Volume, and Leaders"""
        df = self.get_real_market_movers('ALL')
        
        if df.empty:
            return {
                'gainers': [],
                'volume': [],
                'market_cap': []
            }

        # 1. Top Gainers (High rank, decent volume to avoid noise)
        # Filter for volume > 100,000 to avoid liquidity traps
        gainers_df = df[df['Volume'] > 100000].sort_values(by='ChagesRatio', ascending=False).head(10)
        
        # 2. Top Volume
        volume_df = df.sort_values(by='Volume', ascending=False).head(10)
        
        # 3. Market Cap Leaders
        cap_df = df.sort_values(by='Marcap', ascending=False).head(10)

        def format_stocks(stock_df):
            result = []
            for _, row in stock_df.iterrows():
                try:
                    result.append({
                        'symbol': str(row['Code']),
                        'name': row['Name'],
                        'price': f"{int(row['Close']):,}",
                        'change': f"{row['ChagesRatio']:+.2f}",
                        'volume': f"{int(row['Volume']):,}",
                        'market': row['Market']
                    })
                except Exception as e:
                    continue
            return result

        return {
            'gainers': format_stocks(gainers_df),
            'volume': format_stocks(volume_df),
            'market_cap': format_stocks(cap_df)
        }

    def collect_all(self):
        """Main execution method to gather all data and save to JSON"""
        print("Starting KR Market Data Collection...")
        
        # 1. Get Top Lists
        top_lists = self.get_top_lists()
        
        # 2. Structure Data
        # We reuse 'top_stocks' key for the main dashboard list (using Market Cap leaders by default for the main table)
        # But we add specific keys for the tabs
        data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'leaders': top_lists['market_cap'], # Explicit leaders list
            'gainers': top_lists['gainers'],
            'volume': top_lists['volume'],
            'ai_analysis': {} # Placeholder for AI results
        }
        
        # 3. Perform AI Analysis (Pre-calculation)
        try:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv('GOOGLE_API_KEY')
            
            if api_key:
                print("Starting AI Analysis for Top Lists...")
                # Robust Client Initialization matching Daily Report
                client = None
                model_legacy = None
                
                try:
                    from google import genai
                    client = genai.Client(api_key=api_key)
                    print("Using Google GenAI Client (New SDK)")
                except ImportError:
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    model_legacy = genai.GenerativeModel('gemini-2.0-flash')
                    print("Using Google GenerativeAI (Legacy SDK)")

                # Gather all unique symbols
                all_symbols = []
                seen = set()
                for cat in ['gainers', 'volume', 'leaders']:
                    # Analyze top 5 to ensure coverage
                    for stock in data[cat][:5]: 
                        if stock['symbol'] not in seen:
                            all_symbols.append(stock)
                            seen.add(stock['symbol'])
                
                print(f"Analyzing {len(all_symbols)} stocks...")
                
                prompt = f"""
                당신은 글로벌 증시 전문 AI 분석가입니다. 아래 한국 주식 리스트에 대해 실시간 SWOT 분석과 투자 인사이트를 제공해주세요.
                
                [지시사항]
                1. 제공된 **모든 종목**에 대해 JSON 키(종목코드)로 결과를 반환하세요.
                2. 답변은 **핵심만 간결하게** 작성하세요.
                3. 정보가 부족하면 섹터 정보로 추론하세요.
                4. 포맷: insight, risk, swot_s, swot_w, swot_o, swot_t, dcf_target(숫자), dcf_bear(숫자), dcf_bull(숫자), upside.
                5. JSON 형식만 출력하세요.
                
                [대상]
                {json.dumps([{ 'symbol': s['symbol'], 'name': s.get('name', 'N/A') } for s in all_symbols], ensure_ascii=False)}
                """
                
                ai_text = ""
                if client:
                    response = client.models.generate_content(
                        model='gemini-2.0-flash', 
                        contents=prompt
                    )
                    ai_text = response.text
                elif model_legacy:
                    response = model_legacy.generate_content(prompt)
                    ai_text = response.text
                
                cleaned_text = ai_text.replace('```json', '').replace('```', '').strip()
                data['ai_analysis'] = json.loads(cleaned_text)
                print(f"AI Analysis Completed. Parsed {len(data['ai_analysis'])} items.")
                
        except Exception as e:
            print(f"AI Analysis Failed during update: {e}")
            # traceback.print_exc()
            
        # 4. Save to JSON
        output_path = os.path.join(self.output_dir, 'kr_daily_data.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"KR Market data saved to {output_path}")
        return data

if __name__ == "__main__":
    manager = KRDataManager()
    manager.collect_all()
