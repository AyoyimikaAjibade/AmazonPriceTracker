from selenium import webdriver

DIRECTORY = 'reports'
NAME = 'iphone'
CURRENCY = '€'
MIN_PRICE = '4.59'
MAX_PRICE = '12.9'
FILTERS = {
    'min': MIN_PRICE,
    'max': MAX_PRICE
}
BASE_URL = 'https://www.amazon.de/'

'''
selenium and chromedriver default setting for scrapping a website
'''
def get_chrome_web_driver(options):
    return webdriver.Chrome('./chromedriver', chrome_options=options)


def get_web_driver_options():
    return webdriver.ChromeOptions()


def set_ignore_certificate_error(options):
    options.add_argument('--ignore-certificate-errors')


def set_browser_as_incognito(options):
    options.add_argument('--incognito')


def set_automation_as_head_less(options):
    options.add_argument('--headless')

