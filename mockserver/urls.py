from __future__ import annotations

from django.urls import path

from mockserver.admin_views import DuplicateCollectionView, DuplicateEndpointView, ToggleStatusView
from mockserver.models import Collection, Endpoint

app_name = "mockserver"

urlpatterns = [
    path(
        "mockserver/collection/<uuid:pk>/duplicate/",
        DuplicateCollectionView.as_view(),
        name="collection_duplicate",
    ),
    path(
        "mockserver/collection/<uuid:pk>/toggle-status/",
        ToggleStatusView.as_view(),
        {"model_class": Collection},
        name="collection_toggle_status",
    ),
    path(
        "mockserver/endpoint/<uuid:pk>/toggle-status/",
        ToggleStatusView.as_view(),
        {"model_class": Endpoint},
        name="endpoint_toggle_status",
    ),
    path(
        "mockserver/endpoint/<uuid:pk>/duplicate/",
        DuplicateEndpointView.as_view(),
        name="endpoint_duplicate",
    ),
]
