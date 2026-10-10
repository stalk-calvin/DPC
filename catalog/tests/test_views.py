from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from .factories import make_category, make_product, make_tag

URL = reverse("product-list")


class ProductListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.books = make_category("Books")
        cls.toys = make_category("Toys")
        cls.gift = make_tag("gift")
        cls.novel = make_product(
            name="Novel", description="A gripping novel", category=cls.books
        )
        cls.puzzle = make_product(
            name="Puzzle",
            description="Wooden puzzle",
            category=cls.toys,
            tags=(cls.gift,),
        )

    def test_lists_all_products_without_filters(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, "product_list.html")
        self.assertQuerySetEqual(
            response.context["products"], [self.novel, self.puzzle]
        )

    def test_applies_search_and_filters_from_query_string(self):
        response = self.client.get(
            URL, {"q": "wooden", "category": self.toys.pk, "tags": [self.gift.pk]}
        )
        self.assertQuerySetEqual(response.context["products"], [self.puzzle])
        self.assertContains(response, "1 product found")

    def test_invalid_filters_show_errors_and_no_results(self):

        with self.assertLogs("catalog.views", "WARNING") as logs:
            response = self.client.get(URL, {"category": 999})
        self.assertIn("Rejected product filters 'category=999'", logs.output[0])
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertContains(response, "No products match your criteria.")

    def test_user_input_is_html_escaped(self):
        response = self.client.get(URL, {"q": "<script>alert(1)</script>"})
        self.assertNotContains(response, "<script>alert(1)</script>")

    def test_at_least_one_tag_is_preselected(self):
        response = self.client.get(URL)
        self.assertEqual(response.context["form"]["tag_match"].value(), "any")

    def test_pagination_links_keep_active_filters(self):
        for _ in range(10):
            make_product(description="Another gripping novel", category=self.books)
        response = self.client.get(URL, {"q": "gripping"})
        self.assertTrue(response.context["is_paginated"])
        self.assertContains(response, "?q=gripping&amp;page=2")

    def test_query_count_does_not_grow_with_number_of_products(self):
        def count_queries() -> int:
            with CaptureQueriesContext(connection) as ctx:
                self.client.get(URL)
            return len(ctx)

        baseline = count_queries()
        for _ in range(5):
            make_product(category=self.books, tags=(self.gift,))
        self.assertEqual(count_queries(), baseline)
