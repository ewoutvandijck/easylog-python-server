from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
from adobe.pdfservices.operation.pdf_services import PDFServices

from src.settings import settings

credentials = ServicePrincipalCredentials(
    client_id=settings.ADOBE_CLIENT_ID, client_secret=settings.ADOBE_CLIENT_SECRET
)

# Create an instance of PDF Services
adobe_client = PDFServices(credentials=credentials)
