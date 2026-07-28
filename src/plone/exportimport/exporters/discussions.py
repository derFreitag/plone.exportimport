from .base import BaseExporter
from collections.abc import Callable
from pathlib import Path
from plone import api
from plone.exportimport import interfaces
from plone.exportimport import logger
from zope.interface import implementer

import argparse

try:
    import plone.app.discussion  # noqa
except ImportError:
    HAS_DISCUSSION = False
else:
    HAS_DISCUSSION = True


@implementer(interfaces.INamedExporter)
class DiscussionsExporter(BaseExporter):
    name: str = "discussions"
    paths_list: list[str] | None = None

    def export_data(
        self,
        base_path: Path,
        paths_list: list[str] | None = None,
        data_hooks: list[Callable] = None,
        obj_hooks: list[Callable] = None,
        options: argparse.Namespace | None = None,
    ) -> list[Path]:
        """Write data to filesystem.

        When ``paths_list`` is given (a partial export), only discussions of
        the objects at those paths are exported.
        """
        self.paths_list = paths_list
        return super().export_data(base_path, data_hooks, obj_hooks, options=options)

    def _exported_uids(self) -> set[str]:
        """Return the UIDs of the objects at ``self.paths_list``."""
        catalog = api.portal.get_tool("portal_catalog")
        brains = catalog.unrestrictedSearchResults(
            path={"query": list(self.paths_list), "depth": 0}
        )
        return {brain.UID for brain in brains}

    def dump(self) -> list[Path]:
        """Serialize object and dump it to disk."""
        if not HAS_DISCUSSION:
            logger.debug("- Discussions: Skipping (plone.app.discussion not installed)")
            return []

        from plone.exportimport.utils import discussions as utils

        uids = self._exported_uids() if self.paths_list else None
        discussions = utils.get_discussions(uids=uids)
        filepath = self._dump(discussions, self.filepath)
        logger.debug(
            f"- Discussions: Wrote {len(discussions)} discussions to {filepath}"
        )
        return [filepath]
