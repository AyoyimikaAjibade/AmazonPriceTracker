import time
import json
from datetime import datetime
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from amazon_config import (
get_chrome_web_driver,
get_web_driver_options,
set_ignore_certificate_error,
set_browser_as_incognito,
set_automation_as_head_less,
DIRECTORY,
NAME,
FILTERS,
BASE_URL,
CURRENCY,
)

class GenerateReport:
    def __init__(self, file_name, filters, base_link, currency, data):
        self.data = data
        self.file_name = file_name
        self.filters = filters
        self.base_link = base_link
        self.currency = currency
        # individual keys and values of the report defined in json format
        report = {
            'title': self.file_name,
            'date':self.get_now(),
            'best_item': self.get_best_item(),
            'currency': self.currency,
            'filters': self.filters,
            'base_link': self.base_link,
            'products': self.data
        }
        print('Creating report...')
        # opening the file in a write mode and adding the report to the file
        with open(f"{DIRECTORY}/{file_name}.json", 'w') as f:
            json.dump(report, f)
        print("Done...")

    @staticmethod
    def get_now():
        '''
        set the time for report generation to now formatting the time neatly
        '''
        now = datetime.now()
        return now.strftime("%d/%m/%Y %H:%M:%S")

    def get_best_item(self):
        '''
        arrange the price from cheapest to expensive in the report
        '''
        try:
            return sorted(self.data, key=lambda k:k['price'])[0]
        except Exception as e:
            print(e)
            print("Problem with sorting items")
            return None

class AmazonAPI:
    def __init__(self, search_term, filters, base_url, currency):
        self.base_url = base_url
        self.search_term = search_term
        #passing all the web driver options to the function
        options = get_web_driver_options()
        # set_automation_as_head_less(options)
        set_ignore_certificate_error(options)
        set_browser_as_incognito(options)
        self.driver = get_chrome_web_driver(options)
        self.currency = currency
        #based on amazon url if the prices are filtered this varible identifies the filtered price which is actually
        #decimal divide by 100 in the url
        self.price_filter = f"&rh=p_36%3A{filters['min']}00-{filters['max']}00"

    def run(self):
        #log info to console
        print("Starting Script...")
        print(f"Looking for {self.search_term} products...")
        links = self.get_products_links()
        if not links:
            print("Stopped script.")
            return
        print(f"Got {len(links)} links to products...")
        print("Getting info about products...")
        products = self.get_products_info(links)
        print(f"Got info about {len(products)} products...")
        self.driver.quit()
        return products

    def get_products_links(self):
        '''
        this function is responsible for simulating selenium to input the search term value
        and getting all product links based on the filtered price parameter
        '''
        self.driver.get(self.base_url)
        element = self.driver.find_element_by_xpath('//*[@id="twotabsearchtextbox"]')
        element.send_keys(self.search_term)
        element.send_keys(Keys.ENTER)
        time.sleep(2)  # wait to load page
        self.driver.get(f'{self.driver.current_url}{self.price_filter}')
        print(f"Our url: {self.driver.current_url}")
        time.sleep(2)  # wait to load page
        result_list = self.driver.find_elements_by_class_name('s-result-list')
        links = []
        # if links not found the script doesn't brake
        try:
            results = result_list[0].find_elements_by_xpath(
                "//div/span/div/div/div[2]/div[2]/div/div[1]/div/div/div[1]/h2/a")
            links = [link.get_attribute('href') for link in results]
            return links
        except Exception as e:
            print("Didn't get any products...")
            print(e)
            return links

    def get_products_info(self, links):
        '''
        get the individual links and extract the asin or id so as to get all the products info
        '''
        asins = self.get_asins(links)
        products = []
        for asin in asins:
            product = self.get_single_product_info(asin)
            if product:
                products.append(product)
        return products

    def get_asins(self, links):
        '''
        get individual link
        '''
        return [self.get_asin(link) for link in links]

    def get_single_product_info(self, asin):
        '''
        get single info about current product
        '''
        print(f"Product ID: {asin} - getting data...")
        product_short_url = self.shorten_url(asin)
        self.driver.get(f'{product_short_url}?language=en_GB')
        time.sleep(2)
        title = self.get_title()
        seller = self.get_seller()
        price = self.get_price()
        if title and seller and price:
            product_info = {
                'asin': asin,
                'url': product_short_url,
                'title': title,
                'seller': seller,
                'price': price
            }
            return product_info
        return None

    def get_title(self):
        try:
            return self.driver.find_element_by_id('productTitle').text
        except Exception as e:
            print(e)
            print(f"Can't get title of a product - {self.driver.current_url}")
            return None

    def get_seller(self):
        try:
            return self.driver.find_element_by_id('bylineInfo').text
        except Exception as e:
            print(e)
            print(f"Can't get seller of a product - {self.driver.current_url}")
            return None

    def get_price(self):
        '''
        if the price is in the main section get it otherwise locate the price in the Available section for new product
         which is below in the section
        '''
        price = None
        try:
            price = self.driver.find_element_by_id('priceblock_ourprice').text
            price = self.convert_price(price)
        except NoSuchElementException:
            try:
                availability = self.driver.find_element_by_id('availability').text
                if 'Available' in availability:
                    price = self.driver.find_element_by_class_name('olp-padding-right').text
                    price = price[price.find(self.currency):]
                    price = self.convert_price(price)
            except Exception as e:
                print(e)
                print(f"Can't get price of a product - {self.driver.current_url}")
                return None
        except Exception as e:
            print(e)
            print(f"Can't get price of a product - {self.driver.current_url}")
            return None
        return price

    @staticmethod
    def get_asin(product_link):
        '''
         looking through individual links and get the value between /dp/ and /ref
        '''
        return product_link[product_link.find('/dp/') + 4:product_link.find('/ref')]

    def shorten_url(self, asin):
        '''
        shorten the long url to a shorter one that works through cutting out redundant links that still works
        '''
        return self.base_url + 'dp/' + asin

    def convert_price(self, price):
        price = price.split(self.currency)[1]
        try:
            price = price.split("\n")[0] + "." + price.split("\n")[1]
        except:
            Exception()
        try:
            price = price.split(",")[0] + price.split(",")[1]
        except:
            Exception()
        return float(price)


if __name__ == '__main__':
    am = AmazonAPI(NAME, FILTERS, BASE_URL, CURRENCY)
    data = am.run()
    GenerateReport(NAME, FILTERS, BASE_URL, CURRENCY, data)



