import logging

from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.admin.models import LogEntry
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.db.models import Count
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Category, Product, Tag

logger = logging.getLogger(__name__)


# Deleting several objects at once uses bulk_create (no signal), so only single-object actions are logged.
@receiver(post_save, sender=LogEntry)
def log_admin_action(sender, instance, created, **kwargs):
    if created:
        logger.info(
            "Admin %r on %s.%s %r: %s",
            instance.user.get_username(),
            instance.content_type.app_label,
            instance.content_type.model,
            instance.object_repr,
            "Deleted." if instance.is_deletion() else instance.get_change_message(),
        )


@receiver(user_login_failed)
def log_failed_login(sender, credentials, **kwargs):
    logger.warning("Login failed for username %r", credentials.get("username"))


@receiver(user_logged_in)
def log_login(sender, user, **kwargs):
    logger.debug("User %r logged in", user.get_username())


class AdminLoginForm(AdminAuthenticationForm):
    # One message for both cases on purpose: never reveal that a password was correct.
    error_messages = {
        **AdminAuthenticationForm.error_messages,
        "invalid_login": (
            "Login failed. Either the username or password is wrong, or this account "
            "does not have admin access (“Staff status” must be ticked on the user)."
        ),
    }


admin.site.login_form = AdminLoginForm


@admin.register(Category, Tag)
class NamedModelAdmin(admin.ModelAdmin):
    list_display = ("name", "product_count")
    search_fields = ("name",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(product_count=Count("products"))

    @admin.display(description="Products", ordering="product_count")
    def product_count(self, category_or_tag) -> int:
        return category_or_tag.product_count


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "tag_list")
    list_filter = ("category", "tags")
    list_select_related = ("category",)
    search_fields = ("name", "description")
    autocomplete_fields = ("category",)
    filter_horizontal = ("tags",)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("tags")

    @admin.display(description="Tags")
    def tag_list(self, product: Product) -> str:
        return ", ".join(tag.name for tag in product.tags.all())
