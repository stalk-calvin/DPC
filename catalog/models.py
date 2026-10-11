from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Count
from django.db.models.functions import Lower


class NamedModel(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        abstract = True
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="%(app_label)s_%(class)s_name_ci_unique",
                violation_error_message="An entry with this name already exists.",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self):
        self.name = self.name.strip()

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        super().save(*args, **kwargs)


class Category(NamedModel):
    class Meta(NamedModel.Meta):
        verbose_name_plural = "categories"


class Tag(NamedModel):
    pass


class TagMatch(models.TextChoices):
    ANY = "any", "At least one selected tag"
    ALL = "all", "Every selected tag"


class ProductQuerySet(models.QuerySet):
    def with_related(self):
        return self.select_related("category").prefetch_related("tags")

    def search(self, term: str = ""):
        term = (term or "").strip()
        return self.filter(description__icontains=term) if term else self

    def in_category(self, category=None):
        return self.filter(category=category) if category else self

    def with_tags(self, tags=(), match: str = TagMatch.ANY):
        tag_ids = {getattr(tag, "pk", tag) for tag in tags}
        if not tag_ids:
            return self

        # Subquery on the join table instead of a JOIN: no duplicate rows, so no DISTINCT needed.
        matching_tag_links = Product.tags.through.objects.filter(tag_id__in=tag_ids)
        if match == TagMatch.ALL:
            matching_tag_links = (
                matching_tag_links.values("product_id")
                .annotate(matched_tag_count=Count("tag_id"))
                .filter(matched_tag_count=len(tag_ids))
            )
        return self.filter(pk__in=matching_tag_links.values("product_id"))

    def filter_by(self, *, q="", category=None, tags=(), tag_match=TagMatch.ANY):
        return self.search(q).in_category(category).with_tags(tags, tag_match)


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="products")

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["name", "pk"]
        indexes = [models.Index(fields=["name"])]
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
