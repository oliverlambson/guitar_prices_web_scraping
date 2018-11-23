"""
Web scraping script for getting guitar prices from themusiczoo.com
"""
from bs4 import BeautifulSoup as soup
from requests import get
from requests.exceptions import Timeout

brand = 'Gibson'
subbrand = 'Custom Shop'
ranges = ['Les Paul', 'SG']
year = 2018
url = 'https://www.themusiczoo.com/collections/gibson-custom-shop/new+solid-body-electric?page=1'
idx = url.find('/', url.find('/') + 2)
url_base = url[:idx]

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

page_no = 1
last_page = 1

guitars = []
while page_no <= last_page:
    try:
        response = get(url, headers=headers, timeout=10)
        assert(response.status_code == 200) # raise error if not 200 response

        html_soup = soup(response.text, 'lxml')

        products = html_soup.findAll('div', {'class': 'product-bottom'})
        if page_no == 1:
            pagination = html_soup.find('ul', {'class': 'pagination-page'}).findAll('li')
            last_page = int(pagination[-2].text.strip())
            if last_page > 9:
                print('Too many pages... Only reading 9 pages. Need to change code.')
                last_page = 9

        products = products[9:] # returns 9 irrelevant guitars first

        # print('\n'.join(product.prettify() for product in products))

        for i, product in enumerate(products):
            link = url_base + product.find('a', 'product-title')['href']
            name = product.find('a', 'product-title').find('span')
            price = product.find('span', 'money')
            name = name.string.strip()
            price = price.string.strip()
            price = price.replace('$','').replace(',','')
            price = float(price)
            guitars.append({
                'name': name,
                'price': price,
                'link': link
            })


        # print('\n'.join(f"{guitar['name']:63.63} {guitar['price']:7}" for guitar in guitars))

        page_no += 1
        url = url[:-1] + str(page_no)
    except Timeout as e:
        print(e)
        print('Server timeout.')
        exit()
    except AssertionError as e:
        print(e)
        exit()


print(f'{last_page} pages parsed.')
print(f'{len(guitars)} guitars found.')
print('-'*79)
print('\n'.join(f"{guitar['name']:63.63} {guitar['price']:7}" for guitar in guitars))

# brand
# subbrand
# rnge
# model
# variant
# year
# price
# source
# date_collected
