from django.contrib import admin
from unfold.admin import ModelAdmin
from mockserver.models import Collection, Endpoint, SharedCollection


class AuditModelAdmin(ModelAdmin):
    exclude = ("created_by", "updated_by")

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


@admin.register(Collection)
class CollectionAdmin(AuditModelAdmin):
    pass

@admin.register(Endpoint)
class EndpointAdmin(AuditModelAdmin):
    pass

@admin.register(SharedCollection)
class SharedCollectionAdmin(ModelAdmin):
    pass