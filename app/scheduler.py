"""Independent periodic jobs. One upstream delay must not stall the other jobs."""

import asyncio

from .integrations.caldav import CALENDAR_SYNC_INTERVAL
from .integrations.common import log_failure
from .services.planner import catch_up


async def repeat(job, interval=CALENDAR_SYNC_INTERVAL):
    while True:
        try:
            await asyncio.to_thread(job)
        except Exception as error:
            log_failure("Background job", error)
        await asyncio.sleep(interval)


def start(runtime):
    def planner():
        with runtime.database.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            catch_up(db)

    return [
        asyncio.create_task(repeat(job))
        for job in (planner, runtime.calendars.sync, runtime.photos.sync)
    ]


async def stop(tasks):
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
