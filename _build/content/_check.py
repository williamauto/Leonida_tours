#!/usr/bin/env python3
"""Validate content modules against the site content schema.

Usage:  python3 _build/content/_check.py [module.py ...]

Checks each module for:
  * loadable Python with a POSTS (or STATIC) list
  * required keys on every record
  * body blocks that use only known block types and carry the right shape
  * image references that exist in img/ and have an ALT/SIZE entry in data.json
  * duplicate slugs across every module checked
  * FAQ shape (question / answer pairs)
  * a rough word count per record
"""
import ast
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, "..", ".."))
IMG = os.path.join(SITE, "img")
DATA = json.load(open(os.path.join(SITE, "_build", "data.json")))


def load_alt():
    """Pull the ALT dict out of build.py without executing the build."""
    src = open(os.path.join(SITE, "_build", "build.py")).read()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "ALT" for t in node.targets):
            return ast.literal_eval(node.value)
    return {}


BLOCK_KEYS = {"h2", "h3", "p", "ul", "ol", "table", "note", "quote", "image"}
KNOWN_IMAGES = set(load_alt().keys())

REQ = ["slug", "title", "meta", "kicker", "cat", "date", "img", "img_alt",
       "excerpt", "body", "faq"]

errors = []
warnings = []


def err(where, msg):
    errors.append(f"{where}: {msg}")


def warn(where, msg):
    warnings.append(f"{where}: {msg}")


def k_is_heading(b):
    """An h2/h3 block may carry a sibling "id" anchor."""
    return isinstance(b, dict) and set(b.keys()) in ({"h2"}, {"h2", "id"},
                                                      {"h3"}, {"h3", "id"})


def check_body(where, body):
    if not isinstance(body, list) or not body:
        err(where, "body must be a non-empty list")
        return 0
    words = 0
    for i, b in enumerate(body):
        tag = f"{where}.body[{i}]"
        if not isinstance(b, dict):
            err(tag, "block must be a dict")
            continue
        keys = set(b.keys())
        if len(keys) != 1 and not k_is_heading(b):
            err(tag, f"block must have exactly one key, got {sorted(keys)}")
            continue
        k = "h2" if "h2" in b else ("h3" if "h3" in b else next(iter(keys)))
        if k not in BLOCK_KEYS:
            err(tag, f"unknown block type {k!r}")
            continue
        v = b[k]
        if k in ("h2", "h3"):
            if not isinstance(v, str) or not v.strip():
                err(tag, f"{k} must be a non-empty string")
            words += len(v.split())
        elif k == "p":
            if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
                err(tag, "p must be a list of strings")
            else:
                words += sum(len(x.split()) for x in v)
        elif k in ("ul", "ol"):
            if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
                err(tag, f"{k} must be a list of strings")
            else:
                words += sum(len(x.split()) for x in v)
        elif k == "table":
            if not isinstance(v, dict) or "head" not in v or "rows" not in v:
                err(tag, "table needs head and rows")
            else:
                words += len(" ".join(map(str, v["head"])).split())
                for r in v["rows"]:
                    words += len(" ".join(map(str, r)).split())
        elif k == "note":
            if not isinstance(v, dict) or "title" not in v or "text" not in v:
                err(tag, "note needs title and text")
            else:
                words += len(v["title"].split()) + len(v["text"].split())
        elif k == "quote":
            if not isinstance(v, dict) or "text" not in v:
                err(tag, "quote needs text")
            else:
                words += len(str(v["text"]).split())
        elif k == "image":
            if not isinstance(v, dict) or "img" not in v or "alt" not in v:
                err(tag, "image needs img and alt")
            else:
                check_image(tag, v["img"])
    return words


def check_image(where, name):
    if not isinstance(name, str):
        err(where, "image name must be a string")
        return
    if name not in KNOWN_IMAGES:
        err(where, f"image {name!r} has no ALT/SIZE entry in data.json")
        return
    for ext in (".jpg", ".png", ".jpeg", ".webp"):
        if os.path.exists(os.path.join(IMG, name + ext)):
            return
    err(where, f"image file img/{name}.jpg not found")


def check_faq(where, faq):
    if not isinstance(faq, list) or not faq:
        err(where, "faq must be a non-empty list")
        return
    for i, pair in enumerate(faq):
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            err(f"{where}.faq[{i}]", "each faq entry must be [question, answer]")
            continue
        if not all(isinstance(x, str) and x.strip() for x in pair):
            err(f"{where}.faq[{i}]", "question and answer must be non-empty strings")


def check_record(where, r, seen_slugs):
    if not isinstance(r, dict):
        err(where, "record must be a dict")
        return
    for k in REQ:
        if k not in r:
            err(where, f"missing required key {k!r}")
    slug = r.get("slug")
    if not isinstance(slug, str) or not re.match(r"^[a-z0-9-]+$", slug):
        err(where, f"bad slug {slug!r}")
    else:
        if slug in seen_slugs:
            err(where, f"duplicate slug {slug!r}")
        seen_slugs.add(slug)
    t = r.get("title")
    if isinstance(t, str):
        if not (20 <= len(t) <= 120):
            warn(where, f"title length {len(t)} outside 20-120")
        if t != t.strip():
            err(where, "title has leading/trailing whitespace")
    m = r.get("meta")
    if isinstance(m, str) and not (70 <= len(m) <= 175):
        warn(where, f"meta length {len(m)} outside 70-175")
    d = r.get("date")
    if isinstance(d, str) and not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
        err(where, f"date must be YYYY-MM-DD, got {d!r}")
    if "img" in r:
        check_image(where, r["img"])
    if "img_alt" in r and (not isinstance(r["img_alt"], str) or len(r["img_alt"]) < 8):
        err(where, "img_alt must be a descriptive string")
    if "body" in r:
        w = check_body(where, r["body"])
        if w < 600:
            warn(where, f"body is only ~{w} words (target 600+)")
    if "faq" in r:
        check_faq(where, r["faq"])


def load(path):
    name = "c_" + re.sub(r"\W", "_", os.path.basename(path))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    paths = sys.argv[1:]
    if not paths:
        paths = sorted(os.path.join(HERE, f) for f in os.listdir(HERE)
                       if re.match(r"^(posts|static|pages)_.*\.py$", f))
    seen = set()
    total = 0
    for path in paths:
        base = os.path.basename(path)
        try:
            mod = load(path)
        except Exception as exc:
            err(base, f"import failed: {exc}")
            continue
        recs = getattr(mod, "POSTS", None) or getattr(mod, "STATIC", None)
        if recs is None:
            err(base, "module has no POSTS or STATIC list")
            continue
        for r in recs:
            check_record(base + ":" + str(r.get("slug", "?")), r, seen)
        total += len(recs)
        print(f"{base}: {len(recs)} records ok")
    print(f"\n{total} records checked")
    for w in warnings:
        print("WARN " + w)
    if errors:
        for e in errors:
            print("FAIL " + e)
        print(f"\n{len(errors)} error(s)")
        return 1
    print("all content checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
