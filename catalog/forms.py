from django import forms

from .models import Category, Tag, TagMatch


class ProductFilterForm(forms.Form):
    """Field names match ProductQuerySet.filter_by keyword arguments."""

    q = forms.CharField(label="Description contains", required=False, max_length=200)
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(), required=False, empty_label="All categories"
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(), required=False, widget=forms.CheckboxSelectMultiple
    )
    tag_match = forms.ChoiceField(
        label="Show products with",
        choices=TagMatch.choices,
        required=False,
        widget=forms.RadioSelect,
    )

    # The view always binds GET data, so `initial` would be ignored; default the data instead.
    def __init__(self, data=None, *args, **kwargs):
        if data is not None and not data.get("tag_match"):
            data = data.copy()
            data["tag_match"] = TagMatch.ANY
        super().__init__(data, *args, **kwargs)
