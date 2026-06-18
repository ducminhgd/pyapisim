from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group
from django.forms import CheckboxSelectMultiple, ModelForm, MultipleChoiceField

from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.admin import ModelAdmin, TabularInline
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
        username = (
            request.user.get_username()
            if request.user.is_authenticated
            else "anonymous"
        )
        if not change:
            obj.created_by = username
        obj.updated_by = username
        super().save_model(request, obj, form, change)


class SharedCollectionInline(TabularInline):
    model = SharedCollection
    extra = 1
    fields = ("shared_with", "role")
    autocomplete_fields = ("shared_with",)

@admin.register(Collection)
class CollectionAdmin(AuditModelAdmin):
    inlines = [SharedCollectionInline]
    list_display = ("code", "name", "status", "visibility", "created_by")

admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    search_fields = ("username", "email", "first_name", "last_name")

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
        self.initial["allowed_methods"] = self.instance.allowed_methods or []

    def clean_allowed_methods(self) -> list[str]:
        return self.cleaned_data.get("allowed_methods", [])

@admin.register(Endpoint)
class EndpointAdmin(AuditModelAdmin):
    form = EndpointAdminForm

# @admin.register(SharedCollection)
# class SharedCollectionAdmin(ModelAdmin):
#     pass
