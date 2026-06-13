class AppException(Exception):
    status_code: int = 500
    default_detail: str = "Internal server error"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.default_detail)
        self.detail = detail or self.default_detail


class InvalidUploadError(AppException):
    status_code = 400
    default_detail = "Invalid upload"


class UnsupportedFormatError(AppException):
    status_code = 415
    default_detail = "Unsupported audio format"


class FileTooLargeError(AppException):
    status_code = 413
    default_detail = "File too large"


class JobNotFoundError(AppException):
    status_code = 404
    default_detail = "Job not found"


class TranscriptionError(AppException):
    status_code = 500
    default_detail = "Transcription failed"
