from __future__ import annotations

from uuid import uuid4
from django.db import models
from django.utils.translation import gettext_lazy as _

class Endpoint(models.Model):
    """Endpoint model"""

    class Status(models.TextChoices):
        UNKNOWN = "UNKNOWN", _("Unknown")
        ACTIVE = "ACTIVE", _("Active")
        INACTIVE = "INACTIVE", _("Inactive")
        DELETED = "DELETED", _("Deleted")

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    collection = models.ForeignKey(
        "Collection", on_delete=models.SET_NULL, related_name="endpoints", null=True, blank=True
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    path = models.CharField(max_length=200)
    allowed_methods = models.JSONField(default=list)
    http_status_code = models.IntegerField(default=200)
    response_headers = models.JSONField(default=dict)
    response_body = models.TextField(blank=True, null=True)
    delay_ms = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status, default=Status.UNKNOWN)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100)

    def __str__(self):
        return f"[{self.name}] {self.path}"