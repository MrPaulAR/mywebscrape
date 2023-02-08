from urllib.parse import urljoin

import re
import httpx
from app import Sequence, Vendor
from bs4 import BeautifulSoup
from my_funcs import create_or_update_sequences, get_unique_vendor


storename = "RGBSequences"


def get_products_from_page(
    soup: BeautifulSoup, url: str, vendor: Vendor
) -> list[Sequence]:

    products = soup.find_all("div", class_="grid__item small--one-half medium-up--one-fifth")
    sequences = []
    for product in products:
        sequence_name = product.find(class_="product-card__name").text
        product_url = urljoin(url, product.find("a")["href"])
        price_str = product.find(class_="product-card__price")
        price = re.findall(r".*\$([0-9\.]+).*", price_str.text)[0]
        if price == "$0.00" or price == "0":
            price = "Free"
        sequences.append(
            Sequence(
                name=sequence_name, vendor_id=vendor.id, link=product_url, price=price
            )
        )
        print(sequence_name, product_url, price)
    next_page = soup.find("span", class_="next")
    if next_page:
        next_url = urljoin(url, next_page.find("a")["href"])
        response = httpx.get(next_url, timeout=30.0)  # type: ignore
        next_soup = BeautifulSoup(response.text, "html.parser")
        sequences.extend(get_products_from_page(soup=next_soup, url=url, vendor=vendor))

    return sequences


def main() -> None:
    print(f"Loading {storename}")
    vendor = get_unique_vendor(storename)

    for url in vendor.urls:
        print(f"Loading {url.url}")
        response = httpx.get(url.url, timeout=30.0)
        soup = BeautifulSoup(response.text, "html.parser")
        sequences = get_products_from_page(soup=soup, url=url.url, vendor=vendor)

        create_or_update_sequences(sequences)


if __name__ == "__main__":
    main()
