"""
Web scraping script for getting guitar prices from themusiczoo.com
"""
import csv
from bs4 import BeautifulSoup as soup
from requests import get
from requests.exceptions import Timeout

def get_base_url(url):
    """
    url: 'https://www.aa.aa/bb/cc/...'
    return: 'https://www.aa.aa'
    """
    idx = url.find('/', url.find('/') + 2)
    return url[:idx]

def get_price(price):
    """
    price: '$xx,xxx.xx'
    return: float(xxxxx.xx)
    """
    price = price.replace('$','').replace(',','')
    return float(price)

def check_valid(s, brand, subbrand):
    """
    check if brand and subbrand in s
    example parameters:
    s: 'Gibson Custom Shop Standard Historic '60 Les Paul Rei...'
    brand: 'Gibson'
    subbrand: 'Custom Shop'
    return: True
    """
    return (brand in s) and (subbrand in s)

def get_range(s, ranges):
    """
    find range
    example parameters:
    s: 'Gibson Custom Shop Standard Historic '60 Les Paul Rei...'
    ranges: ['Les Paul', 'SG', ...]
    return: 'Les Paul'
    """
    for r in ranges:
        if r in s:
            return r
    return None

def get_model(s, brand, subbrand, rnge):
    """
    get model by removing brand, subbrand, rnge from s
    example parameters:
    s: 'Gibson Custom Shop Standard Historic '60 Les Paul Rei...'
    brand: 'Gibson'
    subbrand: 'Custom Shop'
    range: 'Les Paul'
    return: 'Standard Historic '60 Rei...'
    """
    s = s.replace(brand, '').replace(subbrand, '').replace(rnge, '')
    s = s.strip()
    s = ' '.join(s.split())
    return s

# init
write_csv = False
csv_name = 'themusiczoo_gibson_custom_shop'

brand = 'Gibson'
subbrand = 'Custom Shop'
ranges = ['Les Paul', 'SG', 'Firebird']
year = 2018

url = 'https://www.themusiczoo.com/collections/gibson-custom-shop/new+solid-body-electric?page=1'
url_base = get_base_url(url)

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

page_no = 1
last_page = 1
guitars_found = 0
invalid_guitars = 0
duplicate_models = 0
unknown_guitars = []
guitars = []

while page_no <= last_page:
    try:
        response = get(url, headers=headers, timeout=30)
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
        guitars_found += len(products)

        # print('\n'.join(product.prettify() for product in products))

        for i, product in enumerate(products):
            link = url_base + product.find('a', 'product-title')['href']

            descrip = product.find('a', 'product-title').find('span')
            descrip = descrip.string.strip()

            if check_valid(descrip, brand, subbrand):
                rnge = get_range(descrip, ranges)
                if rnge != None:
                    model = get_model(descrip, brand, subbrand, rnge)
                    models = [guitar['model'] for guitar in guitars]
                    if model not in models:
                        price = product.find('span', 'money')
                        price = price.string.strip()
                        price = get_price(price)


                        guitars.append({
                            'descrip': descrip,
                            'brand': brand,
                            'subbrand': subbrand,
                            'range': rnge,
                            'model': model,
                            'variant': '',
                            'price': price,
                            'year': year,
                            'link': link
                        })
                    else:
                        duplicate_models += 1
                else:
                    unknown_guitars.append(descrip)
            else:
                invalid_guitars += 1


        # print('\n'.join(f"{guitar['descrip']:63.63} {guitar['price']:7}" for guitar in guitars))

        page_no += 1
        url = url[:-1] + str(page_no)
    except Timeout as e:
        print(e)
        print('Server timeout.')
        break
    except AssertionError as e:
        print(e)
        break

guitars_added = len(guitars)
unknown_guitars_count = len(unknown_guitars)

print('-'*79)
# print('\n'.join(f"{guitar['descrip']:63.63} {guitar['price']:7}" for guitar in guitars))
print('\n'.join(
    f"{guitar['brand']:7.7} "
    f"{guitar['subbrand']:15.15} "
    f"{guitar['range']:15.15} "
    f"{guitar['model']:15.15} "
    f"{guitar['price']:7}" for guitar in guitars)
)
print('-'*79)
if unknown_guitars_count > 0:
    print('Unknown guitars found:')
    print('\n'.join(guitar for guitar in unknown_guitars))
    print('-'*79)
print(f'{last_page:3} pages parsed.')
print(f'{guitars_found:3} guitars found.')
print(f'{invalid_guitars:3} invalid guitars found.')
print(f'{unknown_guitars_count:3} unknown guitars found.')
print(f'{duplicate_models:3} duplicate guitars found.')
print(f'{guitars_added:3} guitars added.')
print('-'*79)

if unknown_guitars_count == 0 and invalid_guitars == 0 and write_csv == True:
    csv_name += '.csv'
    with open(csv_name, 'w') as f:
        writer = csv.DictWriter(f,
            fieldnames=[
                'brand',
                'subbrand',
                'range',
                'model',
                'variant',
                'year',
                'price'
            ],
            extrasaction='ignore',
            delimiter=';'
        )
        writer.writerows(guitars)
    print(f'{guitars_added:3} guitars written to {csv_name}')

# brand
# subbrand
# rnge
# model
# variant
# year
# price
# source
# date_collected
