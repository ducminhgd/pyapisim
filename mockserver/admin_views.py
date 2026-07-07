from __future__ import annotations

from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from mockserver.forms import DuplicateCollectionForm, DuplicateEndpointForm
from mockserver.models import Collection, Endpoint


@method_decorator(staff_member_required, name="dispatch")
class DuplicateCollectionView(View):
    """Admin view that renders a pre-populated form for duplicating a collection.

    GET  — shows the form with defaults derived from the original collection.
    POST — validates the form, clones the collection (with endpoints & shares),
           and redirects to the new collection's change page.
    """

    template_name = "admin/mockserver/collection/duplicate.html"

    def _get_original(self, pk: str) -> Collection:
        return get_object_or_404(Collection, pk=pk)

    def _check_permission(self, original: Collection, request: HttpRequest) -> bool:
        """Return True if *request.user* may duplicate *original*."""
        if request.user.is_superuser:
            return True
        return original.user_can_view(request.user)

    def get(self, request: HttpRequest, pk: str) -> HttpResponse:
        original = self._get_original(pk)
        if not self._check_permission(original, request):
            return HttpResponseForbidden("You do not have permission to duplicate this collection.")

        form = DuplicateCollectionForm(original=original)

        context = {
            **admin.site.each_context(request),
            "title": f"Duplicate {original.name}",
            "original": original,
            "form": form,
            "endpoint_count": original.endpoints.count(),
            "share_count": original.shared_collections.count(),
            "opts": Collection._meta,
            "is_popup": False,
            "save_as": False,
            "has_permission": True,
            "has_view_permission": True,
        }
        return render(request, self.template_name, context)

    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        original = self._get_original(pk)
        if not self._check_permission(original, request):
            return HttpResponseForbidden("You do not have permission to duplicate this collection.")

        form = DuplicateCollectionForm(request.POST, original=original)
        if form.is_valid():
            username = request.user.get_username()
            new_collection = original.duplicate(
                new_code=form.cleaned_data["code"],
                new_name=form.cleaned_data["name"],
                created_by=username,
            )
            messages.success(request, f'Collection "{new_collection.name}" created successfully.')
            change_url = reverse("admin:mockserver_collection_change", args=[new_collection.pk])
            return redirect(change_url)

        # Re-render with errors.
        context = {
            **admin.site.each_context(request),
            "title": f"Duplicate {original.name}",
            "original": original,
            "form": form,
            "endpoint_count": original.endpoints.count(),
            "share_count": original.shared_collections.count(),
            "opts": Collection._meta,
            "is_popup": False,
            "save_as": False,
            "has_permission": True,
            "has_view_permission": True,
        }
        return render(request, self.template_name, context)


@method_decorator(staff_member_required, name="dispatch")
class ToggleStatusView(View):
    """Toggle the status of a Collection or Endpoint between ACTIVE and INACTIVE."""

    def _check_permission(self, obj, request: HttpRequest) -> bool:
        """Return True if *request.user* may toggle the status of *obj*."""
        if request.user.is_superuser:
            return True
        if isinstance(obj, Collection):
            return obj.user_can_edit(request.user)
        if isinstance(obj, Endpoint):
            collection = obj.collection
            return collection is not None and collection.user_can_edit(request.user)
        return False

    def _get_changelist_url(self, model_class) -> str:
        opts = model_class._meta
        return reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist")

    def get(self, request: HttpRequest, pk: str, model_class) -> HttpResponse:
        obj = get_object_or_404(model_class, pk=pk)
        if not self._check_permission(obj, request):
            return HttpResponseForbidden("You do not have permission to toggle this item.")

        # Toggle status.
        new_status = (
            model_class.Status.INACTIVE if obj.status == model_class.Status.ACTIVE
            else model_class.Status.ACTIVE
        )
        obj.status = new_status
        obj.save(update_fields=["status"])

        verb = "deactivated" if new_status == model_class.Status.INACTIVE else "activated"
        messages.success(request, f'"{obj}" has been {verb}.')

        # Redirect back to the changelist.
        return redirect(self._get_changelist_url(model_class))


@method_decorator(staff_member_required, name="dispatch")
class DuplicateEndpointView(View):
    """Admin view that renders a pre-populated form for duplicating an endpoint.

    GET  — shows the form with defaults derived from the original endpoint.
    POST — validates the form, creates a new endpoint, and redirects to its
           change page.
    """

    template_name = "admin/mockserver/endpoint/duplicate.html"

    def _get_original(self, pk: str) -> Endpoint:
        return get_object_or_404(Endpoint.objects.select_related("collection"), pk=pk)

    def _check_permission(self, original: Endpoint, request: HttpRequest) -> bool:
        """Return True if *request.user* may duplicate *original*."""
        if request.user.is_superuser:
            return True
        collection = original.collection
        return collection is not None and collection.user_can_view(request.user)

    def _filter_collection_queryset(self, form: DuplicateEndpointForm, request: HttpRequest) -> None:
        """Restrict the *collection* dropdown to collections the user can edit."""
        from django.db import models

        from mockserver.models import SharedCollection as _SC

        if request.user.is_superuser:
            form.fields["collection"].queryset = Collection.objects.all()
        else:
            form.fields["collection"].queryset = Collection.objects.filter(
                models.Q(created_by=request.user.get_username())
                | models.Q(
                    id__in=request.user.shared_collections.filter(
                        role=_SC.Role.EDITOR,
                    ).values("collection_id")
                ),
            )

    def get(self, request: HttpRequest, pk: str) -> HttpResponse:
        original = self._get_original(pk)
        if not self._check_permission(original, request):
            return HttpResponseForbidden("You do not have permission to duplicate this endpoint.")

        form = DuplicateEndpointForm(original=original)
        self._filter_collection_queryset(form, request)

        context = {
            **admin.site.each_context(request),
            "title": f"Duplicate {original.name}",
            "original": original,
            "form": form,
            "opts": Endpoint._meta,
            "is_popup": False,
            "save_as": False,
            "has_permission": True,
            "has_view_permission": True,
        }
        return render(request, self.template_name, context)

    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        original = self._get_original(pk)
        if not self._check_permission(original, request):
            return HttpResponseForbidden("You do not have permission to duplicate this endpoint.")

        form = DuplicateEndpointForm(request.POST, original=original)
        self._filter_collection_queryset(form, request)
        if form.is_valid():
            username = request.user.get_username()
            new_ep = form.save(commit=False)
            new_ep.created_by = username
            new_ep.updated_by = username
            new_ep.save()
            messages.success(request, f'Endpoint "{new_ep.name}" created successfully.')
            change_url = reverse("admin:mockserver_endpoint_change", args=[new_ep.pk])
            return redirect(change_url)

        # Re-render with errors.
        context = {
            **admin.site.each_context(request),
            "title": f"Duplicate {original.name}",
            "original": original,
            "form": form,
            "opts": Endpoint._meta,
            "is_popup": False,
            "save_as": False,
            "has_permission": True,
            "has_view_permission": True,
        }
        return render(request, self.template_name, context)
