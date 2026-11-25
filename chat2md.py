#!/usr/bin/env python3
"""chat2md — turn a public ChatGPT or Grok *share link* into a Markdown file.

Usage:
    python3 chat2md.py <share-url> [more urls...] [-o OUTDIR]

Supported:
    https://chatgpt.com/share/<id>    (also chat.openai.com/share/<id>)
    https://grok.com/share/<id>       (also .../share/<slug>_<id>)

No login, no browser, standard library only.
"""
import argparse, json, re, sys, urllib.request, urllib.error
from pathlib import Path

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} fetching {url}: {e.read()[:300]!r}")


# ---------------------------------------------------------------- ChatGPT
def decode_turbo(flat):
    """Decode React Router's turbo-stream flat array into Python objects."""
    memo = {}

    def val(i):
        if not isinstance(i, int) or i < 0:
            return None  # negative indices are undefined/null/NaN/holes
        if i in memo:
            return memo[i]
        v = flat[i]
        if isinstance(v, dict):
            out = {}
            memo[i] = out
            for k, vi in v.items():
                out[flat[int(k[1:])]] = val(vi)
            return out
        if isinstance(v, list):
            if v and isinstance(v[0], str) and v[0] in ("D", "P", "Y", "R", "E", "S", "Z"):
                return v[1] if len(v) > 1 and not isinstance(v[1], int) else None
            out = []
            memo[i] = out
            out.extend(val(x) for x in v)
            return out
        memo[i] = v
        return v

    return val(0)


def find_key(obj, key):
    stack = [obj]
    seen = set()
    while stack:
        o = stack.pop()
        if id(o) in seen:
            continue
        seen.add(id(o))
        if isinstance(o, dict):
            if key in o and o[key]:
                return o
            stack.extend(o.values())
        elif isinstance(o, list):
            stack.extend(o)
    return None


def part_text(p):
    if isinstance(p, str):
        return p
    if isinstance(p, dict):
        if p.get("content_type") == "image_asset_pointer":
            return "*[image]*"
        return p.get("text") or ""
    return ""


def chatgpt(url):
    html = fetch(url)
    chunks = re.findall(r'streamController\.enqueue\(("(?:[^"\\]|\\.)*")\)', html)
    if not chunks:
        sys.exit("Could not find conversation data in the ChatGPT page.")
    first_line = "".join(json.loads(c) for c in chunks).split("\n", 1)[0]
    data = decode_turbo(json.loads(first_line))
    conv = find_key(data, "mapping")
    if not conv:
        err = find_key(data, "error")
        sys.exit("ChatGPT returned no conversation" + (f": {err.get('error')}" if err else "."))

    mapping = conv["mapping"]
    node = conv.get("current_node") or next(
        (k for k, n in mapping.items() if not n.get("children")), None)
    chain = []
    while node and node in mapping:
        chain.append(mapping[node])
        node = mapping[node].get("parent")
    chain.reverse()

    msgs = []
    for n in chain:
        m = n.get("message") or {}
        role = (m.get("author") or {}).get("role")
        if role not in ("user", "assistant"):
            continue
        meta = m.get("metadata") or {}
        if meta.get("is_visually_hidden_from_conversation"):
            continue
        c = m.get("content") or {}
        if c.get("content_type") not in (None, "text", "multimodal_text", "code"):
            continue  # skip tool calls, reasoning, etc.
        text = c.get("text") if c.get("content_type") == "code" else \
            "\n\n".join(filter(None, (part_text(p) for p in c.get("parts") or [])))
        if c.get("content_type") == "code" and text:
            text = f"```\n{text}\n```"
        if text and text.strip():
            msgs.append(("User" if role == "user" else "ChatGPT", text.strip()))
    return conv.get("title") or "ChatGPT conversation", msgs


# ---------------------------------------------------------------- Grok
def grok(url):
    m = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", url)
    sid = m.group(1) if m else url.rstrip("/").split("/")[-1].split("?")[0]
    data = json.loads(fetch(f"https://grok.com/rest/app-chat/share_links/{sid}"))
    conv = data.get("conversation") or {}
    msgs = []
    for r in data.get("responses") or []:
        text = (r.get("message") or "").strip()
        if not text:
            continue
        who = "User" if (r.get("sender") or "").lower() == "human" else "Grok"
        msgs.append((who, text))
    return conv.get("title") or data.get("title") or "Grok conversation", msgs


# ---------------------------------------------------------------- main
def to_md(title, msgs, url):
    out = [f"# {title}", "", f"> Source: {url}", ""]
    for who, text in msgs:
        out += [f"## {who}", "", text, "", "---", ""]
    return "\n".join(out)


def slug(s):
    return re.sub(r"[^\w\- ]+", "", s).strip().replace(" ", "-")[:80] or "chat"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("urls", nargs="+")
    ap.add_argument("-o", "--outdir", default=".")
    a = ap.parse_args()
    Path(a.outdir).mkdir(parents=True, exist_ok=True)
    for url in a.urls:
        if "grok.com" in url:
            title, msgs = grok(url)
        elif "chatgpt.com" in url or "openai.com" in url:
            title, msgs = chatgpt(url)
        else:
            print(f"Skipping unsupported URL: {url}", file=sys.stderr)
            continue
        if not msgs:
            print(f"No messages found in {url}", file=sys.stderr)
            continue
        path = Path(a.outdir) / f"{slug(title)}.md"
        path.write_text(to_md(title, msgs, url), encoding="utf-8")
        print(f"Wrote {path} ({len(msgs)} messages)")


if __name__ == "__main__":
    main()
