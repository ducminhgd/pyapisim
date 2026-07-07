from __future__ import annotations

import json
import uuid

from django import forms
from django.forms import CheckboxSelectMultiple, MultipleChoiceField
from unfold.widgets import (
    UnfoldAdminSelectWidget,
    UnfoldAdminTextareaWidget,
    UnfoldAdminTextInputWidget,
)

from mockserver.models import Collection, Endpoint


def _generate_unique_code(original_code: str) -> str:
    """Generate a unique code based on *original_code*.

    Appends a short random suffix to avoid collisions. The result is
    guaranteed to be ≤ 50 characters.
    """
    suffix = uuid.uuid4().hex[:6]
    # Reserve room for the hyphen + 6-char suffix.
    max_base = 50 - 1 - 6  # 43
    base = original_code[:max_base] if len(original_code) > max_base else original_code
    return f"{base}-{suffix}"


class DuplicateCollectionForm(forms.ModelForm):
    """Pre-populated form for duplicating a :class:`Collection`.

    On init, pass ``original`` (the source ``Collection``) to seed the
    initial values.  The ``name`` field is suffixed with ``" - Copy"``
    and a fresh unique ``code`` is generated.
    """

    class Meta:
        model = Collection
        fields = ["name", "code", "description", "status", "visibility"]
        widgets = {
            "name": UnfoldAdminTextInputWidget,
            "code": UnfoldAdminTextInputWidget,
            "description": UnfoldAdminTextareaWidget,
            "status": UnfoldAdminSelectWidget,
            "visibility": UnfoldAdminSelectWidget,
        }

    def __init__(self, *args, original: Collection | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if original is not None:
            copy_name = f"{original.name} - Copy"
            # Truncate if it exceeds the model's max_length.
            self.fields["name"].initial = copy_name[: self.fields["name"].max_length or 100]

            self.fields["code"].initial = _generate_unique_code(original.code)
            self.fields["description"].initial = original.description
            self.fields["status"].initial = original.status
            self.fields["visibility"].initial = original.visibility

    def clean_code(self) -> str:
        code = self.cleaned_data["code"]
        if Collection.objects.filter(code=code).exists():
            raise forms.ValidationError(
                f'The code "{code}" is already in use. Please choose a different one.',
                code="unique",
            )
        return code


HTTP_METHOD_CHOICES = [
    ("GET", "GET"),
    ("POST", "POST"),
    ("PUT", "PUT"),
    ("PATCH", "PATCH"),
    ("DELETE", "DELETE"),
    ("HEAD", "HEAD"),
    ("OPTIONS", "OPTIONS"),
]


def _generate_unique_path(original_path: str) -> str:
    """Generate a unique path based on *original_path*.

    Appends a short random suffix to avoid collisions within the same collection.
    The result is guaranteed to be ≤ 200 characters.
    """
    suffix = uuid.uuid4().hex[:6]
    max_base = 200 - 1 - 6  # 193
    base = original_path[:max_base] if len(original_path) > max_base else original_path
    return f"{base}-{suffix}"


class DuplicateEndpointForm(forms.ModelForm):
    """Pre-populated form for duplicating an :class:`Endpoint`.

    On init, pass ``original`` (the source ``Endpoint``) to seed the
    initial values.  The ``name`` and ``path`` fields are suffixed to
    avoid collisions.
    """

    allowed_methods = MultipleChoiceField(
        choices=HTTP_METHOD_CHOICES,
        widget=CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Endpoint
        fields = [
            "collection",
            "name",
            "description",
            "path",
            "http_status_code",
            "response_headers",
            "response_body",
            "delay_ms",
            "status",
        ]
        widgets = {
            "name": UnfoldAdminTextInputWidget,
            "path": UnfoldAdminTextInputWidget,
            "description": UnfoldAdminTextareaWidget,
            "response_headers": UnfoldAdminTextareaWidget,
            "response_body": UnfoldAdminTextareaWidget,
            "http_status_code": UnfoldAdminTextInputWidget,
            "delay_ms": UnfoldAdminTextInputWidget,
            "status": UnfoldAdminSelectWidget,
            "collection": UnfoldAdminSelectWidget,
        }

    def __init__(self, *args, original: Endpoint | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if original is not None:
            copy_name = f"{original.name} - Copy"
            self.fields["name"].initial = copy_name[: self.fields["name"].max_length or 100]

            self.fields["path"].initial = _generate_unique_path(original.path)
            self.fields["description"].initial = original.description
            self.fields["allowed_methods"].initial = original.allowed_methods or []
            self.fields["http_status_code"].initial = original.http_status_code
            self.fields["response_headers"].initial = json.dumps(original.response_headers, indent=2)
            self.fields["response_body"].initial = original.response_body
            self.fields["delay_ms"].initial = original.delay_ms
            self.fields["status"].initial = original.status
            self.fields["collection"].initial = original.collection

    def clean_allowed_methods(self) -> list[str]:
        return self.cleaned_data.get("allowed_methods", [])

    def clean_response_headers(self) -> dict:
        raw = self.cleaned_data.get("response_headers", "{}")
        if isinstance(raw, dict):
            return raw
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise forms.ValidationError("Invalid JSON. Please enter a valid JSON object.")

    def clean(self):
        cleaned_data = super().clean()
        collection = cleaned_data.get("collection")
        path = cleaned_data.get("path")
        if collection and path:
            qs = Endpoint.objects.filter(collection=collection, path=path)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error(
                    "path",
                    forms.ValidationError(
                        f'An endpoint with path "{path}" already exists in this collection.',
                        code="unique",
                    ),
                )
        return cleaned_data
