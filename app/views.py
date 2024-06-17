from bs4 import BeautifulSoup
from django.shortcuts import render
import ntplib
import requests
import re



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


def purchase_ticket(request):
    if request.method == 'POST':
        with requests.session() as session:
            data = json.loads(request.body)
            eventId = data['event_id']
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36 Edg/99.0.1150.55'
            header = {
                'User-Agent': user_agent,
                'Cache-Control': 'max-age=0',
            }
            _ntpServer = 'ntp1.jst.mfeed.ad.jp'

            requestUrl = 'https://t.livepocket.jp/api/sessions/create?mytimestamp=' + str(int(getNtpTimeUnix(_ntpServer)*1000))

            requestDatadata = {
                'login': data['email'],
                'password': data['password'],
                'login_password': data['email'] + '&' + data['password'],
            }
            res = session.get(requestUrl, headers=header)
            res = session.post(requestUrl, data=requestDatadata, headers=header, cookies=res.cookies)
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
            if res.history:
                for resp in res.history:
                    print(f"Redirected from {resp.url} to {resp.headers['Location']}")
                print(f"Final destination: {res.url}")
            else:
                print("No redirects")
            location = res.url
            locationPart = re.split('[=&]',location)
            print(locationPart)
            reservedSessionId = locationPart[3]
            onetimeToken = locationPart[5]
            requestUrl = 'https://t.livepocket.jp/api/tickets/purchase?mytimestamp=' + str(int(getNtpTimeUnix(_ntpServer)*1000))
            requestData = {
                'utoken': data['utoken'],
                'onetime_token_name': 'buy_ticket',
                'onetime_token_value': onetimeToken,
                'url': 'https://t.livepocket.jp/purchase/confirm?id=' + eventId + '&reserved_session_id=' + reservedSessionId,
                'reserve_session_id': reservedSessionId,
                'payment_method': 0,
                'event_id': eventId,
                'payment_type': 'credit',
                'order_id': '',
                'notified': 'true',
                'serial_codes': 'null',
                'fan_club': 'null',
                'use_discount_id': '',
                'use_discount_code_id': '',
                'security_code': ''
            }
            res = session.post(requestUrl, data=requestData, headers=header, cookies=res.cookies)
            jsonData = json.loads(res.text)
            orderId = jsonData['result']['order_id']
            onetimeToken = jsonData['result']['onetime_token_value']
            requestUrl = 'https://t.livepocket.jp/purchase/enquate'
            requestData = {
                'reserve_session_id': reservedSessionId,
                'order_id': orderId,
                'onetime_token_name': 'buy_ticket',
                'onetime_token_value': onetimeToken,
            }
            res = session.post(requestUrl, data=requestData, headers=header, cookies=res.cookies)
            if res.history:
                for resp in res.history:
                    print(f"Redirected from {resp.url} to {resp.headers['Location']}")
                print(f"Final destination: {res.url}")
            else:
                print("No redirects")
            response_data = {"data":res.text}
    else:
        response_data = {'msg': 'This endpoint accepts only POST requests.'}
    return JsonResponse(response_data, safe=False)

