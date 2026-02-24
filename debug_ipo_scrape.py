
import requests
from bs4 import BeautifulSoup

def test_scrape():
    url = "https://finance.naver.com/news/news_list.naver?mode=LSS3D&section_id=101&section_id2=258&section_id3=406"
    print(f"Testing URL: {url}")
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        print(f"Status Code: {resp.status_code}")
        if resp.status_code != 200:
            return
        
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        # Log all titles found to see what matches
        items = soup.select('dd.articleSubject a, .articleTitle a, td.title a')
        with open('debug_ipo_output.txt', 'w', encoding='utf-8') as f:
            f.write(f"Items found: {len(items)}\n")
            for i, item in enumerate(items[:20]):
                title = item.get_text().strip()
                f.write(f"[{i}] {title}\n")
        print("Output saved to debug_ipo_output.txt")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_scrape()
