"""Errors from business rules, translated to HTTP by the application boundary."""


class DomainError(Exception):
    def __init__(self, status_code, detail=None, headers=None):
        self.status_code = status_code
        self.detail = detail
        self.headers = headers
        super().__init__(detail)
