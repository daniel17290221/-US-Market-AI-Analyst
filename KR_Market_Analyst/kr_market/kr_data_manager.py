
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime
import os
import json
import traceback

class KRDataManager:
    def __init__(self, output_dir=None):
        if output_dir is None:
            # Default to the directory where the script is located
            self.output_dir = os.path.dirname(os.path.abspath(__file__))
        else:
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
        """Generate formatted Top 10 lists for Gainers, Volume, and Leaders (KOSPI/KOSDAQ separate)"""
        df = self.get_real_market_movers('ALL')
        
        if df.empty:
            return {
                'gainers': [], 'volume': [], 'leaders_kospi': [], 'leaders_kosdaq': []
            }

        # Helper to format
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
                except Exception:
                    continue
            return result

        # 1. Leaders: Top 10 KOSPI & Top 10 KOSDAQ Market Cap
        kospi_df = df[df['Market'] == 'KOSPI'].sort_values(by='Marcap', ascending=False).head(10)
        kosdaq_df = df[df['Market'].isin(['KOSDAQ', 'KOSDAQ GLOBAL'])].sort_values(by='Marcap', ascending=False).head(10)

        # 2. Gainers: Top 10 overall (Volume > 50k to filter noise)
        gainers_df = df[df['Volume'] > 50000].sort_values(by='ChagesRatio', ascending=False).head(10)
        
        # 3. Volume: Top 10 overall
        volume_df = df.sort_values(by='Volume', ascending=False).head(10)
        
        return {
            'leaders_kospi': format_stocks(kospi_df),
            'leaders_kosdaq': format_stocks(kosdaq_df),
            'gainers': format_stocks(gainers_df),
            'volume': format_stocks(volume_df)
        }

    def get_indices(self):
        """Fetch major KR market indices with improved reliability"""
        try:
            print("Fetching KR indices...")
            indices = {
                'KOSPI': {'symbol': 'KS11', 'name': '코스피'},
                'KOSDAQ': {'symbol': 'KQ11', 'name': '코스닥'},
                'KOSPI200': {'symbol': 'KS200', 'name': '코스피 200'}
            }
            
            results = {}
            for k, v in indices.items():
                try:
                    # Fetch last 5 days to ensure we have enough points for price & previous close
                    df = fdr.DataReader(v['symbol']).tail(5)
                    if not df.empty and len(df) >= 2:
                        price = df['Close'].iloc[-1]
                        prev_price = df['Close'].iloc[-2]
                        change_val = price - prev_price
                        change_rate = (change_val / prev_price) * 100
                        
                        results[k] = {
                            'symbol': v['symbol'],
                            'name': v['name'],
                            'price': f"{price:,.2f}",
                            'change': f"{change_rate:+.2f}%"
                        }
                    else:
                        results[k] = {'symbol': v['symbol'], 'name': v['name'], 'price': 'N/A', 'change': '0%'}
                except Exception as e:
                    print(f"Error fetching index {k}: {e}")
                    results[k] = {'symbol': v['symbol'], 'name': v['name'], 'price': 'N/A', 'change': '0%'}
            
            return results
        except Exception as e:
            print(f"Error in get_indices: {e}")
            return {}

    def get_sector_performance(self):
        """
        Calculate performance for major sectors based on representative stocks.
        This provides a reliable 'Sector Heatmap' view.
        """
        try:
            print("Calculating sector performance...")
            # Predefined mapping of Sectors to Representative Stock Symbols
            SECTOR_MAP = {
                '반도체': ['005930', '000660', '042700', '000990', '140860'],
                '2차전지': ['373220', '006400', '247540', '066970', '091990'],
                '자동차': ['005380', '000270', '012330', '011210'],
                '바이오': ['207940', '068270', '000100', '302440', '183490'],
                'IT/플랫폼': ['035420', '035720', '035810', '041510'],
                '금융/지주': ['105560', '055550', '086790', '005490', '000370'],
                '철강/금속': ['005490', '004020', '010130', '001230'],
                '화학/에너지': ['051910', '096770', '010950', '011780'],
                '게임/엔터': ['036570', '259960', '352820', '041510', '035900'],
                '조선/중공업': ['329180', '010140', '009540', '042670']
            }

            # Fetch the latest stock listing to get prices and changes
            df = self.get_real_market_movers('ALL')
            if df.empty: return []

            # Create a lookup for quick access
            df.set_index('Code', inplace=True)
            
            results = []
            for sector, symbols in SECTOR_MAP.items():
                changes = []
                stocks_info = []
                
                # Filter symbols that exist in the current listing
                valid_symbols = [s for s in symbols if s in df.index]
                
                for s in valid_symbols:
                    row = df.loc[s]
                    change = float(row['ChagesRatio'])
                    changes.append(change)
                    stocks_info.append({
                        'symbol': s,
                        'name': row['Name'],
                        'change': f"{change:+.2f}%"
                    })
                
                if changes:
                    avg_change = sum(changes) / len(changes)
                    results.append({
                        'sector': sector,
                        'change': avg_change,
                        'change_str': f"{avg_change:+.2f}%",
                        'stocks': stocks_info[:3] # Top 3 representative stocks
                    })
            
            # Sort by change descending
            results.sort(key=lambda x: x['change'], reverse=True)
            return results
        except Exception as e:
            print(f"Error calculating sector performance: {e}")
            traceback.print_exc()
            return []

    def get_commodities(self):
        """Fetch general commodities and FX relevant to KR market"""
        try:
            print("Fetching commodities & FX...")
            items = [
                {'symbol': 'USD/KRW', 'name': '원/달러 환율'},
                {'symbol': 'CL=F', 'name': 'WTI 원유'},
                {'symbol': 'GC=F', 'name': '국제 금'}
            ]
            
            result = []
            for item in items:
                try:
                    # Fetch last 5 days
                    df = fdr.DataReader(item['symbol']).tail(5)
                    if not df.empty and len(df) >= 2:
                        price = df['Close'].iloc[-1]
                        prev_price = df['Close'].iloc[-2]
                        change_val = price - prev_price
                        change_rate = (change_val / prev_price) * 100
                        
                        result.append({
                            'name': item['name'],
                            'price': f"{price:,.2f}",
                            'change': f"{change_rate:+.2f}%"
                        })
                    else:
                        result.append({'name': item['name'], 'price': 'N/A', 'change': '0%'})
                except Exception as e:
                    print(f"Error fetching commodity {item['name']}: {e}")
                    result.append({'name': item['name'], 'price': 'N/A', 'change': '0%'})
            
            return result
        except Exception as e:
            print(f"Error in get_commodities: {e}")
            return []

    def get_ipo_and_schedules(self):
        """Fetch IPO and corporate action schedules from Naver Finance"""
        try:
            print("Fetching IPO & Schedule news...")
            import requests
            try:
                from bs4 import BeautifulSoup
            except ImportError:
                print("❌ Error: beautifulsoup4 is not installed.")
                return []
            
            # Use Naver Finance IPO news sections
            url = "https://finance.naver.com/news/news_list.naver?mode=LSS3D&section_id=101&section_id2=258&section_id3=406" # 공시/IPO 뉴스
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            if resp.status_code != 200: return []
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            news_list = []
            
            # Parse news titles
            items = soup.select('.articleSubject a, .articleTitle a')
            for item in items[:8]:
                title = item.get_text().strip()
                # Filter for IPO, 유상증자, 무상증자, etc.
                if any(kw in title for kw in ['IPO', '공모', '청약', '유상', '무상', '증자', '상장']):
                    link = "https://finance.naver.com" + item['href']
                    news_list.append({
                        "name": title[:25] + "..." if len(title) > 25 else title,
                        "status": "뉴스",
                        "manager": "네이버금융",
                        "price": "-",
                        "date": datetime.now().strftime("%m.%d"),
                        "full_title": title,
                        "url": link
                    })
            
            # Fallback if no news found
            if not news_list:
                news_list = [
                    {"name": "IPO/증자 정보 업데이트 중", "status": "알림", "manager": "-", "price": "-", "date": "-"}
                ]
            return news_list
        except Exception as e:
            print(f"Error fetching IPO news: {e}")
            return []

    def get_market_news(self):
        """Fetch general market news using Google News RSS (KR)"""
        try:
            print("Fetching general market news...")
            import requests
            import xml.etree.ElementTree as ET
            
            # Google News RSS for Korean Market
            url = "https://news.google.com/rss/search?q=%EA%B5%AD%EB%82%B4+%EC%A6%9D%EC%8B%9C&hl=ko&gl=KR&ceid=KR:ko"
            resp = requests.get(url, timeout=5)
            if resp.status_code != 200: return []
            
            root = ET.fromstring(resp.content)
            news_items = []
            for item in root.findall('.//item')[:10]:
                title = item.find('title').text
                link = item.find('link').text
                pub_date = item.find('pubDate').text
                
                # Format title and source
                source = "Google News"
                if " - " in title:
                    title, source = title.rsplit(" - ", 1)
                
                news_items.append({
                    "title": title,
                    "url": link,
                    "source": source,
                    "date": pub_date
                })
            return news_items
        except Exception as e:
            print(f"Error fetching market news: {e}")
            return []

    def get_investor_flows(self):
        """Fetch net buying/selling of foreigners and institutions for KOSPI and KOSDAQ"""
        try:
            print("Fetching investor flows (Supply/Demand)...")
            import requests
            from bs4 import BeautifulSoup
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            results = {}

            # Targets: KOSPI, KOSDAQ
            targets = [('KOSPI', '0'), ('KOSDAQ', '1')]
            
            for name, sosok in targets:
                url = f"https://finance.naver.com/sise/sise_index.naver?code={name}"
                resp = requests.get(url, headers=headers, timeout=5)
                if resp.status_code != 200: continue
                
                # Naver Finance index pages are EUC-KR
                soup = BeautifulSoup(resp.content, 'html.parser', from_encoding='euc-kr')
                
                flows = []
                # Naver Finance index page uses .lst_kos_info for investor summary
                # It contains DT/DD pairs: <dt>개인</dt><dd>+100억</dd>
                invest_dl = soup.select_one('.lst_kos_info')
                if not invest_dl:
                    invest_dl = soup.select_one('.lst_invest') # Fallback 1
                
                if invest_dl:
                    # In some layouts, DT/DD are pairs; in others, everything is inside DD
                    # Let's try to be as flexible as possible
                    items = invest_dl.find_all(['dd', 'li', 'div'], recursive=False)
                    if not items: items = invest_dl.find_all(['dd', 'dt']) # fallback to all
                    
                    for item in items:
                        text = item.get_text().strip()
                        
                        label = None
                        if '개인' in text: label = '개인'
                        elif '외국인' in text or '외인' in text: label = '외국인'
                        elif '기관' in text: label = '기관'
                        
                        if not label: continue
                        
                        # Value extraction: prioritized Strong > Span > Text subtraction
                        val_tag = item.find(['strong', 'span'])
                        if val_tag and val_tag.get_text().strip() != label:
                            val_raw = val_tag.get_text().strip()
                        else:
                            val_raw = text.replace(label, '').strip()
                        
                        # Clean value (handle cases like "+1,234억" or "-50")
                        clean_val = val_raw.replace('억', '').replace(',', '').strip()
                        try:
                            # Handle sign if it's separate
                            val_int = int(clean_val)
                            status = "매수" if val_int > 0 else ("매도" if val_int < 0 else "보합")
                            formatted_val = f"{val_int:+}억" if val_int != 0 else "0억"
                        except:
                            formatted_val = val_raw
                            status = "매수" if '+' in val_raw else ("매도" if '-' in val_raw else "보합")
                            
                        flows.append({
                            'label': label,
                            'value': formatted_val,
                            'status': status
                        })
                
                results[name] = flows
            
            return results
        except Exception as e:
            print(f"Error fetching investor flows: {e}")
            return {}

    def collect_all(self):
        """Main execution method to gather all data and save to JSON"""
        print("Starting KR Market Data Collection...")
        
        # 1. Get Top Lists
        top_lists = self.get_top_lists()
        
        # 2. Get Indices & Commodities & Sectors & IPOs & News & Flows
        market_indices = self.get_indices()
        commodities = self.get_commodities()
        sector_heatmap = self.get_sector_performance()
        ipo_news = self.get_ipo_and_schedules()
        market_news = self.get_market_news()
        investor_flows = self.get_investor_flows()
        
        # 3. Structure Data - Make top_stocks more dynamic by mixing leaders, gainers, and volume
        dynamic_stocks = []
        dynamic_stocks.extend(top_lists['gainers'][:3])     # Top 3 Gainers
        dynamic_stocks.extend(top_lists['volume'][:3])      # Top 3 Volume Leaders
        dynamic_stocks.extend(top_lists['leaders_kospi'][:2]) # Top 2 KOSPI Leaders
        dynamic_stocks.extend(top_lists['leaders_kosdaq'][:2]) # Top 2 KOSDAQ Leaders
        
        data = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S KST'),
            'market_indices': market_indices,
            'commodities': commodities,
            'sector_heatmap': sector_heatmap,
            'ipo_news': ipo_news,
            'market_news': market_news,
            'investor_flows': investor_flows,
            'top_stocks': dynamic_stocks, 
            'leaders_kospi': top_lists['leaders_kospi'],
            'leaders_kosdaq': top_lists['leaders_kosdaq'],
            'gainers': top_lists['gainers'],
            'volume': top_lists['volume'],
            'ai_analysis': {} 
        }
        
        # 4. Perform AI Analysis (Pre-calculation) with Batching
        try:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv('GOOGLE_API_KEY')
            
            if api_key:
                print("Starting AI Analysis for Top Lists...")
                # Robust Client Initialization
                client = None
                model_legacy = None
                try:
                    from google import genai
                    client = genai.Client(api_key=api_key)
                except ImportError:
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    model_legacy = genai.GenerativeModel('gemini-pro')

                # Gather all unique symbols
                all_symbols = []
                seen = set()
                # Analyze ALL items in the lists (10+10+10+10 = 40 max)
                for cat in ['leaders_kospi', 'leaders_kosdaq', 'gainers', 'volume']:
                    for stock in data[cat]: 
                        if stock['symbol'] not in seen:
                            all_symbols.append(stock)
                            seen.add(stock['symbol'])
                
                import time
                print(f"Analyzing {len(all_symbols)} stocks in batches...")
                
                # Split into chunks of 15 to be safer with token/JSON limits
                chunk_size = 15
                for i in range(0, len(all_symbols), chunk_size):
                    batch = all_symbols[i:i + chunk_size]
                    print(f"Processing batch {i//chunk_size + 1}: {len(batch)} stocks...")
                    
                    prompt = f"""
                    당신은 글로벌 증시 전문 AI 분석가입니다. 아래 한국 주식 리스트에 대해 실시간 SWOT 분석과 투자 인사이트를 제공해주세요.
                    
                    [반드시 준수할 JSON 데이터 구조]
                    각 종목 코드(Symbol)를 키로 하는 객체를 반환하세요.
                    {{
                        "symbol_code": {{
                            "insight": "핵심 투자 포인트 (1문장)",
                            "risk": "핵심 리스크 (1문장)",
                            "swot_s": "Strength 강점 키워드",
                            "swot_w": "Weakness 약점 키워드",
                            "swot_o": "Opportunity 기회 키워드",
                            "swot_t": "Threat 위협 키워드",
                            "upside": "+15%",
                            "dcf_target": "적정주가 숫자",
                            "dcf_bear": "하단주가 숫자", 
                            "dcf_bull": "상단주가 숫자"
                        }}
                    }}

                    [지시사항]
                    1. 모든 텍스트는 한국어로 작성하세요.
                    2. 정보가 부족하면 섹터/업종의 일반적인 특징으로 추론하여 공란 없이 채우세요.
                    3. JSON 형식 외의 다른 설명이나 텍스트는 포함하지 마세요.
                    
                    [대상 종목]
                    {json.dumps([{ 'symbol': s['symbol'], 'name': s.get('name', 'N/A') } for s in batch], ensure_ascii=False)}
                    """
                    
                    ai_text = ""
                    try:
                        # Safe retry logic
                        for attempt in range(2):
                            try:
                                if client:
                                    response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
                                    ai_text = response.text
                                elif model_legacy:
                                    model = genai.GenerativeModel('gemini-2.0-flash')
                                    response = model.generate_content(prompt)
                                    ai_text = response.text
                                
                                if ai_text:
                                    break
                            except Exception as api_e:
                                print(f"API Attempt {attempt+1} failed: {api_e}")
                                time.sleep(2)

                        if not ai_text:
                            continue

                        # Clean and Parse
                        cleaned_text = ai_text.replace('```json', '').replace('```', '').strip()
                        # Sometimes Gemini adds text before or after JSON
                        if '{' in cleaned_text and '}' in cleaned_text:
                            start = cleaned_text.find('{')
                            end = cleaned_text.rfind('}') + 1
                            cleaned_text = cleaned_text[start:end]
                        
                        try:
                            batch_results = json.loads(cleaned_text)
                            if isinstance(batch_results, dict):
                                # Clean keys - ensure they are the original symbols
                                for sym, results in batch_results.items():
                                    data['ai_analysis'][sym] = results
                            print(f"Successfully processed {len(batch_results)} stocks in this batch.")
                        except json.JSONDecodeError as jde:
                            print(f"JSON Parse Error in batch {i//chunk_size + 1}: {jde}")
                            # Fallback: maybe it's too many stocks, but we'll try next batch
                    except Exception as batch_e:
                        print(f"Batch {i//chunk_size + 1} fatal error: {batch_e}")
                    
                    # Small throttle between batches
                    time.sleep(1)
                
                print(f"AI Analysis Completed. Total items: {len(data['ai_analysis'])}")
                
        except Exception as e:
            print(f"AI Analysis Init Failed: {e}")
            
        # 5. Save to JSON
        output_path = os.path.join(self.output_dir, 'kr_daily_data.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"KR Market data saved to {output_path}")
        return data

if __name__ == "__main__":
    manager = KRDataManager()
    manager.collect_all()
