"""Writing editions to disk.

    python3 -m newspaper.publish                  # simulate a game, publish it
    python3 -m newspaper.publish --label my-game  # ... under editions/my-game/

This module stops at the filesystem, deliberately: it writes the run as files a
person can read in the repository. Serving the same editions at the paper's
fixed, unguessable, non-publicly-discoverable URL with the whole archive
browsable (spec #26, #27) is :func:`hosting.build_site`, which renders the same
edition payloads as HTML rather than reading these files -- so neither output is
downstream of the other, and a page is never a parsed Markdown document.

Layout, under ``config.newspaper.output.editions_dir``::

    editions/<label>/index.md          the archive index (spec #27)
    editions/<label>/round-01.md       the edition, as it reads
    editions/<label>/round-01.json     the same edition, structured
    editions/<label>/round-01.svg      that edition's image (spec #29)
    editions/<label>/archive.json      every edition plus the run's provenance

Which of those three per-edition formats are written is
``config.newspaper.output.formats``.
"""

import copy as copy_module
import json
import os
import sys

from engine.config import repo_root
from engine.errors import ConfigError

from .edition import Paper
from .render import archive_index_to_markdown, to_markdown

FORMAT_JSON = "json"
FORMAT_MARKDOWN = "markdown"
FORMAT_IMAGE = "image"
KNOWN_FORMATS = (FORMAT_JSON, FORMAT_MARKDOWN, FORMAT_IMAGE)


def _formats(config):
    formats = config.require("newspaper.output.formats")
    if not isinstance(formats, list) or not formats:
        raise ConfigError(
            "config.newspaper.output.formats must be a non-empty list of %s"
            % list(KNOWN_FORMATS)
        )
    unknown = [name for name in formats if name not in KNOWN_FORMATS]
    if unknown:
        raise ConfigError(
            "config.newspaper.output.formats names %s; known formats are %s"
            % (unknown, list(KNOWN_FORMATS))
        )
    return formats


def without_image_content(edition):
    """The edition, minus the image bytes.

    The JSON artifact records the image's provenance -- modality, provider, the
    whole list of what was considered and why (spec #29) -- and points at the
    file. It does not inline a 30KB SVG into every payload; the picture is next
    to it on disk.
    """
    trimmed = copy_module.deepcopy(edition)
    image = trimmed.get("image")
    if isinstance(image, dict):
        image.pop("content", None)
        image["file"] = image.get("filename")
    return trimmed


def publish_game(engine, label="game", out_dir=None, paper=None):
    """Render and write every edition of ``engine``'s game so far.

    Returns a manifest of what was written -- paths, the image modality actually
    used per edition, and the round each edition covers -- so a caller (or a
    test) can assert on the result without re-reading the files.
    """
    paper = paper or Paper(engine)
    formats = _formats(engine.config)
    # Read whether or not it is used, so that config.json stays the single source
    # for where editions live even when a caller (a test, a facilitator trying
    # something out) points somewhere else for one run.
    configured_dir = engine.config.require_str("newspaper.output.editions_dir")
    root = out_dir or os.path.join(repo_root(), configured_dir, label)
    os.makedirs(root, exist_ok=True)

    archive = paper.archive()
    written = []
    for edition in archive["editions"]:
        stem = "round-%02d" % edition["round"]
        files = {}
        if FORMAT_MARKDOWN in formats:
            files["markdown"] = _write(root, "%s.md" % stem, to_markdown(edition))
        if FORMAT_JSON in formats:
            files["json"] = _write(
                root, "%s.json" % stem,
                json.dumps(without_image_content(edition), indent=2, ensure_ascii=False) + "\n",
            )
        image = edition.get("image") or {}
        if FORMAT_IMAGE in formats and image.get("filename") and image.get("content"):
            files["image"] = _write(root, image["filename"], image["content"])
        written.append(
            {
                "round": edition["round"],
                "files": files,
                "image_modality": (image.get("provenance") or {}).get("modality"),
                "image_provider": (image.get("provenance") or {}).get("provider"),
                "departments": [department["id"] for department in edition["departments"]],
            }
        )

    index = _write(root, "index.md", archive_index_to_markdown(archive))
    archive_json = _write(
        root, "archive.json",
        json.dumps(
            dict(
                archive,
                editions=[without_image_content(e) for e in archive["editions"]],
            ),
            indent=2, ensure_ascii=False,
        ) + "\n",
    )
    return {
        "label": label,
        "directory": root,
        "index": index,
        "archive": archive_json,
        "editions": written,
        "formats": formats,
        "archive_prior_editions": archive["archive_prior_editions"],
    }


def _write(root, name, content):
    path = os.path.join(root, name)
    mode, encoding = ("wb", None) if isinstance(content, bytes) else ("w", "utf-8")
    with open(path, mode, encoding=encoding) as fh:
        fh.write(content)
    return path


def main(argv=None):
    from .sample import sample_game

    argv = list(sys.argv[1:] if argv is None else argv)
    label = "sample-game"
    if "--label" in argv:
        label = argv[argv.index("--label") + 1]
    manifest = publish_game(sample_game(), label=label)
    print("wrote %d editions to %s" % (len(manifest["editions"]), manifest["directory"]))
    for entry in manifest["editions"]:
        print(
            "  round %s -> %s (image: %s via %s)"
            % (
                entry["round"],
                os.path.basename(entry["files"].get("markdown", "-")),
                entry["image_modality"],
                entry["image_provider"],
            )
        )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
