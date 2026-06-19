from __future__ import annotations

from uuid import uuid4
from django.db import models
from django.utils.translation import gettext_lazy as _


def _default_allowed_methods():
    return ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]


class Endpoint(models.Model):
    """Endpoint model"""
    class Meta:
        unique_together = ("collection", "path")

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        INACTIVE = "INACTIVE", _("Inactive")

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    collection = models.ForeignKey(
        "Collection",
        on_delete=models.SET_NULL,
        related_name="endpoints",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    path = models.CharField(max_length=200, help_text="Unique path for the endpoint, example path: <BASE_URL>/mockapi/{code}/{path}")
    allowed_methods = models.JSONField(default=_default_allowed_methods)
    http_status_code = models.IntegerField(default=200)
    response_headers = models.JSONField(default=dict, blank=True)
    response_body = models.TextField(blank=True, null=True)
    delay_ms = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100)

    def __str__(self):
        return f"[{self.name}] {self.path}"
