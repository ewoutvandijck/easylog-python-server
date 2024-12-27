from fastapi.security import HTTPBearer


# Create a custom bearer class that doesn't validate
class OptionalHTTPBearer(HTTPBearer):
    def __init__(self):
        super().__init__(auto_error=False)


# Create the security scheme
optional_bearer_header = OptionalHTTPBearer()
