import time

from django.views import View
from django.http import HttpResponse
from mockserver.models import Endpoint


class MockAPIView(View):
    """
    Mock API endpoint — returns pre-configured responses from the database.

    Matches the request against a stored Endpoint by collection code + path,
    then replays the configured status code, headers, and body.
    """

    def dispatch(self, request, *args, **kwargs):
        ep = Endpoint.objects.filter(
            collection__code=kwargs["c_code"],
            path=kwargs["ep_path"],
        ).first()

        if not ep or ep.status == Endpoint.Status.INACTIVE:
            return HttpResponse("Endpoint not found", status=404)

        if request.method not in ep.allowed_methods:
            return HttpResponse("Method not allowed", status=405)

        if ep.delay_ms:
            time.sleep(ep.delay_ms / 1000)

        return HttpResponse(
            content=ep.response_body or "",
            status=ep.http_status_code,
            headers=ep.response_headers,
        )
