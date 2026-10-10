from decimal import Decimal
from itertools import count

from catalog.models import Category, Product, Tag

_sequence = count(1)


def make_category(name: str | None = None) -> Category:
    return Category.objects.create(name=name or f"Category {next(_sequence)}")


def make_tag(name: str | None = None) -> Tag:
    return Tag.objects.create(name=name or f"tag-{next(_sequence)}")


def make_product(
    *,
    name: str | None = None,
    description: str = "A product",
    price: Decimal | str = "9.99",
    category: Category | None = None,
    tags: tuple[Tag, ...] = (),
) -> Product:
    product = Product.objects.create(
        name=name or f"Product {next(_sequence)}",
        description=description,
        price=Decimal(price),
        category=category or make_category(),
    )
    product.tags.set(tags)
    return product
