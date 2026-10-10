from decimal import Decimal
from typing import NamedTuple

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Category, Product, Tag


class SeedProduct(NamedTuple):
    name: str
    category: str
    price: str
    tags: tuple[str, ...]
    description: str


CATEGORIES = (
    "Electronics",
    "Books",
    "Home & Kitchen",
    "Sports & Outdoors",
    "Toys & Games",
)

TAGS = (
    "new",
    "sale",
    "bestseller",
    "eco-friendly",
    "wireless",
    "portable",
    "gift",
    "premium",
    "kids",
    "outdoor",
)

PRODUCTS = (
    SeedProduct(
        "Noise-Cancelling Headphones",
        "Electronics",
        "199.99",
        ("wireless", "premium", "bestseller"),
        "Over-ear wireless headphones with active noise cancellation and 30-hour battery life.",
    ),
    SeedProduct(
        "Bluetooth Speaker",
        "Electronics",
        "49.99",
        ("wireless", "portable", "outdoor"),
        "Waterproof portable speaker with deep bass, ideal for outdoor adventures.",
    ),
    SeedProduct(
        "Smart Watch",
        "Electronics",
        "149.00",
        ("new", "wireless", "gift"),
        "Fitness tracking smart watch with heart-rate monitor and wireless sync.",
    ),
    SeedProduct(
        "USB-C Power Bank",
        "Electronics",
        "29.99",
        ("portable", "sale"),
        "Compact 10,000 mAh power bank with fast charging for phones and tablets.",
    ),
    SeedProduct(
        "The Pragmatic Programmer",
        "Books",
        "39.95",
        ("bestseller", "gift"),
        "Classic software engineering book on craftsmanship and pragmatic practices.",
    ),
    SeedProduct(
        "Clean Code",
        "Books",
        "34.50",
        ("bestseller",),
        "A handbook of agile software craftsmanship focused on readable, maintainable code.",
    ),
    SeedProduct(
        "Bedtime Stories Collection",
        "Books",
        "14.99",
        ("kids", "gift"),
        "Illustrated collection of short bedtime stories for young readers.",
    ),
    SeedProduct(
        "Hiking Trail Guide",
        "Books",
        "19.99",
        ("outdoor", "new"),
        "Pocket guide to the best hiking trails with maps and difficulty ratings.",
    ),
    SeedProduct(
        "Bamboo Cutting Board",
        "Home & Kitchen",
        "24.99",
        ("eco-friendly", "sale"),
        "Durable, eco-friendly bamboo cutting board that is gentle on knife edges.",
    ),
    SeedProduct(
        "Stainless Steel Water Bottle",
        "Home & Kitchen",
        "18.00",
        ("eco-friendly", "portable", "outdoor"),
        "Insulated reusable bottle keeps drinks cold for 24 hours; a portable eco-friendly choice.",
    ),
    SeedProduct(
        "Espresso Machine",
        "Home & Kitchen",
        "329.00",
        ("premium", "new"),
        "Premium espresso machine with milk frother for cafe-quality coffee at home.",
    ),
    SeedProduct(
        "Air Fryer",
        "Home & Kitchen",
        "89.99",
        ("bestseller", "sale"),
        "Healthy air fryer that cooks crispy food with little or no oil.",
    ),
    SeedProduct(
        "Yoga Mat",
        "Sports & Outdoors",
        "25.00",
        ("eco-friendly", "portable"),
        "Non-slip eco-friendly yoga mat made of natural rubber, lightweight and portable.",
    ),
    SeedProduct(
        "Camping Tent",
        "Sports & Outdoors",
        "129.99",
        ("outdoor", "premium"),
        "Four-person waterproof camping tent with quick setup for outdoor trips.",
    ),
    SeedProduct(
        "Mountain Bike Helmet",
        "Sports & Outdoors",
        "59.99",
        ("outdoor", "new"),
        "Lightweight ventilated helmet designed for mountain biking and trail riding.",
    ),
    SeedProduct(
        "Adjustable Dumbbells",
        "Sports & Outdoors",
        "179.00",
        ("premium", "bestseller"),
        "Space-saving adjustable dumbbells from 5 to 52 lbs for home workouts.",
    ),
    SeedProduct(
        "Building Blocks Set",
        "Toys & Games",
        "44.99",
        ("kids", "gift", "bestseller"),
        "Creative building blocks set with 500 pieces to spark imagination in kids.",
    ),
    SeedProduct(
        "Remote Control Car",
        "Toys & Games",
        "39.99",
        ("kids", "wireless", "outdoor"),
        "Fast wireless remote control car with rechargeable battery for outdoor fun.",
    ),
    SeedProduct(
        "Strategy Board Game",
        "Toys & Games",
        "34.99",
        ("gift", "new"),
        "Family strategy board game for 2-4 players that rewards planning and trading.",
    ),
    SeedProduct(
        "Wooden Puzzle",
        "Toys & Games",
        "15.99",
        ("kids", "eco-friendly", "sale"),
        "Eco-friendly wooden jigsaw puzzle made from sustainable wood for kids.",
    ),
)


class Command(BaseCommand):
    help = "Load sample categories, tags and products. Safe to run multiple times."

    @transaction.atomic
    def handle(self, *args, **options):

        categories_by_name = {
            name: Category.objects.get_or_create(name=name)[0] for name in CATEGORIES
        }
        tags_by_name = {name: Tag.objects.get_or_create(name=name)[0] for name in TAGS}

        new_product_count = 0
        for seed_product in PRODUCTS:
            product, was_created = Product.objects.get_or_create(
                name=seed_product.name,
                category=categories_by_name[seed_product.category],
                defaults={
                    "description": seed_product.description,
                    "price": Decimal(seed_product.price),
                },
            )
            if was_created:
                product.tags.set(
                    tags_by_name[tag_name] for tag_name in seed_product.tags
                )
                new_product_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete: {len(categories_by_name)} categories, {len(tags_by_name)} tags, "
                f"{new_product_count} new product(s) ({Product.objects.count()} total)."
            )
        )
