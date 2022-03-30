import re
from dataclasses import dataclass
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from my_funcs import insert_sequence

from app import BaseUrl, Vendor

storename = 'ShowStoppers'


@dataclass
class Sequence:
    name: str
    url: str
    price: str


BASEURL = "https://showstoppersequences-com.3dcartstores.com/"


def get_products_from_page(soup: BeautifulSoup, url: str) -> list[Sequence]:

    products = soup.find_all("div", class_="product-item item-template-0 alternative")

    sequences = []
    for product in products:
        sequence_name = product.find("div", class_="name").find("a").text
        # song, artist = sequence_name.split(" - ")
        product_url = urljoin(BASEURL, product.find("a")["href"])
        p_text = product.find("div", class_="price").text.strip()
        if not p_text:
            price = "Free"
        else:
            pattern = re.compile(".*(\$[0-9]+\.[0-9]+).*")
            price = pattern.search(p_text).group(1)
        sequences.append(Sequence(sequence_name, product_url, price))

    next_page = soup.find("a", text="Next Page")
    if next_page:
        next_page_url = urljoin(url, next_page["href"])  # type: ignore
        print(f"Loading %s" % (next_page_url))
        response = httpx.get(next_page_url)
        next_soup = BeautifulSoup(response.text, "html.parser")
        sequences.extend(get_products_from_page(next_soup, url))

    return sequences


def main() -> None:
    print(f"Loading %s" % storename)
    baseurls = BaseUrl.query.join(Vendor).add_columns(Vendor.name.label("vendor_name")) \
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
