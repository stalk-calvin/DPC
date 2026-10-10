from django.contrib import admin
from django.urls import path

from catalog.views import ProductListView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", ProductListView.as_view(), name="product-list"),
]
