from azure.storage.blob import BlobServiceClient
import os

def get_blob_url(blob_name):
    container_name = "lab1"  # Der Name deines Containers


    connect_str = os.getenv('connect_str')

    if connect_str is None:
        raise ValueError("Die Umgebungsvariable 'connect_str' wurde nicht gefunden.")
    else:
        print(f"connect_str: {connect_str}")

    container_name = "lab1"

    # Blob-Dienst-Client erstellen
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    # Blob-Client erstellen
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    # URL des Blobs abrufen
    url = blob_client.url
    
    return url