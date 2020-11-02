from flask import Flask, render_template, request
import json
from urllib.request import urlopen
import requests
from bs4 import BeautifulSoup
from os import environ
import sys

app = Flask(__name__)

SEARCH_KEY=environ['SEARCH_KEY']

def getContent(argv):
    tech = argv.replace(' ','+')
    page = urlopen(f'{SEARCH_KEY}{tech}')
    html_bytes = page.read()
    html = html_bytes.decode("utf-8")
    data = json.loads(html)
    r = requests.get(data['items'][0]['link'])
    soup = BeautifulSoup(r.text, 'lxml')
    content = soup.find('div',{'class':'entry-content'}).find('p').text
    return content

@app.route('/')
def my_fun():
	try:
		tech = request.args['tech']
		print('----------------------',tech)
		result = getContent(tech)
	except:
		tech=''
		result=''
	return f'<html><body><h1>{tech}</h1><p>{result}</p></body></html>'

if __name__ == "__main__":
    app.run(debug=True)









