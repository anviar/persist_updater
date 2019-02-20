# -*- coding: utf-8 -*-
from selenium.webdriver import Chrome, chrome
import pickle
from pathlib import Path
from configparser import ConfigParser
import subprocess
from time import sleep
import logging
from logging.handlers import RotatingFileHandler

# some work variables
workdir = Path(__file__).resolve().parent
cookies_file_path = workdir / 'cookies.dat'
config = ConfigParser()
config.read(workdir / 'config.ini')

logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=config['main']['verbose'],
    handlers=[
        RotatingFileHandler(
            workdir / 'main.log',
            maxBytes=104857600,
            backupCount=10
        )]
)

logging.debug('Initiating Slenium server using {}'.format(config['selenium']['jar']))
with open(workdir / 'selenium.log', 'wt') as log:
    selenium_process = subprocess.Popen(
        ['java', '-jar', config['selenium']['jar']],
        stderr=subprocess.STDOUT, stdout=log)
sleep(config['selenium'].getint('delay'))

options = chrome.options.Options()
options.add_argument("headless")
options.add_argument("disable-gpu")
options.add_argument("no-sandbox")
browser = Chrome(options=options)
browser.set_window_size(1920, 1080)
browser.maximize_window()
browser.get('https://hh.ru/404')
if cookies_file_path.exists():
    with open(cookies_file_path, 'rb') as cookies_file:
        for cookie in pickle.load(cookies_file):
            browser.add_cookie(cookie)
browser.get('https://hh.ru/applicant/resumes')
if len(browser.find_elements_by_class_name('resumelist__resume')) == 0:
    logging.warning('resume list not found, trying to auth')
    login_form = browser.find_elements_by_xpath('//form[@data-qa="account-login-form"]')[1]
    login_form.find_element_by_name('username').send_keys(config['hh']['username'])
    login_form.find_element_by_name('password').send_keys(config['hh']['password'])
    login_form.find_element_by_xpath('.//input[@data-qa="account-login-submit"]').click()
    browser.get('https://hh.ru/applicant/resumes')
resumes = browser.find_elements_by_xpath('.//div[@data-qa="resume "]')
for res in resumes:
    title = res.find_element_by_xpath('.//span[@data-qa="resume-title"]').text
    refresh_button = res.find_elements_by_class_name('bloko-icon-link')
    if len(refresh_button) == 1 and refresh_button[0].is_enabled():
        try:
            refresh_button[0].click()
            logging.info("Updated: {}".format(title))
        except Exception as e:
            print(e)
    else:
        logging.debug("Already up to date: {}".format(title))
with open(cookies_file_path, 'wb') as cookies_file:
    pickle.dump(browser.get_cookies(), cookies_file)
browser.close()
browser.quit()
selenium_process.terminate()
