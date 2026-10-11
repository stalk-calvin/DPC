import logging

from django.views.generic import ListView

from .forms import ProductFilterForm
from .models import Product

logger = logging.getLogger(__name__)


class ProductListView(ListView):
    """The product page: validates the filters, then lists matching products, 5 per page."""

    template_name = "product_list.html"
    context_object_name = "products"
    paginate_by = 5

    def get_queryset(self):
        # Kept on the view so get_context_data() can render it with the user's choices.
        self.form = ProductFilterForm(self.request.GET)
        products = Product.objects.with_related()
        # Invalid input (e.g. an unknown category id) shows form errors and no results.
        if not self.form.is_valid():
            logger.warning(
                "Rejected product filters %r: %s",
                self.request.GET.urlencode(),
                self.form.errors.as_json(),
            )
            return products.none()
        # The form's field names match filter_by()'s keyword arguments.
        return products.filter_by(**self.form.cleaned_data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(form=self.form, **kwargs)
        # The paginator has already counted the results, so this adds no query.
        logger.debug(
            "Product list %r: %d result(s), page %d",
            self.request.GET.urlencode(),
            context["paginator"].count,
            context["page_obj"].number,
        )
        return context
