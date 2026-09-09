"""The header of an archive: version, count and digest."""

import hashlib
import json

from depot.errors import ArchiveError

FORMAT_VERSION = 1


def digest_of(frames):
    """A stable digest over the encoded entries.

    The frames are re-serialised with sorted keys so the digest depends
    on the content and not on the order a dictionary happened to be
    built in.
    """
    canonical = json.dumps(frames, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_manifest(frames):
    return {
        "version": FORMAT_VERSION,
        "count": len(frames),
        "digest": digest_of(frames),
    }


def check_manifest(manifest, frames):
    """Raise unless ``manifest`` describes ``frames``."""
    if not isinstance(manifest, dict):
        raise ArchiveError("an archive needs a manifest")
    version = manifest.get("version")
    if version != FORMAT_VERSION:
        raise ArchiveError("unsupported archive version %r" % (version,))
    if manifest.get("count") != len(frames):
        raise ArchiveError(
            "archive says %r entries but carries %d" % (manifest.get("count"), len(frames))
        )
    if manifest.get("digest") != digest_of(frames):
        raise ArchiveError("archive digest does not match its entries")
    return manifest


def describe(manifest):
    """A one-line summary for logs and error messages."""
    return "archive v%s, %s entry(s)" % (manifest.get("version", "?"), manifest.get("count", "?"))
