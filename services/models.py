from django.core.validators import MinValueValidator
from django.db import models


class Service(models.Model):
    """A grooming service offered by CutZone (e.g. Haircut)."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    duration_minutes = models.PositiveIntegerField(
        validators=[MinValueValidator(5)],
        help_text="How long the service takes, in minutes.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["price"]

    def __str__(self):
        return f"{self.name} (₦{self.price:,.0f} / {self.duration_minutes} min)"
