import logging

from django.views.generic import ListView

from .forms import ProductFilterForm
from .models import Product

logger = logging.getLogger(__name__)


class ProductListView(ListView):
    template_name = "product_list.html"
    context_object_name = "products"
    paginate_by = 5

    def get_queryset(self):
        self.form = ProductFilterForm(self.request.GET)
        products = Product.objects.with_related()
        if not self.form.is_valid():
            logger.warning(
                "Rejected product filters %r: %s",
                self.request.GET.urlencode(),
                self.form.errors.as_json(),
            )
            return products.none()
        return products.filter_by(**self.form.cleaned_data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(form=self.form, **kwargs)
        logger.debug(
            "Product list %r: %d result(s), page %d",
            self.request.GET.urlencode(),
            context["paginator"].count,
            context["page_obj"].number,
        )
        return context
