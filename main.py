import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from bs4 import BeautifulSoup
import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'
}
crypto_to_scrape = ['BTC', 'ETH', 'ADA']
real_time_prices = {}


def scrape(url):
    r = requests.get(url, headers=headers)
    data = r.content
    soup = BeautifulSoup(data, 'lxml')
    return soup


def format_price(price):
    return float(''.join(price.split(',')))


def calculate_seven_day_avg(crypto):
    past_seven_day_open = []
    historical_url = f'https://sg.finance.yahoo.com/quote/{crypto}-USD/history?p={crypto}-USD'
    soup = scrape(historical_url)
    rows = soup.findAll('tr', attrs={'class': 'BdT Bdc($seperatorColor) Ta(end) Fz(s) Whs(nw)'})
    for i in range(8):
        date = rows[i].find('td', attrs={'class': 'Py(10px) Ta(start) Pend(10px)'}).text
        open_price = rows[i].find('td', attrs={'class': 'Py(10px) Pstart(10px)'}).text
        open_price = format_price(open_price)
        if i != 0:
            past_seven_day_open.append(open_price)
    return sum(past_seven_day_open) / 7


def find_real_time_price(crypto):
    yahoo_url = f"https://sg.finance.yahoo.com/quote/{crypto}-USD?p={crypto}-USD"
    soup = scrape(yahoo_url)
    price = soup.find('fin-streamer', attrs={'class': 'Fw(b) Fz(36px) Mb(-4px) D(ib)'})
    real_time_prices[crypto] = format_price(price.text)
    print(real_time_prices)


def decide_notification(crypto):

    seven_day_avg = calculate_seven_day_avg(crypto)
    if crypto == 'ADA':
        if real_time_prices[crypto] < seven_day_avg * 0.85:
            send_notification(crypto, real_time_prices[crypto], seven_day_avg)
    else:
        if real_time_prices[crypto] < seven_day_avg * 0.92:
            send_notification(crypto, real_time_prices[crypto], seven_day_avg)


def send_notification(crypto, current_price, seven_day_avg):
    port = 465
    smtp_server = 'smtp.gmail.com'

    drop = (seven_day_avg - current_price) / seven_day_avg
    drop = '{:.2f}'.format(drop * 100)

    seven_day_avg_str = "{:.2f}".format(seven_day_avg)

    message = MIMEMultipart('mixed')
    message['From'] = '' #<YourEmailAddress>
    message['To'] = ''#<YourEmailAddress>
    message['Subject'] = f'New {crypto}/USD Hits'
    body = f'{crypto} has hit {current_price} USD with 7 - day average {seven_day_avg_str} USD with drop of {drop} %.'
    body = MIMEText(body, 'plain')
    message.attach(body)
    message = message.as_string()

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login('', '') #<YourEmailAddress>, <YourAppPassword>
            server.sendmail('', [''], message) #<YourEmailAddress>
        print('-' * 50)
        print("Email Notification -> Message has been sent.")
        print('-' * 50)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    for crypto in crypto_to_scrape:
        find_real_time_price(crypto)
        decide_notification(crypto)
