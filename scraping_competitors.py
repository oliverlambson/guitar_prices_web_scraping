from bs4 import BeautifulSoup as soup
from requests import get

url = 'https://www.themusiczoo.com/collections/gibson-custom-shop/electric-guitars+new?page=1'
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

response = get(url, headers=headers)
html_soup = soup(response.text, 'lxml')

products = html_soup.findAll('div', {'class': 'product-bottom'})

print('\n'.join(product.prettify() for product in products))

guitars = []
for i, product in enumerate(products):
    name = product.find('a', 'product-title').find('span')
    price = product.find('span', 'money')
    name = name.string.strip()
    price = price.string.strip()
    price = price.replace('$','').replace(',','')
    price = float(price)
    guitars.append({
        'name': name,
        'price': price
    })
for guitar in guitars:
    print(f"{guitar['name']:63.63} {guitar['price']:7}")
