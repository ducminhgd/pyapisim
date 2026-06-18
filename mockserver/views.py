from rest_framework.views import APIView

class RestFulAPIView(APIView):
    """
    Base class for RESTful API views.
    """

    def get(self, request, *args, **kwargs):
        return self.handle_request(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.handle_request(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.handle_request(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.handle_request(request, *args, **kwargs)

    def handle_request(self, request, *args, **kwargs):
        """
        Override this method to handle the request and return a response.
        """
        raise NotImplementedError("Subclasses must implement handle_request method.")