from __future__ import annotations

from uuid import uuid4
from django.db import models
from django.utils.translation import gettext_lazy as _


class Collection(models.Model):
    """Collection model"""

    class Status(models.TextChoices):
        UNKNOWN = "UNKNOWN", _("Unknown")
        ACTIVE = "ACTIVE", _("Active")
        INACTIVE = "INACTIVE", _("Inactive")
        DELETED = "DELETED", _("Deleted")

    class Visibility(models.TextChoices):
        UNKNOWN = "UNKNOWN", _("Unknown")
        PUBLIC = "PUBLIC", _("Public")
        PRIVATE = "PRIVATE", _("Private")

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status, default=Status.UNKNOWN)
    visibility = models.CharField(
        max_length=20, choices=Visibility, default=Visibility.UNKNOWN
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100)

    def __str__(self):
        return f"[{self.code}] {self.name}"
