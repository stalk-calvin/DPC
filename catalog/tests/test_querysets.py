from django.test import TestCase

from catalog.models import Product, TagMatch

from .factories import make_category, make_product, make_tag


class ProductQuerySetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.electronics = make_category("Electronics")
        cls.outdoors = make_category("Outdoors")
        cls.wireless = make_tag("wireless")
        cls.portable = make_tag("portable")
        cls.sale = make_tag("sale")

        cls.headphones = make_product(
            name="Headphones",
            description="Wireless over-ear headphones",
            category=cls.electronics,
            tags=(cls.wireless,),
        )
        cls.speaker = make_product(
            name="Speaker",
            description="Portable WIRELESS speaker",
            category=cls.electronics,
            tags=(cls.wireless, cls.portable),
        )
        cls.tent = make_product(
            name="Tent",
            description="Two-person camping tent",
            category=cls.outdoors,
            tags=(cls.portable, cls.sale),
        )

    def assertProducts(self, queryset, expected):
        self.assertQuerySetEqual(queryset, expected, ordered=False)

    def test_search_matches_description_case_insensitively(self):
        self.assertProducts(
            Product.objects.search("wireless"), [self.headphones, self.speaker]
        )

    def test_search_only_looks_at_description_not_name(self):
        make_product(name="Mystery Box", description="Surprise item")
        self.assertProducts(Product.objects.search("mystery"), [])

    def test_blank_search_returns_everything(self):
        for term in ("", "   ", None):
            with self.subTest(term=term):
                self.assertEqual(Product.objects.search(term).count(), 3)

    def test_in_category(self):
        self.assertProducts(Product.objects.in_category(self.outdoors), [self.tent])
        self.assertEqual(Product.objects.in_category(None).count(), 3)

    def test_with_tags_any_returns_each_product_once(self):
        result = Product.objects.with_tags([self.wireless, self.portable])
        self.assertProducts(result, [self.headphones, self.speaker, self.tent])
        self.assertEqual(
            result.count(), 3, "products matching several tags must not repeat"
        )

    def test_with_tags_all_requires_every_tag(self):
        result = Product.objects.with_tags(
            [self.wireless, self.portable], match=TagMatch.ALL
        )
        self.assertProducts(result, [self.speaker])

    def test_with_tags_accepts_primary_keys(self):
        self.assertProducts(Product.objects.with_tags([self.sale.pk]), [self.tent])

    def test_with_no_tags_returns_everything(self):
        self.assertEqual(Product.objects.with_tags([]).count(), 3)

    def test_filter_by_combines_all_criteria_with_and(self):
        result = Product.objects.filter_by(
            q="wireless",
            category=self.electronics,
            tags=[self.portable],
            tag_match=TagMatch.ANY,
        )
        self.assertProducts(result, [self.speaker])

    def test_filter_by_without_criteria_returns_everything(self):
        self.assertEqual(Product.objects.filter_by().count(), 3)

    def test_with_related_avoids_extra_queries_per_product(self):

        products_joined_with_category_query, tags_prefetch_query = 1, 1
        with self.assertNumQueries(
            products_joined_with_category_query + tags_prefetch_query
        ):
            category_and_tag_names = [
                (product.category.name, [tag.name for tag in product.tags.all()])
                for product in Product.objects.with_related()
            ]
        self.assertEqual(len(category_and_tag_names), 3)
