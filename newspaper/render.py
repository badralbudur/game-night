"""Turning an edition into something a person reads.

The edition is a structured payload of typed blocks, and this module renders it
to Markdown. Keeping them separate is what makes the redaction and tone checks
in :mod:`newspaper.edition` worth anything: every printed sentence is a leaf of
the payload, so a check that walks the payload has seen the whole paper, and a
check that also reads this module's output has seen it the way a player will.

Markdown, and not HTML, because M5's boundary is the rendered edition and M6
owns hosting. An HTML template that existed here would be a hosting decision
taken in the wrong milestone.
"""

_HEADINGS = {1: "#", 2: "##", 3: "###", 4: "####"}


def block_to_markdown(block):
    kind = block["kind"]
    if kind == "heading":
        return "%s %s" % (_HEADINGS.get(block.get("level", 2), "##"), block["text"])
    if kind == "standfirst":
        return "*%s*" % block["text"]
    if kind == "para":
        return block["text"]
    if kind == "quote":
        return "\n".join("> %s" % line for line in block["text"].splitlines() or [""])
    if kind in ("aside", "note"):
        # An aside is an editorial joke and is dropped when config says the paper
        # is not to be funny; a note is a factual footnote and always prints.
        # They look the same on the page and are deliberately different in kind.
        return "_%s_" % block["text"]
    if kind == "list":
        return "\n".join("- %s" % item for item in block["items"])
    if kind == "table":
        columns = block["columns"]
        lines = [
            "| %s |" % " | ".join(str(column) for column in columns),
            "| %s |" % " | ".join("---" for _ in columns),
        ]
        lines.extend(
            "| %s |" % " | ".join(str(cell) for cell in row) for row in block["rows"]
        )
        return "\n".join(lines)
    raise ValueError("no renderer for block kind %r" % kind)


def department_to_markdown(department):
    parts = ["## %s" % department["title"]]
    parts.extend(block_to_markdown(block) for block in department["blocks"])
    return "\n\n".join(parts)


def to_markdown(edition):
    """One edition, as the paper reads."""
    masthead = [
        "# %s" % edition["publication"],
        "*%s*" % edition["motto"],
        " · ".join(
            [
                "**%s**" % edition["edition_line"],
                edition["dateline"],
                edition["price_line"],
            ]
        ),
        edition["weather_line"],
        "_%s_" % edition["standing_line"],
    ]

    image = edition.get("image") or {}
    if image.get("filename"):
        masthead.append("![%s](%s)" % (image["alt"], image["filename"]))
        masthead.append("*%s*" % image["cutline"])

    parts = ["\n\n".join(masthead), "---"]
    parts.extend(department_to_markdown(department) for department in edition["departments"])
    parts.append(
        "---\n\n_%s. Round %s. Offers for the current notice close %s._"
        % (edition["publication"], edition["round"], edition["closes"])
    )
    return "\n\n".join(parts) + "\n"


def archive_index_to_markdown(archive):
    """A local index of the editions on disk -- the archive M6 will serve (#27)."""
    lines = [
        "# %s" % archive["publication"],
        "*%s*" % archive["motto"],
        "",
        "The complete run of %s, oldest first. Every edition stays here; a new one "
        "never replaces an old one (spec #27)." % archive["game"],
        "",
    ]
    for edition in archive["editions"]:
        image = edition.get("image") or {}
        lines.append(
            "- [%s — %s](round-%02d.md)%s"
            % (
                edition["edition_line"],
                edition["dateline"],
                edition["round"],
                "" if not image.get("filename") else " · [image](%s)" % image["filename"],
            )
        )
    lines.extend(
        [
            "",
            "_Hosting — the unguessable subdomain and the `noindex` header — is M6's."
            " These files are what it will serve._",
        ]
    )
    return "\n".join(lines) + "\n"
