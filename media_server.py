#!/usr/bin/env python3
"""
Media Server for Termux
Serves files from the /media directory over HTTP with CORS support
Optimized for Android/Termux environment
"""

import os
import sys
import logging
import argparse
import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
import mimetypes

class CORSRequestHandler(SimpleHTTPRequestHandler):
    """Custom request handler with CORS support and logging"""

    def __init__(self, *args, directory=None, **kwargs):
        if directory is None:
            directory = os.getcwd()
        super().__init__(*args, directory=directory, **kwargs)

    def end_headers(self):
        """Add CORS headers to all responses"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        """Handle file uploads"""
        try:
            # Handle both multipart form data and direct file uploads
            content_type = self.headers.get('Content-Type', '')

            # Read body first for all POST requests
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)

            if 'multipart/form-data' in content_type:
                # Handle Django's multipart upload
                filename, file_content = self._parse_multipart_form_data(body, content_type)
            else:
                # Fallback to Content-Disposition header
                content_disposition = self.headers.get('Content-Disposition', '')
                if 'filename=' not in content_disposition:
                    self.send_error(400, "No filename in Content-Disposition")
                    return
                filename = content_disposition.split('filename=')[1].strip('"')
                file_content = body

            if not filename:
                self.send_error(400, "No filename")
                return

            # Allow subdirectories
            if '..' in filename or filename.startswith('/'):
                self.send_error(400, "Invalid filename")
                return

            # Create directories if needed
            filepath = os.path.join(self.directory, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Save the file
            with open(filepath, 'wb') as f:
                f.write(file_content)

            logger.info(f"File uploaded successfully: {filename}")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "success", "filename": "' + filename.encode() + b'"}')

        except Exception as e:
            logger.error(f"Upload error: {e}")
            self.send_error(500, f"Upload failed: {str(e)}")

    def _parse_multipart_form_data(self, body, content_type):
        """Parse multipart form data to extract filename and file content"""
        try:
            body_str = body.decode('latin-1')

            # Find the boundary
            if 'boundary=' in content_type:
                boundary = content_type.split('boundary=')[1]
                parts = body_str.split(f'--{boundary}')

                for part in parts:
                    if 'filename=' in part:
                        # Extract filename from Content-Disposition
                        lines = part.split('\r\n')
                        filename = None
                        for line in lines:
                            if line.startswith('Content-Disposition:') and 'filename=' in line:
                                filename_part = line.split('filename=')[1].strip('"')
                                filename = filename_part
                                break

                        if filename:
                            # Find the actual file content (after headers)
                            content_start = part.find('\r\n\r\n')
                            if content_start != -1:
                                file_content = part[content_start + 4:].encode('latin-1')
                                # Remove trailing \r\n if present
                                if file_content.endswith(b'\r\n'):
                                    file_content = file_content[:-2]
                                return filename, file_content

            # Fallback: no filename found
            return None, body
        except Exception as e:
            logger.warning(f"Failed to parse multipart data: {e}")
            return None, body

    def log_message(self, format, *args):
        """Override logging to use our custom logger"""
        logger.info(f"{self.address_string()} - {format % args}")

    def translate_path(self, path):
        """Translate URL path to filesystem path, handling media directory"""
        path = super().translate_path(path)
        # Ensure we're serving from the media directory
        if not path.startswith(self.directory):
            return os.path.join(self.directory, 'index.html')  # Fallback
        return path

def get_local_ip():
    """Get the local IP address of the machine"""
    try:
        # Create a socket to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        logger.warning(f"Could not determine local IP: {e}")
        return "127.0.0.1"

def setup_logging(log_level=logging.INFO):
    """Setup logging configuration"""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Media Server for Termux')
    parser.add_argument('--host', default='192.168.18.46',
                       help='Host IP address (default: 192.168.18.46)')
    parser.add_argument('--port', type=int, default=8000,
                       help='Port number (default: 8000)')
    parser.add_argument('--directory', default='./media',
                       help='Directory to serve (default: ./media)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level (default: INFO)')

    args = parser.parse_args()

    # Setup logging
    global logger
    logger = setup_logging(getattr(logging, args.log_level))

    # Ensure media directory exists
    if not os.path.exists(args.directory):
        logger.error(f"Media directory '{args.directory}' does not exist")
        sys.exit(1)

    # Change to media directory
    os.chdir(args.directory)

    # Create server
    try:
        server_address = (args.host, args.port)
        httpd = HTTPServer(server_address, CORSRequestHandler)

        local_ip = get_local_ip()
        logger.info("Media Server starting...")
        logger.info(f"Serving directory: {os.getcwd()}")
        logger.info(f"Server URL: http://{args.host}:{args.port}/")
        logger.info(f"Local access: http://{local_ip}:{args.port}/")
        logger.info("Press Ctrl+C to stop the server")

        # Start server
        httpd.serve_forever()

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            logger.error(f"Port {args.port} is already in use. Try a different port with --port")
        elif e.errno == 99 or e.errno == 10049:  # Cannot assign requested address
            logger.error(f"Cannot bind to {args.host}:{args.port}. The IP address may not be available.")
            local_ip = get_local_ip()
            logger.info(f"Try using your local IP: {local_ip}")
            logger.info(f"Example: python media_server.py --host {local_ip}")
            logger.info("Or use 0.0.0.0 to bind to all interfaces:")
            logger.info("Example: python media_server.py --host 0.0.0.0")
        else:
            logger.error(f"Server error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()