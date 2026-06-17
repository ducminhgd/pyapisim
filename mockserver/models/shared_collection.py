from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class SharedCollection(models.Model):
    """SharedCollection model"""

    class Role(models.TextChoices):
        UNKNOWN = "UNKNOWN", _("Unknown")
        VIEWER = "VIEWER", _("Viewer")
        EDITOR = "EDITOR", _("Editor")
        OWNER = "OWNER", _("Owner")

    collection = models.ForeignKey(
        "Collection", on_delete=models.CASCADE, related_name="shared_collections"
    )
    shared_with = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="shared_collections"
    )
    role = models.CharField(max_length=20, choices=Role, default=Role.UNKNOWN)
    
    def __str__(self):
        return f"[{self.collection.code}] Shared with {self.shared_with}"