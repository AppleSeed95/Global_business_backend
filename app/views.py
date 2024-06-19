from bs4 import BeautifulSoup
from django.shortcuts import render
import ntplib
import requests
import re
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

import os
from django.conf import settings
import time





# Create your views here.
from django.http import JsonResponse
import json
import sys


def getNtpTimeUnix(_ntpServer):
    ntp_client = ntplib.NTPClient()
    ntp_server_host = _ntpServer

    try:
        ntpResponse = ntp_client.request(ntp_server_host)
        ntpTimeUnix = ntpResponse.tx_time
        return ntpTimeUnix
    except Exception as e:
        print('[ERROR]NTP時刻取得でエラーになりました。')
        print(e)
        sys.exit(1)

def login_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data['email']
        password = data['password']
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36 Edg/99.0.1150.55'
        header = {
            'User-Agent': user_agent,
            'Cache-Control': 'max-age=0',
        }
        _ntpServer = 'ntp1.jst.mfeed.ad.jp'
        with requests.session() as session:

            requestUrl = 'https://t.livepocket.jp/login?acroot=header-new_p_u_nl'
            res = session.get(requestUrl, headers=header)

            requestUrl = 'https://t.livepocket.jp/api/sessions/create?mytimestamp=' + str(int(getNtpTimeUnix(_ntpServer)*1000))

            data = {
                'login': email,
                'password': password,
                'login_password': email + password,
            }
            print(data)
            res = session.post(requestUrl, data=data, headers=header, cookies=res.cookies)

            jsonData = json.loads(res.text)
            response_data = jsonData

    else:
        response_data = {'msg': 'This endpoint accepts only POST requests.'}
    return JsonResponse(response_data)

def get_ticket(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        url = data['url']
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36 Edg/99.0.1150.55'
        header = {
            'User-Agent': user_agent,
            'Cache-Control': 'max-age=0',
        }
        with requests.session() as session:
            res = session.get(url, headers=header)
            res = session.get(url, headers=header, cookies=res.cookies)
            soup = BeautifulSoup(res.text, 'html.parser')
            eventId = soup.find('input', id='event_id')['value']
            eventName = soup.find('input', id='event_cname')['value']
            eventTicketGroups = soup.find('input', id='event_ticket_groups')['value']
            ticketGroupIdList = []
            ticketIdList = []
            ticketTypeList = []
            ticketLimitMaxList = []
            jsonData = json.loads(eventTicketGroups)
            for jsonDataTicketType in jsonData:
                for ticketInfos in jsonDataTicketType["tickets_info"]:
                    ticketGroupIdList.append(jsonDataTicketType['group_id'])
                    ticketIdList.append(ticketInfos['id'])
                    ticketTypeList.append(ticketInfos['type'])
                    ticketLimitMaxList.append(ticketInfos['limit_max'])
            response_data = {
                "ticket_data":jsonData,
                "eventInfo": {
                    "eventId": eventId,
                    "eventName": eventName
                },
            }

    else:
        response_data = {'msg': 'This endpoint accepts only POST requests.'}
    return JsonResponse(response_data, safe=False)


def calc_time(request):
    if request.method == 'POST':
        _ntpServer = 'ntp1.jst.mfeed.ad.jp'
        data = json.loads(request.body)
        _scheduledTime = data['ticketTime']
        _beforeTime = data['beforeTime']
        scheduledTime = datetime.datetime(
                                    year        = int(_scheduledTime[0:4]),
                                    month       = int(_scheduledTime[5:7]),
                                    day         = int(_scheduledTime[8:10]),
                                    hour        = int(_scheduledTime[11:13]),
                                    minute      = int(_scheduledTime[14:16]),
                                    second      = int(_scheduledTime[17:19]),
                                    tzinfo      = None
                                )
        scheduledTimeUnix = datetime.datetime.timestamp(scheduledTime)
        scheduledTimeBeforeUnix = datetime.datetime.timestamp(scheduledTime - datetime.timedelta(seconds=_beforeTime))
        ntpTimeUnix = getNtpTimeUnix(_ntpServer)

        secondDiff = float(scheduledTimeBeforeUnix) - float(ntpTimeUnix)
        response_data = {'data': secondDiff if secondDiff > 0 else 0}
        return JsonResponse(response_data, safe=False)

def purchase_credit_ticket(request):
    data = json.loads(request.body)
    email = data['email']
    password = data['password']
    event_url = data['event_url']
    ticket_id = data['ticket_id']
    ticket_cnt = data['ticket_cnt']
    security_code = data['security_code']
    # webdriver_path = os.path.join(settings.BASE_DIR, 'chromedriver.exe')

    driver = webdriver.Chrome()
    try:
        # Open the webpage
        driver.get('https://t.livepocket.jp/login?acroot=header-new_p_u_nl')

        wait = WebDriverWait(driver, 10)
        email_field = wait.until(EC.presence_of_element_located((By.ID, 'email')))
        email_field.send_keys(email)
        password_field = wait.until(EC.presence_of_element_located((By.ID, 'password')))
        password_field.send_keys(password)

        login_button = driver.find_element(By.CSS_SELECTOR, '.btn-login-pc')
        login_button.click()
        time.sleep(5)
        driver.get(event_url)
        select_element = wait.until(EC.presence_of_element_located((By.ID, 'ticket-' + str(ticket_id))))
        select = Select(select_element)
        select.select_by_visible_text(str(ticket_cnt) +'枚')
        time.sleep(5)
        confirm_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'p.button.register.center-block.btn-procedure-pc-only button.register_input_submit.register_input_submit_pink')))
        confirm_button.click()
        checkbox = wait.until(EC.element_to_be_clickable((By.ID, 'agreement_check_lp')))
        checkbox.click()
        check_button = wait.until(EC.element_to_be_clickable((By.ID, 'submit-btn')))
        check_button.click()
        # driver.find_element_by_tag_name('body').send_keys(Keys.ENTER)
        time.sleep(3)
        alert = driver.switch_to.alert
        alert.accept()
        security_code_field = wait.until(EC.presence_of_element_located((By.ID, 'securityCode')))
        security_code_field.send_keys(security_code)
        buy_button = wait.until(EC.element_to_be_clickable((By.ID, 'exec-button')))
        buy_button.click()
        time.sleep(5)
        buy_button = wait.until(EC.element_to_be_clickable((By.ID, 'exec-button')))
        buy_button.click()
        time.sleep(20)
    finally:
        print('end')

    return JsonResponse({'confirmation': 'text'})

def purchase_ticket(request):
    if request.method == 'POST':
        with requests.session() as session:
            data = json.loads(request.body)
            eventId = data['event_id']
            payment_method = data['payment_method']
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36 Edg/99.0.1150.55'
            header = {
                'User-Agent': user_agent,
                'Cache-Control': 'max-age=0',
            }
            _ntpServer = 'ntp1.jst.mfeed.ad.jp'

            requestUrl = 'https://t.livepocket.jp/api/sessions/create?mytimestamp=' + str(int(getNtpTimeUnix(_ntpServer)*1000))

            requestData = {
                'login': data['email'],
                'password': data['password'],
                'login_password': data['email'] + '&' + data['password'],
            }
            res = session.get(requestUrl, headers=header)
            res = session.post(requestUrl, data=requestData, headers=header, cookies=res.cookies)
            requestUrl = 'https://t.livepocket.jp/purchase?type=new'
            res = session.get(requestUrl, headers=header)
            res = session.get(requestUrl, headers=header, cookies=res.cookies)
            requestData = {
                'type': '',
                'redirect_url': 'https://t.livepocket.jp/purchase/',
                'is_discontinuous': '',
                'is_unused_code': '',
                'event_id': '',
                'event_cname': '',
                'facebook_ticket_count': '0',
                'twitter_ticket_count': '0',
                'referer_type': '',
                'discount_code': '',
                'use_discount_code_time': '',
                'plusid_linkage_invalidation_flg': '0',
            }
            filtered_data = {k: v for k, v in data.items() if k.startswith("ticket_id")}
            ticket_id_key, ticket_id_value = next(iter(filtered_data.items()))
            requestData.update({ticket_id_key:ticket_id_value})
            requestData.update({"ticket_type":data['ticket_type']})
            requestData.update({"event_id":data['event_id']})
            requestData.update({"event_cname":data['event_cname']})
            res = session.post(requestUrl, data=requestData, headers=header, cookies=res.cookies)
            location = res.url
            locationPart = re.split('[=&]',location)
            reservedSessionId = locationPart[3]
            onetimeToken = locationPart[5]
            if payment_method == '0':
                if data['security_code']:
                    requestUrl = 'https://t.livepocket.jp/api/tickets/prepare_purchase?mytimestamp=' + str(int(getNtpTimeUnix(_ntpServer)*1000))
                else:
                    requestUrl = 'https://t.livepocket.jp/api/tickets/purchase?mytimestamp=' + str(int(getNtpTimeUnix(_ntpServer)*1000))
                parameterPaymentType = 'credit'
            else:
                requestUrl = 'https://t.livepocket.jp/api/tickets/prepare_purchase?mytimestamp=' + str(int(getNtpTimeUnix(_ntpServer)*1000))
                parameterPaymentType = 'cvs'
            requestData = {
                'utoken': data['utoken'],
                'onetime_token_name': 'buy_ticket',
                'onetime_token_value': onetimeToken,
                'url': 'https://t.livepocket.jp/purchase/confirm?id=' + eventId + '&reserved_session_id=' + reservedSessionId,
                'reserve_session_id': reservedSessionId,
                'payment_method': payment_method,
                'event_id': eventId,
                'payment_type': parameterPaymentType,
                'order_id': '',
                'notified': 'true',
                'serial_codes': 'null',
                'fan_club': 'null',
                'use_discount_id': '',
                'use_discount_code_id': '',
            }
            if payment_method == '0':
                if(data['security_code']):
                    security_code = data['security_code']
                    requestData.update({"security_code": security_code})
            else:
                selected_cvs_code = data['selected_cvs_code']
                requestData.update({"selected_cvs_code": selected_cvs_code})
            res = session.post(requestUrl, data=requestData, headers=header, cookies=res.cookies)
            jsonData = json.loads(res.text)
            if(jsonData['success'] == False):
                response_data = {"status":'fail',"data":jsonData}
                return JsonResponse(response_data, safe=False)
            orderId = jsonData['result']['order_id']
            onetimeToken = jsonData['result']['onetime_token_value']
            if payment_method == '0':
                if data['security_code']:
                    requestUrl = 'https://t.livepocket.jp/purchase/credit_confirm'
                    requestData = {
                        'id' : eventId,
                        'reserved_session_id' : reservedSessionId,
                        'payment_method_type' :'',
                        'note':'',
                        'order_id': orderId,
                        'onetime_token_name': 'buy_ticket',
                        'onetime_token_value': onetimeToken,
                    }
                    res = session.post(requestUrl, data=requestData, headers=header, cookies=res.cookies)
                    print(res.text)
                    response_data = {"data":'samples'}
                else:
                    requestUrl = 'https://t.livepocket.jp/purchase/enquate'
                    requestData = {
                        'reserve_session_id': reservedSessionId,
                        'order_id': orderId,
                        'onetime_token_name': 'buy_ticket',
                        'onetime_token_value': onetimeToken,
                    }
                    res = session.post(requestUrl, data=requestData, headers=header, cookies=res.cookies)
                    
                    response_data = {"data":res.text}
            else:
                requestUrl = 'https://t.livepocket.jp/purchase/cvs_confirm'
                selected_cvs_code = data['selected_cvs_code']
                requestData = {
                    'id': eventId,
                    'reserved_session_id': reservedSessionId,
                    'payment_method_type': parameterPaymentType,
                    'note': "",
                    'selected_cvs_code': selected_cvs_code,
                    'order_id': orderId,
                    'onetime_token_name': 'buy_ticket',
                    'onetime_token_value': onetimeToken,
                }
                res = session.post(requestUrl, data=requestData, headers=header, cookies=res.cookies)
                requestUrl = 'https://t.livepocket.jp/purchase/form_redirect?onetime_token_name=buy_ticket&onetime_token_value=' + onetimeToken
                res = session.get(requestUrl, headers=header, cookies=res.cookies)
                if res.history:
                    for resp in res.history:
                        print(f"Redirected from {resp.url} to {resp.headers['Location']}")
                    print(f"Final destination: {res.url}")
                else:
                    print("No redirects")
                # requestUrl = 'https://t.livepocket.jp/purchase/enquate?order_id=' + orderId + '&onetime_token_name=buy_ticket&onetime_token_value=' + onetimeToken
                # res = session.get(requestUrl, headers=header, cookies=res.cookies)
                # # if res.history:
                # #     for resp in res.history:
                # #         print(f"Redirected from {resp.url} to {resp.headers['Location']}")
                # #     print(f"Final destination: {res.url}")
                # # else:
                # #     print("No redirects")                
                # requestUrl = 'https://t.livepocket.jp/purchase/complete?order_id=' + orderId
                # res = session.get(requestUrl, headers=header, cookies=res.cookies)
                response_data = {"data":res.text}
    else:
        response_data = {'msg': 'This endpoint accepts only POST requests.'}
    return JsonResponse(response_data, safe=False)

