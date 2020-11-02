import json
from urllib.request import urlopen
import requests
from bs4 import BeautifulSoup
from os import environ
import sys

SEARCH_KEY=environ['SEARCH_KEY']

def main(argv):
    tech='+'
    tech= tech.join(argv[1:])
    page = urlopen(f'{SEARCH_KEY}{tech}')
    html_bytes = page.read()
    html = html_bytes.decode("utf-8")
    data = json.loads(html)
    r = requests.get(data['items'][0]['link'])
    soup = BeautifulSoup(r.text, 'lxml')
    content = soup.find('div',{'class':'entry-content'}).find('p').text
    return content

if __name__ == "__main__":
    content=main(sys.argv)
    print(content)