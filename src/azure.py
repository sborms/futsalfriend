import os

from dotenv import load_dotenv

from azure.identity import DefaultAzureCredential
from azure.mgmt.resource.resources import ResourceManagementClient


class AzureManager:
    def __init__(self) -> None:
        self.session = AzureManager.authenticate_to_azure()
        print("Successfully authenticated to Azure.")

    def authenticate_to_azure():
        """Authenticates to Azure given credentials stored in a .env file."""
        load_dotenv()

        credential = DefaultAzureCredential()
        print(f"Credential: {credential._successful_credential.__class__.__name__}")

        session = ResourceManagementClient(
            credential=credential, subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID")
        )

        return session
