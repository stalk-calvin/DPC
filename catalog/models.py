from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Count
from django.db.models.functions import Lower


class NamedModel(models.Model):
    """Shared by Category and Tag: a trimmed name that is unique regardless of case."""

    name = models.CharField(max_length=100)

    class Meta:
        # No table of its own; Category and Tag each get one with these rules.
        abstract = True
        ordering = ["name"]
        constraints = [
            # Enforced by the database, so "Books" and "books" can't both exist.
            models.UniqueConstraint(
                Lower("name"),
                name="%(app_label)s_%(class)s_name_ci_unique",
                violation_error_message="An entry with this name already exists.",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    # full_clean() calls clean() before checking constraints, so " books " is caught as a duplicate.
    def clean(self):
        self.name = self.name.strip()

    # Also trim here for code paths that skip validation (shell, seed command).
    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        super().save(*args, **kwargs)


class Category(NamedModel):
    # Inherit the parent's ordering and unique rule; only fix the admin's plural ("Categorys").
    class Meta(NamedModel.Meta):
        verbose_name_plural = "categories"


class Tag(NamedModel):
    pass


# The value ("any"/"all") appears in the URL; the label is shown on the page.
class TagMatch(models.TextChoices):
    ANY = "any", "At least one selected tag"
    ALL = "all", "Every selected tag"


class ProductQuerySet(models.QuerySet):
    """Chainable product filters. Each returns the queryset unchanged when its input is empty."""

    # Avoids N+1 queries: JOIN each product's category and fetch all tags in one extra query.
    def with_related(self):
        return self.select_related("category").prefetch_related("tags")

    # Case-insensitive "contains" on the description only, as the requirements specify.
    def search(self, term: str = ""):
        term = (term or "").strip()
        return self.filter(description__icontains=term) if term else self

    def in_category(self, category=None):
        return self.filter(category=category) if category else self

    def with_tags(self, tags=(), match: str = TagMatch.ANY):
        # Accepts Tag objects or primary keys; the set drops duplicates.
        tag_ids = {getattr(tag, "pk", tag) for tag in tags}
        if not tag_ids:
            return self

        # Subquery on the join table instead of a JOIN: no duplicate rows, so no DISTINCT needed.
        matching_tag_links = Product.tags.through.objects.filter(tag_id__in=tag_ids)
        if match == TagMatch.ALL:
            # "Every tag": keep products whose number of matching links equals the number selected.
            matching_tag_links = (
                matching_tag_links.values("product_id")
                .annotate(matched_tag_count=Count("tag_id"))
                .filter(matched_tag_count=len(tag_ids))
            )
        return self.filter(pk__in=matching_tag_links.values("product_id"))

    # Each step adds an AND condition, so search, category and tags combine.
    def filter_by(self, *, q="", category=None, tags=(), tag_match=TagMatch.ANY):
        return self.search(q).in_category(category).with_tags(tags, tag_match)


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    # Decimal, not float, so prices are exact.
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )

    # Many-to-one: each product has exactly one category.
    category = models.ForeignKey(
        Category,
        # Refuse to delete a category that still has products, instead of deleting them too.
        on_delete=models.PROTECT,
        related_name="products",
    )
    # Many-to-many: Django stores the links in a separate join table (catalog_product_tags).
    tags = models.ManyToManyField(Tag, blank=True, related_name="products")

    # Makes the ProductQuerySet methods available as Product.objects.search(...), etc.
    objects = ProductQuerySet.as_manager()

    class Meta:
        # pk breaks ties between equal names, so pagination is stable.
        ordering = ["name", "pk"]
        indexes = [models.Index(fields=["name"])]
        # Rules live in the database so every code path obeys them; forms show these messages.
        constraints = [
            models.UniqueConstraint(
                fields=["category", "name"],
                name="catalog_product_unique_name_per_category",
                violation_error_message="A product with this name already exists in this category.",
            ),
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="catalog_product_price_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return self.name
