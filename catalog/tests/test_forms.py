from django.test import TestCase

from catalog.forms import ProductFilterForm
from catalog.models import TagMatch

from .factories import make_category, make_tag


class ProductFilterFormTests(TestCase):
    def test_empty_input_is_valid_and_means_no_filters(self):
        form = ProductFilterForm({})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["q"], "")
        self.assertIsNone(form.cleaned_data["category"])
        self.assertEqual(list(form.cleaned_data["tags"]), [])
        self.assertEqual(form.cleaned_data["tag_match"], TagMatch.ANY)

    def test_valid_input_is_converted_to_model_instances(self):
        category, tag = make_category(), make_tag()
        form = ProductFilterForm(
            {
                "q": "  lamp  ",
                "category": category.pk,
                "tags": [tag.pk],
                "tag_match": "all",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["q"], "lamp")
        self.assertEqual(form.cleaned_data["category"], category)
        self.assertEqual(list(form.cleaned_data["tags"]), [tag])
        self.assertEqual(form.cleaned_data["tag_match"], TagMatch.ALL)

    def test_unknown_ids_and_choices_are_rejected(self):
        form = ProductFilterForm({"category": 999, "tags": [999], "tag_match": "some"})
        self.assertFalse(form.is_valid())
        self.assertEqual(set(form.errors), {"category", "tags", "tag_match"})

    def test_overly_long_search_is_rejected(self):
        self.assertFalse(ProductFilterForm({"q": "x" * 201}).is_valid())
