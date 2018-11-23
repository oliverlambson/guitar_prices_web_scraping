"""
Web scraping script for getting guitar prices from themusiczoo.com
"""
import sys
import csv
import yaml
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
if 'config' in sys.argv:
    idx = sys.argv.index('config')
    config_file = sys.argv[idx+1]
else:
    config_file = 'themusiczoo-gibson-custom_shop'
    config_file = 'themusiczoo-gibson-usa'
    config_file = 'themusiczoo-fender-custom_shop'
    config_file = 'themusiczoo-fender-american'
    config_file = 'themusiczoo-prs-private_stock'
    config_file = 'themusiczoo-prs-core'
    config_file = 'themusiczoo-prs-bolt_on'
    config_file = 'themusiczoo-prs-s2'
    config_file = 'themusiczoo-prs-se'
    config_file = 'themusiczoo-fender-mim'
    config_file = 'themusiczoo-fender-squier'
    print(f'No config file given--using {config_file}')

if 'write_csv' in sys.argv:
    write_csv = True
else:
    write_csv = False
    write_csv = True
    print(f'Using default write to csv--{write_csv}.')

config_path = 'config/'
config_file += '.yaml'
try:
    with open(config_path + config_file, 'r') as f:
        config = yaml.load(f)

    brand = config['brand']
    subbrand = config['subbrand']
    check_subbrand = config['check_subbrand']
    ranges = config['ranges']
    year = config['year']
    store = config['store']
    url = config['url']
    if 'check_brand' in config:
        check_brand = config['check_brand']
    else:
        check_brand = None
    if 'alt_brand' in config:
        alt_brand = config['alt_brand']
    else:
        alt_brand = None
    if 'exclude' in config:
        exclude = config['exclude']
    else:
        exclude = None
    if 'remove' in config:
        remove = config['remove']
    else:
        remove = None
    if 'min_price' in config:
        min_price = config['min_price']
    else:
        min_price = 0
    if 'max_price' in config:
        max_price = config['max_price']
    else:
        max_price = 1e7
except:
    print('Config. error.')
    exit()

csv_path = 'csv/'
csv_name = (f'{store}-{brand}-{subbrand}').replace(' ', '_').lower()

url_base = get_base_url(url)

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

page_no = 1
last_page = 1
guitars_found = 0
duplicate_models = 0
invalid_guitars = []
out_price_guitars = []
unknown_guitars = []
excluded_guitars = []
guitars = []

while page_no <= last_page:
    try:
        response = get(url, headers=headers, timeout=30)
        print(f'page {page_no} response received')
        assert(response.status_code == 200) # raise error if not 200 response

        html_soup = soup(response.text, 'lxml')

        products = html_soup.findAll('div', {'class': 'product-bottom'})
        if page_no == 1:
            pagination = html_soup.find('ul', {'class': 'pagination-page'})
            if pagination != None:
                pagination = pagination.findAll('li')
                last_page = int(pagination[-2].text.strip())
                if last_page > 9:
                    print('Too many pages... Only reading 9 pages. Need to change code.')
                    last_page = 9

        products = products[9:] # returns 9 irrelevant guitars first
        guitars_found += len(products)

        for i, product in enumerate(products):
            link = url_base + product.find('a', 'product-title')['href']

            descrip = product.find('a', 'product-title').find('span')
            descrip = descrip.string.strip()
            if alt_brand:
                descrip = descrip.replace(alt_brand, brand)
            if remove:
                descrip = ' '.join(descrip.replace(remove, '').split())

            price = product.find('span', 'money')
            price = price.string.strip()
            price = get_price(price)

            if check_brand:
                b_test = brand
            else:
                b_test = ''
            if check_subbrand:
                sb_test = subbrand
            else:
                sb_test = ''

            if check_valid(descrip, b_test, sb_test):
                rnge = get_range(descrip, ranges)
                if rnge != None:
                    model = get_model(descrip, brand, subbrand, rnge)
                    models = [guitar['model'] for guitar in guitars]
                    if model not in models:
                        if (not exclude) or (exclude not in descrip):
                            if min_price < price < max_price:
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
                                out_price_guitars.append((descrip, price))
                        else:
                            excluded_guitars.append((descrip, price))
                    else:
                        duplicate_models += 1
                else:
                    unknown_guitars.append((descrip, price))
            else:
                invalid_guitars.append((descrip, price))


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
invalid_guitars_count = len(invalid_guitars)
out_price_guitars_count = len(out_price_guitars)
excluded_guitars_count = len(excluded_guitars)
unknown_guitars_count = len(unknown_guitars)

print('-'*79)
# print('\n'.join(f"{guitar['descrip']:63.63} {guitar['price']:7}" for guitar in guitars))
print('Guitars found:')
print('\n'.join(
    f"{guitar['brand']:7.7} "
    f"{guitar['subbrand']:15.15} "
    f"{guitar['range']:15.15} "
    f"{guitar['model']:15.15} "
    f"{guitar['price']:8.2f}" for guitar in guitars)
)
print('-'*79)
if invalid_guitars_count > 0:
    invalid_guitars.sort(key=lambda item: item[1], reverse=True)
    print('Invalid guitars found:')
    print('\n'.join(f'{guitar[1]:8.2f} {guitar[0]}' for guitar in invalid_guitars))
    print('-'*79)
if unknown_guitars_count > 0:
    unknown_guitars.sort(key=lambda item: item[1], reverse=True)
    print('Unknown guitars found:')
    print('\n'.join(f'{guitar[1]:8.2f} {guitar[0]}' for guitar in unknown_guitars))
    print('-'*79)
if excluded_guitars_count > 0:
    excluded_guitars.sort(key=lambda item: item[1], reverse=True)
    print('Exlcuded guitars:')
    print('\n'.join(f'{guitar[1]:8.2f} {guitar[0]}' for guitar in excluded_guitars))
    print('-'*79)
if out_price_guitars_count > 0:
    out_price_guitars.sort(key=lambda item: item[1], reverse=True)
    print('Guitars with price out of range:')
    print('\n'.join(f'{guitar[1]:8.2f} {guitar[0]}' for guitar in out_price_guitars))
    print('-'*79)
print(f'{last_page:3} pages parsed.')
print(f'{guitars_found:3} guitars found.')
print(f'{invalid_guitars_count:3} invalid guitars found.')
print(f'{unknown_guitars_count:3} unknown guitars found.')
print(f'{duplicate_models:3} duplicate guitars found.')
print(f'{excluded_guitars_count:3} guitars excluded.')
print(f'{out_price_guitars_count:3} guitar prices out of range.')
print(f'{guitars_added:3} guitars recorded.')
print('-'*79)

if write_csv == True:
    csv_name += '.csv'
    with open(csv_path + csv_name, 'w') as f:
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
