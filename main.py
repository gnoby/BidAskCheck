import configparser
from datetime import datetime
import http.server
import http.server
import os
import threading
import time
from http import HTTPStatus
from urllib.parse import parse_qs

import requests

from BidAskObj import Quote
from BidAskObj import setuplog
from BidAskObj import formatmarket
from BidAskObj import formatnumber

global config
global logger

# z.B. Bid/Ask: Bid/Ask:
# 157.15 157.45
# Bid niederiger, Ask höher
# Bid ist der Kurs zu dem man Verkaufen kann
# Ask ist der Kurs zu dem man Kaufen kann

def main():
    global config
    global logger

    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')

    logger = setuplog(config)

    setupserver()
    # url = "https://api.onvista.de/api/v1/stocks/ISIN:US88160R1014/snapshot"
    # url = "https://api.onvista.de/api/v1/funds/ISIN:IE00B9M6RS56/snapshot"
    # url = "https://api.onvista.de/api/v1/instruments/BOND/ISIN:DE0001030575/snapshot"

    # Test
    # file = open('example.json')
    # json_obj = json.load(file)
    # checkisin(json_obj)

    while True:
        # stocklist = config.get('bidaskchecker', 'stocklist').split(",")
        # for stock in stocklist:
        #     url = config.get('bidaskchecker', 'base_url') + config.get('bidaskchecker', 'stock_url') + stock + "/snapshot"
        #     response = requests.get(url)
        #     checkisin(response.json())
        #     time.sleep(config.getint('bidaskchecker', "SLEEP_BETWEEN_CALLS"))

        etflist = config.get('bidaskchecker', 'etflist').split(",")
        for etf in etflist:
            if not is_nighttime():
                url = config.get('bidaskchecker', 'base_url') + config.get('bidaskchecker', 'etf_url') + etf + "/snapshot"
                response = requests.get(url)
                checkisin(response.json())
            time.sleep(config.getint('bidaskchecker', "SLEEP_BETWEEN_CALLS"))

        bondlist = config.get('bidaskchecker', 'bondlist').split(",")
        for bond in bondlist:
            if not is_nighttime():
                url = config.get('bidaskchecker', 'base_url') + config.get('bidaskchecker', 'bond_url') + bond + "/snapshot"
                response = requests.get(url)
                checkisin(response.json())
            time.sleep(config.getint('bidaskchecker', "SLEEP_BETWEEN_CALLS"))



def checkifbidsmallerask(quotelist):
    ignoredmarkets = config.get('bidaskchecker', 'ignoredmarkets').split(",")

    smallask = 0
    smallaskmkt = ""
    highbid = 0
    highbidmkt = ""

    for quote in quotelist:
        if quote.market in ignoredmarkets:
            continue
        if hasattr(quote, 'ask'):
            if smallask == 0 or smallask > quote.ask:
                smallask = quote.ask
                smallaskmkt = quote.market
        if hasattr(quote, 'bid'):
            if highbid == 0 or highbid < quote.bid:
                highbid = quote.bid
                highbidmkt = quote.market

    logString = quotelist[0].isin + ": Bid(Verkauf): " + formatmarket(highbidmkt) \
                + ":" + formatnumber(highbid) \
                + "; Ask(Kauf): " + formatmarket(smallaskmkt) + ":" + formatnumber(smallask)

    log(logString)

    if highbid > (smallask * 1.0001):
        log("Alert!!!!:" + logString)
        requests.get(config.get('bidaskchecker', 'TELEGRAM_URL') + "Alert!\n" + logString)


def checkisin(json_obj):
    jsonQuoteList = json_obj['quoteList']['list']

    quoteObjectList = list()
    for jsonQuote in jsonQuoteList:
        quote = Quote()
        quote.market = jsonQuote['market']['name']
        quote.name = json_obj['instrument']['name']
        quote.isin = json_obj['instrument']['isin']
        quote.quality = jsonQuote['codeQualityPriceBidAsk']
        if 'bid' in jsonQuote:
            quote.bid = jsonQuote['bid']
        if 'ask' in jsonQuote:
            quote.ask = jsonQuote['ask']
        if quote.quality == "RLT":
            quoteObjectList.append(quote)

    #stringresult = quoteObjectList[0].name + "-" + quoteObjectList[0].isin + ": "

    #for quoteObject in quoteObjectList:
    #    stringresult += quoteObject.tostring()

     #log(stringresult)

    checkifbidsmallerask(quoteObjectList)


def log(value):
    logger.info(value)


class HttpHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        params = parse_qs(post_data.decode("utf-8"))
        self.send_response(HTTPStatus.OK)
        self.end_headers()

        if "quit" in params:
            log('User Exit')
            os._exit(0)

    def do_GET(self):
        self.send_response(HTTPStatus.OK)
        self.end_headers()
        refreshFile = open("refresh.html", "rb")
        self.wfile.write(refreshFile.read())

        self.wfile.write(b"\n</select><br/>Log:<br/>")

        # Ausgabe Log-File in umgekehrter Reihenfolge
        logfilename = config.get('bidaskchecker', 'LOG_FILE_NAME')

        for line in reversed(open(logfilename, 'rb').readlines()):
            self.wfile.write(line.rstrip())
            self.wfile.write(b'<br/>')


def is_nighttime():
    now = datetime.now()
    current_hour = now.hour

    if current_hour >= 22 or current_hour < 9:
        return True
    else:
        return False

def setupserver():
    httpd = http.server.ThreadingHTTPServer(("", 1555), HttpHandler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()


if __name__ == "__main__":
    main()
