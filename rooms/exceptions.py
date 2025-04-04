class RoomManagerError(Exception):
    """Excepción personalizada para errores relacionados con el Room Manager."""
    def __init__(self, message="Error en el Room Manager"):
        self.message = message
        super().__init__(self.message)
