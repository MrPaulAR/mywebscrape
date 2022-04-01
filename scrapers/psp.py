import re
from dataclasses import dataclass
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from my_funcs import insert_sequence

from app import BaseUrl, Vendor

storename = 'PixelSequencePros'
BASEURL = "https://pixelsequencepros.com/"


@dataclass
class Sequence:
    name: str
    url: str
    price: str


def get_products_from_page(soup: BeautifulSoup, url: str) -> list[Sequence]:
    products = soup.find_all("li", class_="grid__item")
    sequences = []
    for product in products:
        sequence_name = product.find("a", class_="full-unstyled-link").text.strip()
        product_url = urljoin(BASEURL, product.find("a")["href"])
        p = product.find("div", class_="price__sale").text
        pattern = r'[^\d\.\$]+'
        price_text = re.sub(pattern, ' ', p).strip()
        pattern = re.compile("(\$\d[\d.]+).*(\$\d[\d.]+)")
        try:
            price = pattern.search(price_text)[2]
        except:
            price = price_text
        if price == "$0.00":
            price = "Free"
        sequences.append(Sequence(sequence_name, product_url, price))

    next_page = soup.find(class_="next")
    if next_page:
        response = httpx.get(next_page["href"])  # type: ignore
        next_soup = BeautifulSoup(response.text, "html.parser")
        sequences.extend(get_products_from_page(next_soup))

    return sequences


def main() -> None:
    print(f"Loading %s..." % storename)
    baseurls = BaseUrl.query.join(Vendor).add_columns(Vendor.name.label("vendor_name"))\
        .filter(Vendor.name == storename).order_by(BaseUrl.id).all()
    for baseurl in baseurls:
        print(f"Loading %s" % baseurl[0].url)
        response = httpx.get(baseurl[0].url)
        soup = BeautifulSoup(response.text, "html.parser")
        products = get_products_from_page(soup, baseurl[0].url)

        for product in products:
            insert_sequence(store=storename, url=product.url, name=product.name, price=product.price)


if __name__ == "__main__":
    main()
