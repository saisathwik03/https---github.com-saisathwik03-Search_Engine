from flask import Flask, request, render_template
from bs4 import BeautifulSoup
from collections import defaultdict
from urllib.parse import urljoin, urlparse
import requests
import csv

app = Flask(__name__)
crawler = None

class WebCrawler:
    def __init__(self):
        self.index = defaultdict(list)
        self.visited = set()
        self.session_visited = set()
        self.links_found = 0

    def crawl(self, url, base_url=None, depth=0, max_depth=20):
        if url in self.visited or depth >= max_depth or self.links_found >= 10:
            return
        self.visited.add(url)
        self.session_visited.add(url)

        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            self.index[url] = soup.get_text()

            for link in soup.find_all('a'):
                href = link.get('href')
                if href:
                    if urlparse(href).netloc:
                        absolute_url = href
                    else:
                        absolute_url = urljoin(base_url or url, href)
                    if absolute_url.startswith("http"):
                        if absolute_url not in self.session_visited and absolute_url not in self.visited:
                            self.links_found += 1
                            if self.links_found > max_depth:
                                return
                            self.crawl(absolute_url, base_url=base_url or url, depth=depth+1, max_depth=max_depth)
        except Exception as e:
            print(f"Error crawling {url}: {e}")

    def search(self, keyword):
        results = []
        for url, text in self.index.items():
            if keyword.lower() in text.lower():
                results.append(url)
        return results[:10]

    def rank_results(self, results, keyword):
        ranked_results = {}
        for url in results:
            text = self.index[url]
            score = text.lower().count(keyword.lower())
            ranked_results[url] = score
        return dict(sorted(ranked_results.items(), key=lambda x: x[1], reverse=True))

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    global crawler
    keyword = request.args.get('keyword')
    url = request.args.get('url')
    if keyword and url:
        if crawler is None:
            crawler = WebCrawler()
        crawler.crawl(url)
        results = crawler.search(keyword)
        if results:
            ranked_results = crawler.rank_results(results, keyword)
            return render_template('results.html', results=ranked_results)
        else:
            return render_template('results.html', message='Result not found for the given keyword and URL.')
    else:
        return render_template('results.html', error='Both keyword and URL parameters are required.'), 400
@app.route('/csvdata', methods=['GET'])
def csv_data():
    # Load data from CSV
    data = []
    with open('data.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            data.append(row)
    return render_template('csvdata.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
