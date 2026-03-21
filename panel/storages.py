import logging
import os

import requests
from django.core.files.storage import Storage
from django.conf import settings

logger = logging.getLogger(__name__)

logger.debug("RemoteMediaStorage module loaded")


class RemoteMediaStorage(Storage):

    def __init__(self):
        self.server_url = settings.MEDIA_URL.rstrip('/')
        self.upload_url = self.server_url
        logger.debug(
            "RemoteMediaStorage initialized — server_url=%s", self.server_url
        )

    def _save(self, name, content):
        if not name:
            raise Exception("Upload failed: No filename provided")

        # Normalizar separadores para evitar %5C en la URL
        name = name.replace('\\', '/')
        logger.debug("_save called — name=%s upload_url=%s", name, self.upload_url)

        # Leer contenido
        if hasattr(content, 'read'):
            file_data = content.read()
            if hasattr(content, 'seek'):
                content.seek(0)
        else:
            file_data = content

        if isinstance(file_data, str):
            file_data = file_data.encode('utf-8')

        logger.debug("File ready — size=%d bytes", len(file_data))

        # Construir multipart manualmente (servidor legacy sin requests.files)
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body_parts = [
            f'--{boundary}'.encode(),
            f'Content-Disposition: form-data; name="file"; filename="{name}"'.encode(),
            b'Content-Type: application/octet-stream',
            b'',
            file_data,
            f'--{boundary}--'.encode(),
            b'',
        ]
        body = b'\r\n'.join(body_parts)

        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Content-Length': str(len(body)),
        }

        logger.debug("POST %s — body=%d bytes", self.upload_url, len(body))

        try:
            response = requests.post(
                self.upload_url, data=body, headers=headers, timeout=10
            )
            if response.status_code == 200:
                logger.info("Upload OK — %s", name)
                return name
            else:
                logger.warning(
                    "Upload failed — status=%s body=%s",
                    response.status_code,
                    response.text[:200],
                )
                raise Exception(
                    f"Remote upload failed: {response.status_code} - {response.text}"
                )
        except requests.exceptions.RequestException as e:
            logger.error("Network error uploading %s: %s", name, e)
            raise Exception(f"Network error: Could not connect to remote media server - {e}")
        except Exception as e:
            logger.error("Upload exception for %s: %s", name, e)
            raise

    def _open(self, name, mode='rb'):
        from io import BytesIO
        response = requests.get(self.url(name))
        if response.status_code == 200:
            return BytesIO(response.content)
        raise FileNotFoundError(f"File {name} not found on remote server")

    def exists(self, name):
        return requests.head(self.url(name)).status_code == 200

    def url(self, name):
        return f"{self.server_url}/{name}"

    def delete(self, name):
        pass  # No implementado — el servidor remoto no expone DELETE

    def size(self, name):
        response = requests.head(self.url(name))
        if response.status_code == 200:
            return int(response.headers.get('content-length', 0))
        return 0
