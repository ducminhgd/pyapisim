from __future__ import annotations

from uuid import uuid4
from django.db import models
from django.utils.translation import gettext_lazy as _


class Collection(models.Model):
    """Collection model"""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        INACTIVE = "INACTIVE", _("Inactive")

    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC", _("Public")
        PRIVATE = "PRIVATE", _("Private")

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True, help_text="Unique code for the collection, example path: <BASE_URL>/mockapi/{code}/{endpoint-path}")
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status, default=Status.ACTIVE)
    visibility = models.CharField(
        max_length=20, choices=Visibility, default=Visibility.PRIVATE,
        help_text="Public collections are visible to all users, while private collections are only visible to the creator and shared users."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100)

    def __str__(self):
        return f"[{self.code}] {self.name}"
