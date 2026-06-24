from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.db import models
from django.forms import CheckboxSelectMultiple, ModelForm, MultipleChoiceField
from django.utils.html import format_html
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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "shared_with":
            kwargs["queryset"] = db_field.remote_field.model._default_manager.exclude(id=request.user.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Collection)
class CollectionAdmin(AuditModelAdmin):
    inlines = [SharedCollectionInline]
    list_display = ("code", "name", "status", "visibility", "created_by")

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
        return obj.is_owner(request.user)


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
    list_display = ("collection", "name", "full_path", "status", "created_by")

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
        collection = obj.collection
        return collection is not None and collection.is_owner(request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "collection":
            if request.user.is_superuser:
                kwargs["queryset"] = Collection.objects.all()
            else:
                kwargs["queryset"] = Collection.objects.filter(
                    models.Q(created_by=request.user.get_username())
                    | models.Q(id__in=request.user.shared_collections.filter(
                        role=SharedCollection.Role.EDITOR,
                    ).values("collection_id")),
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description="Path")
    def full_path(self, obj):
        collection_code = obj.collection.code if obj.collection else "—"
        base_url = f"{self.request.scheme}://{self.request.get_host()}"
        url = f"{base_url}/mockapi/{collection_code}/{obj.path}" if obj.collection else obj.path
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)


# @admin.register(SharedCollection)
# class SharedCollectionAdmin(ModelAdmin):
#     pass
