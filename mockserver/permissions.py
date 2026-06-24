"""Permission helpers for collection sharing.

Rules:
- Owner: full access (view, edit, delete) to collection and endpoints.
- Editor: can view & edit endpoints in the shared collection. Cannot delete.
- Viewer: can only view endpoints in the shared collection.
- Unauthenticated / unrelated users: no access to private collections.
"""

from __future__ import annotations

from django.db import models
from django.http import HttpRequest

from mockserver.models import Collection, Endpoint


def get_collections_queryset_for_user(
    base_queryset,
    user,
) -> "QuerySet[Collection]":
    """Filter a Collection queryset down to what *user* is allowed to see.

    Includes: owned collections, public collections, and shared collections.
    """
    if not user or not user.is_authenticated:
        return base_queryset.filter(visibility=Collection.Visibility.PUBLIC)

    shared_ids = user.shared_collections.values_list("collection_id", flat=True)
    return base_queryset.filter(
        models.Q(created_by=user.get_username())
        | models.Q(visibility=Collection.Visibility.PUBLIC)
        | models.Q(id__in=shared_ids),
    )


def get_endpoints_queryset_for_user(
    base_queryset,
    user,
) -> "QuerySet[Endpoint]":
    """Filter an Endpoint queryset down to what *user* is allowed to see.

    Includes: endpoints in owned collections, public collections, and shared collections.
    """
    if not user or not user.is_authenticated:
        return base_queryset.filter(
            collection__visibility=Collection.Visibility.PUBLIC,
        )

    shared_ids = user.shared_collections.values_list("collection_id", flat=True)
    return base_queryset.filter(
        models.Q(collection__created_by=user.get_username())
        | models.Q(collection__visibility=Collection.Visibility.PUBLIC)
        | models.Q(collection__id__in=shared_ids),
    )


def can_edit_endpoint(endpoint: Endpoint, user, request: HttpRequest | None = None) -> bool:
    """Return True if *user* can modify this endpoint.

    Owners and editors of the parent collection can edit.
    """
    collection = endpoint.collection
    if collection is None:
        return False
    return collection.user_can_edit(user)


def can_delete_endpoint(endpoint: Endpoint, user) -> bool:
    """Return True if *user* can delete this endpoint.

    Only the collection owner can delete endpoints.
    """
    collection = endpoint.collection
    if collection is None:
        return False
    return collection.is_owner(user)


def can_delete_collection(collection: Collection, user) -> bool:
    """Return True if *user* can delete this collection.

    Only the collection owner can delete.
    """
    return collection.is_owner(user)
