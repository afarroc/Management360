import requests
from django.core.files.storage import Storage
from django.conf import settings
import os

print("=== REMOTE MEDIA STORAGE MODULE LOADED ===")

class RemoteMediaStorage(Storage):
    def __init__(self):
        print("=== REMOTE MEDIA STORAGE INITIALIZED ===")
        print(f"MEDIA_URL from settings: {settings.MEDIA_URL}")
        self.server_url = settings.MEDIA_URL.rstrip('/')
        print(f"Server URL set to: {self.server_url}")
        self.upload_url = self.server_url  # Upload to root endpoint
        print(f"Upload URL set to: {self.upload_url}")
        print("=== STORAGE INITIALIZATION COMPLETE ===")

    def _save(self, name, content):
        print("=== STORAGE _SAVE METHOD CALLED ===")
        print(f"File name to save: {name}")
        print(f"Server URL: {self.server_url}")
        print(f"Upload URL: {self.upload_url}")

        # Validate name
        if not name or name is None:
            print("ERROR: File name is None or empty, cannot upload")
            raise Exception("Upload failed: No filename provided")

        # Get file content
        print("Reading file content...")
        if hasattr(content, 'read'):
            print("Content has read method, reading data...")
            file_data = content.read()
            print(f"Read {len(file_data)} bytes from content")
            if hasattr(content, 'seek'):
                print("Resetting content position to 0")
                content.seek(0)  # Reset for potential reuse
        else:
            print("Content is raw data")
            file_data = content

        # Ensure file_data is bytes
        if isinstance(file_data, str):
            print("Converting string data to bytes")
            file_data = file_data.encode('utf-8')

        print(f"Final file data type: {type(file_data)}, size: {len(file_data)} bytes")
        print("=== CONTENT PROCESSING COMPLETE ===")

        # Create multipart form data manually with proper Content-Disposition
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body_parts = []

        # Add file part with proper Content-Disposition header
        body_parts.append(f'--{boundary}'.encode('utf-8'))
        body_parts.append(f'Content-Disposition: form-data; name="file"; filename="{name}"'.encode('utf-8'))
        body_parts.append('Content-Type: application/octet-stream'.encode('utf-8'))
        body_parts.append(''.encode('utf-8'))
        body_parts.append(file_data)  # Keep as bytes
        body_parts.append(f'--{boundary}--'.encode('utf-8'))
        body_parts.append(''.encode('utf-8'))

        # Join with CRLF
        body = b'\r\n'.join(body_parts)

        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Content-Length': str(len(body))
        }

        print("=== PREPARING HTTP REQUEST ===")
        print(f"Sending POST request to: {self.upload_url}")
        print(f"Headers: {headers}")
        print(f"Body size: {len(body)} bytes")
        print(f"Boundary: ----WebKitFormBoundary7MA4YWxkTrZu0gW")

        print("=== SENDING REQUEST ===")
        try:
            response = requests.post(self.upload_url, data=body, headers=headers, timeout=10)
            print("=== RESPONSE RECEIVED ===")
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response text: {response.text}")

            if response.status_code == 200:
                print(f"SUCCESS: File uploaded successfully to remote server: {name}")
                print("=== UPLOAD SUCCESSFUL ===")
                return name
            else:
                print(f"FAILED: Upload failed: {response.status_code} {response.text}")
                print("=== UPLOAD FAILED - FALLING BACK TO LOCAL STORAGE ===")
                # Let Django handle the failure by raising an exception
                # This will cause Django to fall back to local storage
                raise Exception(f"Upload failed: {response.status_code} {response.text}")
        except Exception as e:
            print(f"EXCEPTION: Upload failed: {e}")
            print(f"Exception type: {type(e)}")
            print("=== UPLOAD EXCEPTION - FALLING BACK TO LOCAL STORAGE ===")
            # Let Django handle the exception by re-raising it
            # This will cause Django to fall back to local storage
            raise Exception(f"Upload failed: {str(e)}")

    def _open(self, name, mode='rb'):
        # Download file from remote server
        url = self.url(name)
        response = requests.get(url)
        if response.status_code == 200:
            from io import BytesIO
            return BytesIO(response.content)
        else:
            from django.core.files.base import File
            raise FileNotFoundError(f"File {name} not found on remote server")

    def exists(self, name):
        url = self.url(name)
        response = requests.head(url)
        return response.status_code == 200

    def url(self, name):
        return f"{self.server_url}/{name}"

    def delete(self, name):
        # For now, just return True, as deleting from remote might not be implemented
        # Could implement DELETE request if server supports it
        pass

    def size(self, name):
        url = self.url(name)
        response = requests.head(url)
        if response.status_code == 200:
            return int(response.headers.get('content-length', 0))
        return 0