"""The cabinet: records built from blueprints and kept in memory.

    cabinet = Cabinet()
    cabinet.define(task_blueprint)
    task = cabinet.create("task", {"title": "Bleed the radiators"})
    cabinet.append_to(task, "tags", "home")

Records are plain dictionaries with one entry per declared field.  The
cabinet hands out copies, so the only way to change a stored record is
through the cabinet itself.
"""

from .counters import Counters
from .drawer import Cabinet
from .values import copy_record

__all__ = ["Cabinet", "Counters", "copy_record"]
