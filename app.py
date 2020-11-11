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


@app.route('/')
def hello_world():
    return "Hello world!"


def parse_query(query, site=''):
    site = f' {site}'
    s = query + site
    s = quote_plus(s.strip())
    return s


def get_links(s):
    urlx = f'https://www.google.com/search?q={s}'
    page = requests.get(urlx)
    soup = BeautifulSoup(page.text, "html.parser")
    result = soup.find_all('div', attrs={'class': 'ZINbbc'})
    results = []
    for i in result:
        try:
            results.append(
                re.search('\/url\?q\=(.*)\&sa',
                          str(i.find('a', href=True)['href'])))
        except:
            pass
    links = [i.group(1) for i in results if i != None]
    return links


def get_video(s):
    urlx = f'https://www.google.com/search?tbm=vid&q={s}'
    page = requests.get(urlx)
    soup = BeautifulSoup(page.text, "html.parser")
    result = soup.find_all('div', attrs={'class': 'ZINbbc'})
    headings, links, thumbnails = [], [], []

    for i in range(1, 7):
        try:
            head = result[i].find('div', attrs={'class': 'kCrYT'})
            heading = head.find('h3', attrs={'class': 'zBAuLc'}).text
            link = re.search('\/url\?q\=(.*)\&sa',
                             str(head.find('a', href=True)['href']))
            link = link.group(1).replace('%3Fv%3D', '?v=')
            vidid = link.split('=')[1]
            thumbnail = f'https://img.youtube.com/vi/{vidid}/hqdefault.jpg'
            headings.append(heading)
            links.append(link)
            thumbnails.append(thumbnail)
        except:
            continue
        # print(f'{heading}\n{link}\n{thumbnail}\n')
    return (headings[0], links[0], thumbnails[0])


def get_scholar(s):
    urlx = f'https://scholar.google.com/scholar?hl=en&scisbd=1&q={s}'
    page = requests.get(urlx)
    soup = BeautifulSoup(page.text, "html.parser")
    result = soup.find_all('div', attrs={'class': 'gs_r gs_or gs_scl'})
    headings, links, descs = [], [], []
    for i in result:
        head = i.find('h3', attrs={'class': 'gs_rt'}).find('a', href=True)
        link = head['href']
        heading = head.text
        desc = ''.join(i.find('div', attrs={'class': 'gs_rs'}).find_all(
            text=True, recursive=False)).replace('\n', '').replace('\xa0…', '').strip()
        headings.append(heading)
        links.append(link)
        descs.append(desc)
        print(f'{heading}\n{link}\n{desc}\n\n')
    return (headings[0], links[0], descs[0])


def get_data(link):
    r = requests.get(link)
    soup = BeautifulSoup(r.text, 'lxml')
    content = soup.find('div', {'class': 'entry-content'}).text
    return content


def get_lines(data):
    lines = []
    for i in data.split('\n\n'):
        if (re.search(r'\s', i)):
            i = i.replace('\n', '')
        if (i == ''):
            continue
        lines.append(i)
    return lines


def get_titles(lines):
    meta = {}
    length = len(lines)
    for i in range(length):
        if (len(lines[i].split(' ')) > 15):
            continue
        meta[lines[i]] = i
    return meta


def is_heading(line):
    if (len(line.split(' ')) < 15):
        return True
    else:
        return False


def getContent(argv):
    s = parse_query(argv, 'geeks for geeks')
    links = get_links(s)
    try:
        data = get_data(links[0])
    except:
        return 'No information found!'
    lines = get_lines(data)
    for i in lines:
        if (not is_heading(i)):
            return i.strip()
    return 'No information found!'


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    query_result = req.get('queryResult')
    intent_name = query_result.get('intent').get('displayName')
    if (intent_name == 'Techquery'):
        action = query_result.get('parameters').get('action')
        techn = query_result.get('parameters').get('technology')
        processed_query = action + techn
        s = '+'
        processed_query = s.join(processed_query)
        title, link, description, thumbnail = '', '', '', ''
        query_response = getContent(processed_query)
        s_vid = parse_query(processed_query, 'YouTube')
        title, link, thumbnail = get_video(s_vid)
        # try:
        #     s_sch = parse_query(processed_query)
        #     print('It is selcetd', s_sch)
        #     title, link, description = get_scholar(s_sch)
        #     return {
        #         "fulfillmentMessages": [{
        #             "platform": "ACTIONS_ON_GOOGLE",
        #             "simpleResponses": {
        #                 "simpleResponses": [{
        #                     "textToSpeech": query_response
        #                 }]
        #             }
        #         },
        #             {
        #             "platform": "ACTIONS_ON_GOOGLE",
        #             "basicCard": {
        #                 "title":
        #                 title,
        #                 "image": {
        #                     "imageUri": thumbnail,
        #                     "accessibilityText":
        #                     techn[0]
        #                 },
        #                 "buttons": [{
        #                     "title":
        #                     "Watch video",
        #                     "openUriAction": {
        #                         "uri": link
        #                     }
        #                 }]
        #             }
        #         },
        #             {
        #             "platform": "ACTIONS_ON_GOOGLE",
        #             "suggestions": {
        #                 "suggestions": [{
        #                     "title":
        #                     f"Reseach about {techn[0]}"
        #                 }]
        #             }
        #         }, {
        #             "text": {
        #                 "text": [query_response]
        #             }
        #         }]
        #     }
        # except:
        return {
            "fulfillmentMessages": [{
                "platform": "ACTIONS_ON_GOOGLE",
                "simpleResponses": {
                    "simpleResponses": [{
                        "textToSpeech": query_response
                    }]
                }
            },
                {
                "platform": "ACTIONS_ON_GOOGLE",
                "basicCard": {
                    "title":
                    title,
                    "image": {
                        "imageUri": thumbnail,
                        "accessibilityText":
                        techn[0]
                    },
                    "buttons": [{
                        "title":
                        "Watch video",
                        "openUriAction": {
                            "uri": link
                        }
                    }]
                }
            }, {
                "text": {
                    "text": [query_response]
                }
            }]
        }
    if (intent_name == 'Techquery-Research'):
        query_text = req.get('queryResult').get('parameters').get('any')
        title, link, descrgetiption = '', '', ''
        try:
            s_sch = parse_query(query_text)
            title, link, description = get_scholar(s_sch)
            return {
                "fulfillmentMessages": [{
                    "platform": "ACTIONS_ON_GOOGLE",
                    "basicCard": {
                        "title":
                        title,
                        "formattedText":
                        description,
                        "image": {},
                        "buttons": [{
                            "title": "View Research",
                            "openUriAction": {
                                "uri": link
                            }
                        }]
                    }
                }, {
                    "text": {
                        "text": []
                    }
                }]
            }
        except:
            return {
                "fulfillmentText": "No Reseach paper Available.",
                "displayText": '25',
                "source": "webhookdata"
            }


if __name__ == '__main__':
    app.run(debug=True)
