from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from mockserver.models.shared_collection import SharedCollection


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
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique code for the collection, example path: <BASE_URL>/mockapi/{code}/{endpoint-path}",
    )
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status, default=Status.ACTIVE)
    visibility = models.CharField(
        max_length=20,
        choices=Visibility,
        default=Visibility.PRIVATE,
        help_text="Public collections are visible to all users, while private collections are only visible to the creator and shared users.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100)

    def is_owner(self, user) -> bool:
        """Return True if *user* is the creator of this collection."""
        if not user or not user.is_authenticated:
            return False
        return user.get_username() == self.created_by

    def get_user_role(self, user) -> str | None:
        """Return the role string (VIEWER / EDITOR) if the collection is shared with *user*, else None."""
        if not user or not user.is_authenticated:
            return None
        share = self.shared_collections.filter(shared_with=user).first()
        return share.role if share else None

    def user_can_view(self, user) -> bool:
        """Return True if *user* can view this collection."""
        if self.is_owner(user):
            return True
        if self.visibility == self.Visibility.PUBLIC:
            return True
        return self.get_user_role(user) is not None

    def user_can_edit(self, user) -> bool:
        """Return True if *user* can edit endpoints in this collection."""
        if self.is_owner(user):
            return True
        from mockserver.models.shared_collection import SharedCollection as _SC

        return self.get_user_role(user) == _SC.Role.EDITOR

    def user_can_delete(self, user) -> bool:
        """Return True if *user* can delete this collection or its endpoints."""
        return self.is_owner(user)

    def delete(self, *args, **kwargs):
        """Delete this collection along with all its endpoints and sharing records.

        Endpoints use ``on_delete=SET_NULL`` so they are not cascade-deleted by the
        database.  We explicitly delete them here so no orphaned endpoints remain.
        """
        from django.db import transaction

        with transaction.atomic():
            self.endpoints.all().delete()
            super().delete(*args, **kwargs)

    def duplicate(self, new_code: str, new_name: str, created_by: str) -> Collection:
        """Create a deep copy of this collection.

        Copies all scalar fields, all endpoints, and all sharing records into a
        new ``Collection``. Runs inside ``transaction.atomic()`` so the entire
        clone succeeds or fails as a unit.

        Returns:
            The newly created ``Collection`` instance.
        """
        from django.db import transaction

        from mockserver.models.endpoint import Endpoint
        from mockserver.models.shared_collection import SharedCollection as _SC

        with transaction.atomic():
            new_collection = Collection.objects.create(
                name=new_name,
                code=new_code,
                description=self.description,
                status=self.status,
                visibility=self.visibility,
                created_by=created_by,
                updated_by=created_by,
            )

            # Clone all endpoints.
            for ep in self.endpoints.all():
                Endpoint.objects.create(
                    collection=new_collection,
                    name=ep.name,
                    description=ep.description,
                    path=ep.path,
                    allowed_methods=ep.allowed_methods,
                    http_status_code=ep.http_status_code,
                    response_headers=ep.response_headers,
                    response_body=ep.response_body,
                    delay_ms=ep.delay_ms,
                    status=ep.status,
                    created_by=created_by,
                    updated_by=created_by,
                )

            # Clone all sharing records, except for the new creator
            # (the creator is already the owner and doesn't need a share).
            for share in self.shared_collections.all():
                if share.shared_with.get_username() == created_by:
                    continue
                _SC.objects.create(
                    collection=new_collection,
                    shared_with=share.shared_with,
                    role=share.role,
                )

        return new_collection

    def __str__(self):
        return f"[{self.code}] {self.name}"
