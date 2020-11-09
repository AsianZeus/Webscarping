from os import environ
import sys
import json
from flask import Flask, request
from urllib.parse import quote_plus
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import re

app = Flask(__name__)

SEARCH_KEY=environ['SEARCH_KEY']


@app.route('/') # this is the home page route
def hello_world(): # this is the home page function that generates the page code
    return "Hello world!"

def parse_query(query):
    site=' geeks for geeks'
    s=query+site
    s=quote_plus(s)
    return s

def get_links(s):
  urlx = f'https://www.google.com/search?q={s}'
  page = requests.get(urlx)
  soup = BeautifulSoup(page.text, "html.parser")
  result = soup.find_all('div', attrs = {'class': 'ZINbbc'})
  results=[]
  for i in result:
    try:
      results.append(re.search('\/url\?q\=(.*)\&sa',str(i.find('a', href = True)['href'])))
    except:
      pass
  links=[i.group(1) for i in results if i != None]
  return links

def get_data(link):
  r = requests.get(link)
  soup = BeautifulSoup(r.text, 'lxml')
  content = soup.find('div',{'class':'entry-content'}).text
  return content

def get_lines(data):
    lines=[]
    for i in data.split('\n\n'):
        if(re.search(r'\s', i)):
            i=i.replace('\n','')
        if(i==''):
            continue
        lines.append(i)
    return lines

def get_titles(lines):
    meta={}
    length=len(lines)
    for i in range(length):
        if(len(lines[i].split(' '))>15):
            continue
        meta[lines[i]]=i
    return meta

def is_heading(line):
    if(len(line.split(' '))<15):
        return True
    else:
        return False

def getContent(argv):
    print(argv)
    s='+'
    argv=s.join(argv)
    print(argv)
    s = parse_query(argv)
    links = get_links(s)
    data = get_data(links[0])
    lines = get_lines(data)
    for i in lines:
        if(not is_heading(i)):
            return i


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