from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from catalog.models import Category, Product, Tag

from .factories import make_category, make_product, make_tag


class NamedModelTests(TestCase):
    def test_str_returns_name(self):
        self.assertEqual(str(make_category("Books")), "Books")
        self.assertEqual(str(make_tag("sale")), "sale")

    def test_names_are_unique_case_insensitively_in_database(self):
        for model in (Category, Tag):
            with self.subTest(model=model.__name__):
                model.objects.create(name="Outdoor")
                with self.assertRaises(IntegrityError), transaction.atomic():
                    model.objects.create(name="outdoor")

    def test_duplicate_name_is_reported_by_validation_before_hitting_database(self):
        make_category("Books")
        with self.assertRaisesMessage(
            ValidationError, "An entry with this name already exists."
        ):
            Category(name="BOOKS").full_clean()

    def test_names_are_trimmed_on_save(self):
        for model in (Category, Tag):
            with self.subTest(model=model.__name__):
                self.assertEqual(model.objects.create(name="  Garden  ").name, "Garden")

    def test_padded_duplicate_name_is_reported_by_validation(self):
        make_category("Books")
        with self.assertRaisesMessage(
            ValidationError, "An entry with this name already exists."
        ):
            Category(name="  books ").full_clean()

    def test_default_ordering_is_by_name(self):
        make_tag("b")
        make_tag("a")
        self.assertEqual(list(Tag.objects.values_list("name", flat=True)), ["a", "b"])


class ProductModelTests(TestCase):
    def test_str_returns_name(self):
        self.assertEqual(str(make_product(name="Lamp")), "Lamp")

    def test_negative_price_is_rejected_by_database_constraint(self):
        with self.assertRaises(IntegrityError):
            make_product(price="-1.00")

    def test_negative_price_is_rejected_by_validation(self):
        product = Product(name="X", description="d", price=-1, category=make_category())
        with self.assertRaises(ValidationError) as ctx:
            product.full_clean()
        self.assertIn("price", ctx.exception.message_dict)

    def test_name_is_unique_within_category_but_not_across_categories(self):
        books, toys = make_category(), make_category()
        make_product(name="Classic", category=books)
        make_product(name="Classic", category=toys)
        with self.assertRaises(IntegrityError):
            make_product(name="Classic", category=books)

    def test_deleting_category_with_products_is_blocked(self):
        product = make_product()
        with self.assertRaises(ProtectedError):
            product.category.delete()

    def test_deleting_tag_only_removes_the_association(self):
        tag = make_tag()
        product = make_product(tags=(tag,))
        tag.delete()
        product.refresh_from_db()
        self.assertEqual(product.tags.count(), 0)
