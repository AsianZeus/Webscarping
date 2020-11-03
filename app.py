from os import environ
import sys
import json
from urllib.request import urlopen
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
app = Flask(__name__)

SEARCH_KEY=environ['SEARCH_KEY']


@app.route('/') # this is the home page route
def hello_world(): # this is the home page function that generates the page code
    return "Hello world!"

def getContent(argv):
    print(argv)
    s='+'
    argv=s.join(argv)
    print(argv)
    tech = argv.replace(' ','+')
    print(tech)
    page = urlopen(f'{SEARCH_KEY}{tech}')
    html_bytes = page.read()
    html = html_bytes.decode("utf-8")
    data = json.loads(html)
    r = requests.get(data['items'][0]['link'])
    soup = BeautifulSoup(r.text, 'lxml')
    content = soup.find('div',{'class':'entry-content'}).text
    maxlines=5
    cnt=0
    resultx=''
    for i in content.split('\n'):
        if i=='':
            continue
        if(cnt<maxlines):
            resultx=resultx+'\n'+i
            cnt+=1
    return resultx


@app.route('/webhook', methods=['POST'])
def webhook():
  req = request.get_json(silent=True, force=True)
  query_result = req.get('queryResult')
  techn = query_result.get('parameters').get('technology')
  sum = getContent(techn)
  return {
        "fulfillmentText": sum,
        "displayText": '25',
        "source": "webhookdata"
    }
if __name__ == '__main__':
  app.run(debug=True)