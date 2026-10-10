from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from catalog.models import Category, Product, Tag


class SeedCatalogCommandTests(TestCase):
    def run_seed(self) -> str:
        out = StringIO()
        call_command("seed_catalog", stdout=out)
        return out.getvalue()

    def test_meets_minimum_dataset_requirements(self):
        self.run_seed()
        self.assertGreaterEqual(Category.objects.count(), 5)
        self.assertGreaterEqual(Tag.objects.count(), 10)
        self.assertGreaterEqual(Product.objects.count(), 20)
        self.assertFalse(Product.objects.filter(tags__isnull=True).exists())

    def test_is_idempotent_and_preserves_admin_edits(self):
        self.run_seed()
        product = Product.objects.first()
        product.tags.clear()

        output = self.run_seed()

        self.assertIn("0 new product(s)", output)
        self.assertEqual(Product.objects.count(), 20)
        self.assertEqual(product.tags.count(), 0)
