import argparse
import http.cookiejar
import json
import os.path
import re
import urllib.parse
import urllib.request
from datetime import datetime

import pytz
from bs4 import BeautifulSoup
from colorama import Fore
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

import private


def load_account(username, password):
    login_data = {
        'username': username,
        'password': password,
        'login': 'x',
    }

    print('[ImmiAccount] Logging in...')

    # Set up cookie, handler and opener.
    cookie = http.cookiejar.CookieJar()
    handler = urllib.request.HTTPCookieProcessor(cookie)
    opener = urllib.request.build_opener(handler)

    # Get the login page.
    web_response = opener.open('https://online.immi.gov.au/lusc/login')

    html_str = web_response.read().decode('utf-8')
    soup = BeautifulSoup(html_str, 'lxml')

    # Set up the data.
    web_inputs = soup.find_all('input')
    for web_input in web_inputs:
        if web_input['type'] == 'hidden':
            login_data[web_input['name']] = web_input['value']
    data = urllib.parse.urlencode(login_data).encode('utf-8')

    # Post the data to login.
    req = urllib.request.Request('https://online.immi.gov.au/lusc/login', data=data)
    login_response = opener.open(req)

    login_soup = BeautifulSoup(login_response.read().decode('utf-8'), 'lxml')

    # if login failed, exit.
    if login_soup.find('section', class_='messagebox error'):
        print('[ImmiAccount] Login failed.')
        exit(0)

    # if login successfully, continue.
    print('[ImmiAccount] Login successfully!')
    print('[ImmiAccount] Continue to the information page...')

    # Delete the username, password and login data.
    login_data.pop('username')
    login_data.pop('password')
    login_data.pop('login')

    # Set up the continue data.
    login_data['continue'] = 'x'

    # Post the continue data to continue.
    data = urllib.parse.urlencode(login_data).encode('utf-8')
    req = urllib.request.Request('https://online.immi.gov.au/lusc/login', data=data)
    success_response = opener.open(req)

    # Go to the information page.
    info_request = urllib.request.Request('https://online.immi.gov.au/lusc/pac')
    info_response = opener.open(info_request)
    info_soup = BeautifulSoup(info_response.read().decode('utf-8'), 'lxml')

    result_set = info_soup.find('div', id='resultsTabSet').contents[0]

    print('[ImmiAccount] Getting the information...')

    contents = result_set.find_all('div', id=re.compile('MyAppsResultTab_?'))
    num_applications = int(len(contents) / 5)

    keys = ['ID', 'Applicant_Type', 'Status', 'Reference NO.', 'Type', 'Last Update']
    applications = []
    for idx in range(num_applications):
        applicant = {}

        banner = result_set.find('div', id='MyAppsResultTab_{}_0-body'.format(idx))
        left_side = result_set.find_all('div', id=re.compile('leftSidePanel_{}_?[0-9]a[0-9]$'.format(idx)))
        right_side = result_set.find_all('div', id=re.compile('rightSidePanel_{}_?[0-9]a[0-9]$'.format(idx)))

        key_id = 0
        for cid in range(len(banner.contents)):
            applicant[keys[key_id]] = banner.contents[cid].text
            key_id += 1

        for lid in range(len(left_side) - 1):
            applicant[keys[key_id]] = left_side[lid].find('div').text
            key_id += 1

        applicant['Last Update'] = right_side[0].find('time')['datetime']
        applications.append(applicant)

    print('[ImmiAccount] Information got.')

    return applications


def load_processing_time():
    processing_time = {'ID': 'Global Processing Time'}
    tz_au = pytz.timezone('Australia/Sydney')
    # time_format_au = '%d/%m/%Y %I:%M %p'
    time_format_au = '%d %B %Y'

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Connection': 'keep-alive',
        'Content-type': 'application/x-www-form-urlencoded',
        'Origin': 'https://chat.homeaffairs.gov.au',
        'Referer': 'https://chat.homeaffairs.gov.au/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.41',
        'sec-ch-ua': '"Chromium";v="118", "Microsoft Edge";v="118", "Not=A?Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    print('[Processing Time] Getting the processing time...')

    driver_options = webdriver.EdgeOptions()
    driver_options.add_argument('headless')
    driver = webdriver.Edge(options=driver_options)

    driver.get(
        'https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-processing-times/global-visa-processing-times')

    status_wait = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'pageModified')))

    updated_date = datetime.strptime(driver.find_element('id', 'pageModified').text, time_format_au)
    processing_time['Last Update'] = updated_date.astimezone(tz_au).strftime('%Y-%m-%d')

    driver.find_element('id', 'applicationdate').send_keys('31/05/2023')  # Application Date
    Select(driver.find_element('id', 'visatype')).select_by_value('500')  # Visa Type: Student Visa
    Select(driver.find_element('id', 'visastream')).select_by_value('45')  # Visa Stream: Postgraduate Research Sector

    driver.find_element('id', 'visualtrackerbutton').click()

    status_wait = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'process-info-right')))

    visa_info = driver.find_element('id', 'visa-info-left').text
    processing_time['Visa Type'] = driver.find_element(By.CLASS_NAME, 'title').text
    processing_time['Visa Stream'] = driver.find_element(By.CLASS_NAME, 'subtitle').text
    processing_time['Processing Time'] = driver.find_element(
        By.CLASS_NAME, 'guide-info').find_element(
        By.TAG_NAME, 'span').text

    driver.quit()

    print('[Processing Time] Processing time got.')

    return processing_time


def compare_json_lists(json_list1, json_list2):
    differences = []
    len1 = len(json_list1)
    len2 = len(json_list2)
    i = j = 0

    while i < len1 and j < len2:
        if json_list1[i] != json_list2[j]:
            differences.append((json_list1[i], json_list2[j]))
        i += 1
        j += 1

    while i < len1:
        differences.append((json_list1[i], None))
        i += 1

    while j < len2:
        differences.append((None, json_list2[j]))
        j += 1

    return differences


def send_mail(config, mail_content='', status=''):
    import iMail

    print('[Mail Sender] Sending mail...')

    # Set the Mail Sender
    mail_obj = iMail.EMAIL(host=config.mail_host, sender_addr=config.sender_address, pwd=config.mail_password,
                           sender_name=config.sender_name)
    mail_obj.set_receiver(config.mail_to)

    # Create a new email
    mail_obj.new_mail(subject='[{}] Visa Status Change Detected!'.format(status), encoding='UTF-8')

    # Write content
    mail_obj.add_text(content=mail_content)

    # Send the email
    mail_obj.send_mail()

    print('[Mail Sender] Mail sent.')


if __name__ == "__main__":

    parser = argparse.ArgumentParser('ImmiAccount Status Checker')
    parser.add_argument('--username', type=str, default=private.USERNAME, help='Username')
    parser.add_argument('--password', type=str, default=private.PASSWD, help='Password')
    parser.add_argument('--path', type=str, default='./saves', help='Path to save the data')
    parser.add_argument('--file', type=str, default='data.json', help='File name to save the data')
    parser.add_argument('--mail_host', type=str, default=private.MAIL_HOST, help='Mail server')
    parser.add_argument('--sender_address', type=str, default=private.SENDER_ADDRESS, help='Sender address')
    parser.add_argument('--sender_name', type=str, default=private.SENDER_NAME, help='Sender name')
    parser.add_argument('--mail_password', type=str, default=private.MAIL_PASSWORD, help='Mail password')
    parser.add_argument('--mail_to', type=str, default=private.RECEIVER, help='Mail to')
    args = parser.parse_args()

    if not os.path.exists(args.path):
        os.mkdir(args.path)

    print('\n', '-' * 10, 'ImmiAccount Status Checker', '-' * 10, '\n')

    # today_data = [load_processing_time()]
    today_data = load_account(args.username, args.password)

    color_map = {'Granted': Fore.GREEN, 'Finalised': Fore.YELLOW, 'Refused': Fore.RED, 'Further assessment': Fore.CYAN}
    visa_status = today_data[0]['Status']
    print('[Visa Status] Your Visa Status: {}'.format(color_map[visa_status] + visa_status + Fore.RESET))

    file_path = os.path.join(args.path, args.file)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            past_data = json.load(f)
            if len(compare_json_lists(past_data, today_data)) == 0:
                print('[Data Writer] No change detected.')
                print('[Checker] Exit.')
                print('\n', '-' * 10, 'ImmiAccount Status Checker', '-' * 10, '\n')
                exit(0)

    with open(file_path, 'w', encoding='utf-8') as f:

        print('[Data Writer] Change detected.')
        print('[Data Writer] Saving data...')
        json.dump(today_data, f, ensure_ascii=False, indent=4)
        print('[Data Writer] Data saved.')

        send_mail(args, mail_content=json.dumps(today_data, ensure_ascii=False, indent=4),
                  status=today_data[0]['Status'])

        print('[Checker] Exit.')
        print('\n', '-' * 10, 'ImmiAccount Status Checker', '-' * 10, '\n')