import requests
import json
import time
import pytz
import logging
import threading

import telebot
from datetime import datetime
from selenium.webdriver.firefox.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects


url = 'https://api.coingecko.com/api/v3/coins/the-open-network?tickers=false&market_data=true&community_data=false& eveloper_data=false&sparkline=false'
bot = telebot.TeleBot('5130323698:AAFeD1LEQGIoFpHDlTyIOOTu_ZasF1MMU6g')
with open("domains.csv", "r") as file:
    pass

def get_ton_usd():
    try:
        global ton_usd
        response = requests.get(url)
        data = json.loads(response.text)
        ton_usd = data['market_data']['current_price']['usd']
        threading.Timer(7200, get_ton_usd).start()
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        pass
        
def restart_bot_data():
    with open("domains.csv", "r") as file:
        domains_in_file = (file.read())[1:-1].replace("'", '').split(", ")
        if len(domains_in_file) == 0 or len(domains_in_file) == 1:
            pass
        else:
            for num, domen in enumerate(domains_in_file):
                if num % 2 == 0:
                    max_price = domains_in_file[num+1]
                    return_text = 'К сожалению бот упал, мониторинг домена ' + domen + ' восстановлен'
                    bot.send_message(424015934, str(return_text))
                    threading.Timer(1, check_domains, args=(
                        424015934, domen, max_price)).start()


def delete_domain_from_file(message, domain):
    with open("domains.csv", "r") as file:
        domains_in_file = (file.read())[
            1:-1].replace("'", '').split(", ")
        try:
            index_domain = domains_in_file.index(domain)
            domains_in_file.pop(index_domain)
            domains_in_file.pop(index_domain)
        except:
            return_text = "ERROR! Домен " + domain + \
                'отсутствует в локальном списке доменов'
            bot.send_message(message, str(return_text))
        with open("domains.csv", "w") as file:
            file.write(str(domains_in_file))


def check_domains(message, domain, max_price):
    try:
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options=options)
        driver.get('https://fragment.com/username/' + domain)
        
        try:
            status = driver.find_element(By.XPATH, '//*[@id="aj_content"]/main/section[1]/div[1]/h2/span[2]')
        except:
            return_text = 'ERROR! Домена ' + str(domain) + ' не существует'
            delete_domain_from_file(message, domain)
            bot.send_message(message, str(return_text))
            driver.close()
            return
        if status.text == 'Sold':
            return_text = 'Info! Домен ' + str(domain) + ' уже продан'
            delete_domain_from_file(message, domain)
            bot.send_message(message, str(return_text))
            driver.close()
            return
        elif status.text == 'Available':
            return_text = 'Info! Домен ' + str(domain) + ' доступен для старта аукциона'
            delete_domain_from_file(message, domain)
            bot.send_message(message, str(return_text))
            driver.close()
            return
        
        try:
            who_bid_begin = driver.find_element(By.XPATH, '//*[@id="aj_content"]/main/section[2]/div[2]/table/tbody/tr[1]/td[3]/div/a/span[1]')
            who_bid_end = driver.find_element(By.XPATH, '//*[@id="aj_content"]/main/section[2]/div[2]/table/tbody/tr[1]/td[3]/div/a/span[3]')
            if who_bid_begin.text == 'EQBogv1Bwrm7hHwvIvPH7nS4' and who_bid_end.text == '6QgtcsBGUyRudOklTZZkmkiW':
                threading.Timer(3600, check_domains, args=(message, domain, max_price)).start()
                driver.close()
        except:
            pass 
        
        try:
            time_end_bid = driver.find_element(By.XPATH, '//*[@id="aj_content"]/main/section[1]/div[4]/div[1]/time') 
            time_end_bid = time_end_bid.get_attribute("datetime").replace('T', ' ')[:-6]
            time_end_bid = datetime.strptime(time_end_bid, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc)
            time_now = datetime.now(pytz.utc)
            time_to_check_pid = (time_end_bid - time_now)
            time_to_send_message = time_to_check_pid.total_seconds() - 300
        except:
            logging.exception("message")
            driver.close()
            
        minimal_bid = driver.find_element(By.XPATH, '//*[@id="aj_content"]/main/section[1]/div[2]/table/tbody/tr/td[3]/div/div')
        recommended_price = driver.find_element(By.XPATH, '//*[@id="aj_content"]/main/section[1]/div[2]/table/tbody/tr/td[1]/div/div[2]')
        minimal_bid = "".join(c for c in (minimal_bid.text) if c.isdecimal())
        recommended_price = "".join(c for c in (recommended_price.text) if c.isdecimal())
        
        if float(minimal_bid) * float(ton_usd) > float(max_price):
            delete_domain_from_file(message, domain)
            return_text = 'Info! Минимальная ставка по домену ' + str(domain) + ' выше предельной цены, мониторинг этого домена прекращен' + '\n Минимальная ставка сейчас: ' + str(float(minimal_bid) * float(ton_usd)) + ' $ (' + minimal_bid + ' TON)' + '\n Введенная максимальная цена: ' + str(max_price) + ' $'
            bot.send_message(message, str(return_text))
            driver.close()
            return
            
        if time_to_send_message < 1000:
            element = driver.find_element(By.XPATH, '//*[@id="aj_content"]/main/section[1]/div[5]/button').click()
            element = driver.find_element(By.XPATH, '//*[@id="aj_content"]/div[6]/div/div/section/form/div[2]/button/span').click()
            time.sleep(10)
            element = driver.find_element(By.XPATH, '/html/body/div[2]/div[7]/div/div/section/div/div[1]')
            element.screenshot(domain + ".png")

            driver.get('https://zxing.org/w/decode.jspx')
            send_image = driver.find_element(By.ID, "f").send_keys("/home/dewhole/projects/HARDHEAD/ton/" + domain + ".png")
            element = driver.find_element(By.XPATH, '/html/body/div/table[2]/tbody/tr[2]/td[3]/input').click()
            try:
                link_bid = driver.find_element(By.TAG_NAME, 'pre')
            except:
                threading.Timer(10, check_domains, args=(message, domain, max_price)).start()
                return
            link_bid = link_bid.text
            return_text = 'IMPORTANT! Ссылка для ставки на домен ' + str(domain) + ':' + '\n' + str(link_bid) + '\n Предельная цена: ' + str(float(recommended_price) * float(ton_usd)) + ' $' + ' (' + str(recommended_price) + ' TON)' + '\n Введенная максимальная цена:' + str(max_price) + ' $' + '\n Минимальная ставка сейчас: ' + str(float(minimal_bid) * float(ton_usd)) + ' $' + ' (' + minimal_bid + ' TON' 
            bot.send_message(message, str(return_text))
            driver.close()
            threading.Timer(600, check_domains, args=(message, domain, max_price)).start()
            
        else:
            return_text = 'Info! До ставки на домен ' + str(domain) + ' ' + str(time_to_check_pid) 
            bot.send_message(message, str(return_text))
            driver.close()
            threading.Timer(time_to_send_message, check_domains, args=(message, domain, max_price)).start()
            
    except:
        logging.exception("LOG")
        return_text = 'ERROR! Произошла ошибка с доменом ' + str(domain)
        driver.close()
        bot.send_message(message, str(return_text))
        delete_domain_from_file(message, domain)

        
        
        
@bot.message_handler(content_types=['text', 'document', 'audio'])
def get_text_messages(message):
    
    if message.text == '/start':
        return_text = "Команды: \n 'мой id' - выведет ваш телеграм id \n 'курс' - выведет актуальный курс ТОН-USD \n 'статус' - выведет список доменов, которые сейчас мониторятся \n \n Для запуска мониторинга введите любое количество пар 'домен-предельная цена' в любом виде из примера \n \n пример: casio 2000 gorod 3000, @aurora 4000"
        bot.send_message(message.from_user.id, str(return_text))

    elif message.text == 'курс':
        bot.send_message(message.from_user.id, str('Курс ton = ' + str(ton_usd) + '$'))
        
    elif message.text == 'мой id':
        bot.send_message(message.from_user.id, str(message.from_user.id))
        
    elif message.text == 'статус':
        with open("domains.csv", "r") as file:
            domains_in_file = (file.read())[1:-1].replace("'", '').split(", ")
            if len(domains_in_file) == 0 or len(domains_in_file) == 1:
                bot.send_message(message.from_user.id, str('Info! В работе доменов нет'))
            else:
                return_text = ''
                for num, domen in enumerate(domains_in_file):
                    if num % 2 == 0:
                        max_price = domains_in_file[num+1]
                        return_text = return_text + ' ' + domen + ' ' + max_price + '\n'
                bot.send_message(message.from_user.id, str(return_text))

    else:
        domains = message.text.replace(',', '').replace('.', '').replace(';', '').replace('@', '').split()
        if len(domains) % 2 != 0:
            bot.send_message(message.from_user.id, str('ERROR! Проверьте наличие пар домен-цена'))
            return
        bot.send_message(message.from_user.id, str(domains))
        with open("domains.csv", "r") as file:
            domains_in_file = (file.read())[1:-1].replace("'", '').split(", ")
            if domains_in_file == ['']:
                domains_in_file = []
            for num, domen in enumerate(domains):
                if num % 2 == 0:
                    max_price = domains[num+1]
                    if domen in domains_in_file:
                        return_text = 'Info! Домен ' + str(domen) + ' уже мониторится'
                        bot.send_message(message.from_user.id, str(return_text))
                    else:
                        domains_in_file.append(domen)
                        domains_in_file.append(max_price)
                        threading.Timer(1, check_domains, args=(message.from_user.id, domen, max_price)).start()
                else:
                    continue
        with open("domains.csv", "w") as file:
            file.write(str(domains_in_file))
            
            
@bot.message_handler(commands=['start'])
def get_start_messages(message):
    bot.send_message(message.from_user.id, "Введите требуемые домены")


def test(message):
    bot.send_message(message, "asdfasdfasdf")


get_ton_usd()
restart_bot_data()
bot.infinity_polling(timeout=10, long_polling_timeout=5)



