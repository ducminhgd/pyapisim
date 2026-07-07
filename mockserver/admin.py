from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.db import models
from django.forms import CheckboxSelectMultiple, ModelForm, MultipleChoiceField
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin, TabularInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from mockserver.models import Collection, Endpoint, SharedCollection

admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Forms loaded from `unfold.forms`
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


class AuditModelAdmin(ModelAdmin):
    exclude = ("created_by", "updated_by")
    warn_unsaved_form = True

    def save_model(self, request, obj, form, change):
        username = request.user.get_username() if request.user.is_authenticated else "anonymous"
        if not change:
            obj.created_by = username
        obj.updated_by = username
        super().save_model(request, obj, form, change)


class SharedCollectionInline(TabularInline):
    model = SharedCollection
    extra = 0  # number of inline placeholders to display
    fields = ("shared_with", "role")
    autocomplete_fields = ("shared_with",)

    def has_add_permission(self, request, obj):
        """Allow adding shares if the user can edit the parent collection."""
        if obj is None:
            return True
        return obj.user_can_edit(request.user)

    def has_change_permission(self, request, obj=None):
        """Allow changing shares if the user can edit the parent collection."""
        if obj is None:
            return True
        return obj.user_can_edit(request.user)

    def has_delete_permission(self, request, obj=None):
        """Allow deleting shares if the user can edit the parent collection."""
        if obj is None:
            return True
        return obj.user_can_edit(request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "shared_with":
            kwargs["queryset"] = db_field.remote_field.model._default_manager.exclude(id=request.user.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Collection)
class CollectionAdmin(AuditModelAdmin):
    change_form_template = "admin/mockserver/collection/change_form.html"
    delete_confirmation_template = "admin/mockserver/collection/delete_confirmation.html"
    inlines = [SharedCollectionInline]
    list_display = ("code", "name", "status", "visibility", "created_by", "row_actions")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(
            models.Q(created_by=request.user.get_username())
            | models.Q(visibility=Collection.Visibility.PUBLIC)
            | models.Q(id__in=request.user.shared_collections.values("collection_id")),
        )

    def has_view_permission(self, request, obj=None):
        if obj is None:
            return True
        return obj.user_can_view(request.user)

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        return obj.user_can_edit(request.user)

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        if request.user.is_superuser:
            return True
        return obj.is_owner(request.user)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj is not None and obj.user_can_view(request.user):
            extra_context["duplicate_url"] = reverse("mockserver:collection_duplicate", args=[obj.pk])
        return super().change_view(request, object_id, form_url, extra_context)

    def delete_view(self, request, object_id, extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj is not None:
            extra_context["endpoint_count"] = obj.endpoints.count()
            extra_context["share_count"] = obj.shared_collections.count()
        return super().delete_view(request, object_id, extra_context)

    @admin.display(description="Actions")
    def row_actions(self, obj):
        actions = []
        request = getattr(self, "request", None)
        if request is None:
            return "—"

        # Duplicate action — visible to anyone who can view.
        if obj.user_can_view(request.user):
            dup_url = reverse("mockserver:collection_duplicate", args=[obj.pk])
            actions.append(
                format_html(
                    '<a href="{}" title="{}" class="inline-flex items-center p-1.5 rounded border'
                    " border-base-200 dark:border-base-700 text-important hover:bg-base-100"
                    ' dark:hover:bg-base-800 cursor-pointer">'
                    '<span class="material-symbols-outlined text-base">content_copy</span></a>',
                    dup_url,
                    "Duplicate",
                )
            )

        # Toggle active/inactive — visible to editors.
        if obj.user_can_edit(request.user):
            toggle_url = reverse("mockserver:collection_toggle_status", args=[obj.pk])
            is_active = obj.status == Collection.Status.ACTIVE
            icon = "toggle_off" if is_active else "toggle_on"
            title = "Deactivate" if is_active else "Activate"
            actions.append(
                format_html(
                    '<a href="{}" title="{}" class="inline-flex items-center p-1.5 rounded border'
                    " border-base-200 dark:border-base-700 text-important hover:bg-base-100"
                    ' dark:hover:bg-base-800 cursor-pointer">'
                    '<span class="material-symbols-outlined text-base">{}</span></a>',
                    toggle_url,
                    title,
                    icon,
                )
            )

        # Delete — visible only to the owner.
        if obj.is_owner(request.user):
            delete_url = reverse("admin:mockserver_collection_delete", args=[obj.pk])
            actions.append(
                format_html(
                    '<a href="{}" title="{}" class="inline-flex items-center p-1.5 rounded border'
                    " border-base-200 dark:border-base-700 text-important hover:bg-base-100"
                    ' dark:hover:bg-base-800 cursor-pointer">'
                    '<span class="material-symbols-outlined text-base">delete</span></a>',
                    delete_url,
                    "Delete",
                )
            )

        return format_html('<div class="flex gap-1">{}</div>', mark_safe("".join(actions)))


admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    search_fields = ("username", "email", "first_name", "last_name")

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        # Exclude the current user from autocomplete results
        # (e.g. when sharing a collection, you can't share with yourself)
        if "app_label" in request.GET and "model_name" in request.GET:
            queryset = queryset.exclude(id=request.user.id)
        return queryset, use_distinct


HTTP_METHOD_CHOICES = [
    ("GET", "GET"),
    ("POST", "POST"),
    ("PUT", "PUT"),
    ("PATCH", "PATCH"),
    ("DELETE", "DELETE"),
    ("HEAD", "HEAD"),
    ("OPTIONS", "OPTIONS"),
]


class EndpointAdminForm(ModelForm):
    allowed_methods = MultipleChoiceField(
        choices=HTTP_METHOD_CHOICES,
        widget=CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Endpoint
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial["allowed_methods"] = self.instance.allowed_methods or []

    def clean_allowed_methods(self) -> list[str]:
        return self.cleaned_data.get("allowed_methods", [])


@admin.register(Endpoint)
class EndpointAdmin(AuditModelAdmin):
    form = EndpointAdminForm
    change_form_template = "admin/mockserver/endpoint/change_form.html"
    list_display = ("collection", "name", "full_path", "status", "created_by", "row_actions")

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("collection")
        if request.user.is_superuser:
            return qs
        return qs.filter(
            models.Q(collection__created_by=request.user.get_username())
            | models.Q(collection__visibility=Collection.Visibility.PUBLIC)
            | models.Q(collection__id__in=request.user.shared_collections.values("collection_id")),
        )

    def has_view_permission(self, request, obj=None):
        if obj is None:
            return True
        collection = obj.collection
        return collection is not None and collection.user_can_view(request.user)

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        collection = obj.collection
        return collection is not None and collection.user_can_edit(request.user)

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        if request.user.is_superuser:
            return True
        collection = obj.collection
        return collection is not None and collection.is_owner(request.user)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj is not None and obj.collection is not None:
            collection = obj.collection
            if collection.user_can_view(request.user):
                extra_context["duplicate_url"] = reverse("mockserver:endpoint_duplicate", args=[obj.pk])
        return super().change_view(request, object_id, form_url, extra_context)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "collection":
            if request.user.is_superuser:
                kwargs["queryset"] = Collection.objects.all()
            else:
                kwargs["queryset"] = Collection.objects.filter(
                    models.Q(created_by=request.user.get_username())
                    | models.Q(
                        id__in=request.user.shared_collections.filter(
                            role=SharedCollection.Role.EDITOR,
                        ).values("collection_id")
                    ),
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description="Path")
    def full_path(self, obj):
        collection_code = obj.collection.code if obj.collection else "—"
        base_url = f"{self.request.scheme}://{self.request.get_host()}"
        url = f"{base_url}/mockapi/{collection_code}/{obj.path}" if obj.collection else obj.path
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)

    @admin.display(description="Actions")
    def row_actions(self, obj):
        actions = []
        request = getattr(self, "request", None)
        if request is None:
            return "—"

        collection = obj.collection

        # Duplicate — visible to anyone who can view the parent collection.
        if collection is not None and collection.user_can_view(request.user):
            dup_url = reverse("mockserver:endpoint_duplicate", args=[obj.pk])
            actions.append(
                format_html(
                    '<a href="{}" title="{}" class="inline-flex items-center p-1.5 rounded border'
                    " border-base-200 dark:border-base-700 text-important hover:bg-base-100"
                    ' dark:hover:bg-base-800 cursor-pointer">'
                    '<span class="material-symbols-outlined text-base">content_copy</span></a>',
                    dup_url,
                    "Duplicate",
                )
            )

        # Toggle active/inactive — visible to editors of the parent collection.
        if collection is not None and collection.user_can_edit(request.user):
            toggle_url = reverse("mockserver:endpoint_toggle_status", args=[obj.pk])
            is_active = obj.status == Endpoint.Status.ACTIVE
            icon = "toggle_off" if is_active else "toggle_on"
            title = "Deactivate" if is_active else "Activate"
            actions.append(
                format_html(
                    '<a href="{}" title="{}" class="inline-flex items-center p-1.5 rounded border'
                    " border-base-200 dark:border-base-700 text-important hover:bg-base-100"
                    ' dark:hover:bg-base-800 cursor-pointer">'
                    '<span class="material-symbols-outlined text-base">{}</span></a>',
                    toggle_url,
                    title,
                    icon,
                )
            )

        # Delete — visible only to the owner of the parent collection.
        if collection is not None and collection.is_owner(request.user):
            delete_url = reverse("admin:mockserver_endpoint_delete", args=[obj.pk])
            actions.append(
                format_html(
                    '<a href="{}" title="{}" class="inline-flex items-center p-1.5 rounded border'
                    " border-base-200 dark:border-base-700 text-important hover:bg-base-100"
                    ' dark:hover:bg-base-800 cursor-pointer">'
                    '<span class="material-symbols-outlined text-base">delete</span></a>',
                    delete_url,
                    "Delete",
                )
            )

        return format_html('<div class="flex gap-1">{}</div>', mark_safe("".join(actions)))


# @admin.register(SharedCollection)
# class SharedCollectionAdmin(ModelAdmin):
#     pass
