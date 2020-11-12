from os import environ
import sys

from flask import Flask, request
import json

from urllib.parse import quote_plus
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import re

from nltk.tokenize import sent_tokenize,word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import nltk


nltk.download('wordnet')
nltk.download('punkt')
nltk.download('stopwords')

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
            links.append(link+'?nt=t')
            thumbnails.append(thumbnail)
        except:
            continue
        # print(f'{heading}\n{link}\n{thumbnail}\n')
    cnt=0
    for i in links:
      if('watch' in i):
        break
      else:
        cnt+=1
    print('count',cnt)
    return (headings[cnt], links[cnt], thumbnails[cnt])


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
    content = soup.find('div', {'class': 'entry-content'})
    content = content.find_all_next(['p','ol'])
    context=''
    for i in content:
      context+=i.get_text().strip()+'\n'
    return context


def clean(sentences):
    lemmatizer = WordNetLemmatizer()
    cleaned_sentences = []
    for sentence in sentences:
        sentence = sentence.lower()
        sentence = re.sub(r'[^a-zA-Z]',' ',sentence)
        sentence = sentence.split()
        sentence = [lemmatizer.lemmatize(word) for word in sentence if word not in set(stopwords.words('english'))]
        sentence = ' '.join(sentence)
        cleaned_sentences.append(sentence)
    return cleaned_sentences

def init_probability(sentences):
    probability_dict = {}
    words = word_tokenize('. '.join(sentences))
    total_words = len(set(words))
    for word in words:
        if word!='.':
            if not probability_dict.get(word):
                probability_dict[word] = 1
            else:
                probability_dict[word] += 1

    for word,count in probability_dict.items():
        probability_dict[word] = count/total_words 
    return probability_dict

def update_probability(probability_dict,word):
    if probability_dict.get(word):
        probability_dict[word] = probability_dict[word]**2
    return probability_dict

def average_sentence_weights(sentences,probability_dict):
    sentence_weights = {}
    for index,sentence in enumerate(sentences):
        if len(sentence) != 0:
            average_proba = sum([probability_dict[word] for word in sentence if word in probability_dict.keys()])
            average_proba /= len(sentence)
            sentence_weights[index] = average_proba 
    return sentence_weights

def generate_summary(sentence_weights,probability_dict,cleaned_article,tokenized_article,summary_length = 30):
    summary = ""
    current_length = 0
    while current_length < summary_length :
        highest_probability_word = max(probability_dict,key=probability_dict.get)
        sentences_with_max_word= [index for index,sentence in enumerate(cleaned_article) if highest_probability_word in set(word_tokenize(sentence))]
        sentence_list = sorted([[index,sentence_weights[index]] for index in sentences_with_max_word],key=lambda x:x[1],reverse=True)
        summary += tokenized_article[sentence_list[0][0]] + "\n"
        for word in word_tokenize(cleaned_article[sentence_list[0][0]]):
            try:
                probability_dict = update_probability(probability_dict,word)
            except:
                break
        current_length+=1
    return summary

def filter_data(summary):
    summary=summary.replace('\n\n','')
    info=''
    for i in summary.split('\n'):
        if(len(i)>60 and 'geek' not in i.lower() and 'tutorial' not in i.lower() and 'article' not in i.lower() and 'student' not in i.lower() and 'https' not in i.lower() and i.count(',') < 10):
            info += i.strip()+'\n'
    return info



def getContent(argv):
    s = parse_query(argv, 'geeks for geeks')
    links = get_links(s)
    try:
        article = get_data(links[0])
    except:
        return "Here's what we found!"
    required_length = 7
    tokenized_article = sent_tokenize(article)
    cleaned_article = clean(tokenized_article)
    probability_dict = init_probability(cleaned_article)
    sentence_weights = average_sentence_weights(cleaned_article,probability_dict)
    summary = generate_summary(sentence_weights,probability_dict,cleaned_article,tokenized_article,required_length)
    summary = filter_data(summary)
    return summary



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
        title, link, description = '', '', ''
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
