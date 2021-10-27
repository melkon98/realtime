import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realtime.settings')

app = Celery('realtime')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()


from .redis_client import client
import json
import requests
from django.conf import settings
import telegram
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from time import sleep

telegram_settings = settings.TELEGRAM

def sendNotificationsViaTelegram(message_html):
    bot = telegram.Bot(token=telegram_settings['bot_token'])
    bot.send_message(chat_id="%s" % telegram_settings['channel_name'], text=message_html, parse_mode=telegram.ParseMode.HTML)

ua = UserAgent()
payload={}
headers = {
    'Cookie': 'machine_cookie=6575076475768; machine_cookie_ts=1634909180',
    'Accept': '*/*',
}

client.flushall()

@app.task()
def parse_binance():

    url = "https://www.binance.com/bapi/composite/v1/public/cms/article/catalog/list/query?catalogId=49&pageNo=1&pageSize=15"
    headers["User-Agent"] = str(ua.random)

    while True:
        try:
            first = client.get('binanceFirst')
            response = requests.request("GET", url, headers=headers, data=payload)
            resp = response.json()
            new_resp = []
            
            if not first:
                first = json.dumps(resp["data"]["articles"][0])
                client.set('binanceFirst', first)
                for r in resp["data"]["articles"]:
                    new_resp.append(r)
                # async_to_sync(channel_layer.group_send)("listners",{'type': 'chat_message','message': str(new_resp)}) 
                return new_resp
            first = json.loads(first)
            if first["id"] != resp["data"]["articles"][0]["id"]:
                for r in resp["data"]["articles"]:
                    if first["id"] != r["id"]:
                        new_resp.append(r)
                    else:
                        client.set('binanceFirst', json.dumps(resp["data"]["articles"][0]))
                        # async_to_sync(channel_layer.group_send)("listners",{'type': 'chat_message','message': str(new_resp)}) 
                        for rs in new_resp:
                            sendNotificationsViaTelegram(f"<strong>(Binance)</strong> {rs['title']}")
                        return new_resp
        except Exception as e:
            print(e)
            sleep(1)

@app.task()
def parse_okex():
    
    url = "https://www.okex.com/support/hc/api/internal/recent_activities?locale=en-us&page=1&per_page=5&locale=en-us"
    headers["User-Agent"] = str(ua.random)

    while True:
        try:
            first = client.get('okexFirst')
            response = requests.request("GET", url, headers=headers, data=payload)
            resp = response.json()
            new_resp = []
            
            if not first:
                first = json.dumps(resp["activities"][0])
                client.set('okexFirst', first)
                for r in resp["activities"]:
                    new_resp.append(r)
                # async_to_sync(channel_layer.group_send)("listners",{'type': 'chat_message','message': str(new_resp)}) 
                return new_resp
            first = json.loads(first)
            if first["id"] != resp["activities"][0]["id"]:
                for r in resp["activities"]:
                    if first["id"] != r["id"]:
                        new_resp.append(r)
                    else:
                        client.set('okexFirst', json.dumps(resp["activities"][0]))
                        # async_to_sync(channel_layer.group_send)("listners",{'type': 'chat_message','message': str(new_resp)}) 
                        for rs in new_resp:
                            sendNotificationsViaTelegram(f"https://okexsupport.zendesk.com{rs['url']} \n<strong>(Okex)</strong> {rs['title']}")
                        return new_resp
        except Exception as e:
            print(e)
            sleep(1)

@app.task()
def parse_huobi():
    
    url = "https://www.huobi.com/support/public/getList/v2?page=1&limit=20&oneLevelId=360000031902&twoLevelId=360000039481&language=en-us"
    headers["User-Agent"] = str(ua.random)

    while True:
        try:
            first = client.get('huobiFirst')
            response = requests.request("GET", url, headers=headers, data=payload)
            resp = response.json()
            new_resp = []

            if not first:
                first = json.dumps(resp["data"]["list"][0])
                client.set('huobiFirst', first)
                for r in resp["data"]["list"]:
                    new_resp.append(r)
                # async_to_sync(channel_layer.group_send)("listners",{'type': 'chat_message','message': str(new_resp)}) 
                return new_resp
            first = json.loads(first)
            if first["id"] != resp["data"]["list"][0]["id"]:
                for r in resp["data"]["list"]:
                    if first["id"] != r["id"]:
                        new_resp.append(r)
                    else:
                        client.set('huobiFirst', json.dumps(resp["data"]["list"][0]))
                        # async_to_sync(channel_layer.group_send)("listners",{'type': 'chat_message','message': str(new_resp)}) 
                        for rs in new_resp:
                            sendNotificationsViaTelegram(f"<strong>(Huobi)</strong> {rs['title']}")
                        return new_resp
        except Exception as e:
            print(e)
            sleep(1)

@app.task()
def parse_coinbase():
    url = "https://medium.com/@coinbaseblog"
    headers["User-Agent"] = str(ua.random)

    while True:
        try:
            first = client.get('coinbaseFirst')
            response = requests.request("GET", url, headers=headers, data=payload)
            soup = BeautifulSoup(response.text, 'html.parser')
            mainCenter = soup.find(class_='ap aq ar as at fz av v')
            for _, i in enumerate(mainCenter):
                url_ = i.find("h1").find("a")["href"]
                title_ = i.find("h1").find("a").text
                text_ = "\n".join(f.text for f in i.find("section").findChildren("p"))
                # bot.send_message(chat_id="859434333", text=f"{url_.split('?')[0]}\n\n<strong>{title_}</strong>\n\n{text_}", parse_mode=ParseMode.HTML)
            new_resp = []

            first_url = next(mainCenter.children, None)
            first_url = first.find("h1").find("a")["href"]
            if not first:
                client.set('coinbaseFirst', first_url)
            if first != first_url:
                for r in mainCenter:
                    url_ = r.find("h1").find("a")["href"]
                    if first != url_:
                        title_ = r.find("h1").find("a").text
                        text_ = "\n".join(f.text for f in r.find("section").findChildren("p"))
                        new_resp.append(f"{url_.split('?')[0]}\n\n<strong>(Coinbase) {title_}</strong>\n\n{text_}")
                    else:
                        client.set('coinbaseFirst', first_url)
                        for rs in new_resp:
                            sendNotificationsViaTelegram(rs)
                        return new_resp
        except Exception as e:
            print(e)
            sleep(1)

parse_binance.delay()
parse_okex.delay()
parse_huobi.delay()
parse_coinbase.delay()