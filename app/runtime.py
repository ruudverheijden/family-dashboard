"""Instance-owned dependencies; no shared sessions, cache or scheduler state."""

from .auth import Authentication
from .db import Database
from .integrations.caldav import CalendarSync
from .integrations.immich import PhotoLibrary


class Runtime:
    def __init__(self, config):
        self.database = Database(config.data_dir)
        self.auth = Authentication(self.database, config.admin_password, config.cookie_secure)
        self.calendars = CalendarSync(self.database)
        self.photos = PhotoLibrary(self.database, config.cache_dir, config.cache_limit)
