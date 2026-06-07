#!/usr/bin/env python3
"""OJS REST API client — stdlib only. Works with OJS 3.3/3.4/3.5.

The base URL is everything BEFORE /api/v1, i.e. it must include index.php and
the journal path when restful_urls is Off (the default):
    https://example.com/index.php/myjournal
With restful_urls = On:
    https://example.com/myjournal
Site-level (admin) endpoints use the literal "_" context:
    https://example.com/index.php/_

Auth: a user API key (User Profile -> API Key; requires api_key_secret in
config.inc.php). Passed as "Authorization: Bearer <token>".

Examples:
    python ojs_api.py --base https://example.com/index.php/myjournal --token $TOKEN \
        GET submissions -p status=1 -p stageIds=3 -p count=20
    python ojs_api.py ... GET submissions/219
    python ojs_api.py ... GET issues --all                       # follow pagination
    python ojs_api.py ... PUT submissions/219/publications/305/publish
    python ojs_api.py ... PUT submissions/219/publications/305 \
        --json '{"title": {"en": "New title"}}'
    python ojs_api.py ... POST temporaryFiles --upload logo.png  # multipart upload

Env fallbacks: OJS_BASE_URL, OJS_API_TOKEN.
"""

import argparse
import json
import mimetypes
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid


def build_url(base: str, endpoint: str, params: list[tuple[str, str]]) -> str:
    base = base.rstrip("/")
    endpoint = endpoint.lstrip("/")
    if endpoint.startswith("api/v1/"):
        endpoint = endpoint[len("api/v1/"):]
    url = f"{base}/api/v1/{endpoint}"
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    return url


def make_request(url: str, method: str, token: str, body: bytes | None = None,
                 content_type: str | None = None, insecure: bool = False):
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    if content_type:
        req.add_header("Content-Type", content_type)
    ctx = ssl._create_unverified_context() if insecure else None
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def multipart_body(filepath: str) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    fname = os.path.basename(filepath)
    ctype = mimetypes.guess_type(fname)[0] or "application/octet-stream"
    with open(filepath, "rb") as f:
        data = f.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{fname}"\r\n'
        f"Content-Type: {ctype}\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    return body, f"multipart/form-data; boundary={boundary}"


def pretty(raw: bytes) -> str:
    try:
        return json.dumps(json.loads(raw), indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return raw.decode(errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="OJS REST API client (stdlib-only).",
        epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default=os.environ.get("OJS_BASE_URL"),
                    help="Base URL up to (excluding) /api/v1 — include index.php/<journalPath> "
                         "unless restful_urls=On. Env: OJS_BASE_URL")
    ap.add_argument("--token", default=os.environ.get("OJS_API_TOKEN"),
                    help="API key from User Profile -> API Key. Env: OJS_API_TOKEN")
    ap.add_argument("method", choices=["GET", "POST", "PUT", "DELETE"],
                    type=str.upper, help="HTTP method")
    ap.add_argument("endpoint", help="Endpoint path after /api/v1/, e.g. submissions/12")
    ap.add_argument("-p", "--param", action="append", default=[],
                    metavar="KEY=VALUE", help="Query parameter (repeatable)")
    ap.add_argument("--json", dest="json_body", metavar="JSON",
                    help="JSON request body (string, or @file.json)")
    ap.add_argument("--upload", metavar="FILE",
                    help="Upload FILE as multipart form-data field 'file' "
                         "(use with POST temporaryFiles)")
    ap.add_argument("--all", action="store_true",
                    help="GET only: follow count/offset pagination, merge items")
    ap.add_argument("--insecure", action="store_true",
                    help="Skip TLS certificate verification (self-signed dev servers)")
    args = ap.parse_args()

    if not args.base or not args.token:
        ap.error("--base and --token are required (or set OJS_BASE_URL / OJS_API_TOKEN)")

    params = []
    for p in args.param:
        if "=" not in p:
            ap.error(f"--param must be KEY=VALUE, got: {p}")
        params.append(tuple(p.split("=", 1)))

    body, ctype = None, None
    if args.upload:
        body, ctype = multipart_body(args.upload)
    elif args.json_body is not None:
        text = args.json_body
        if text.startswith("@"):
            with open(text[1:], encoding="utf-8") as f:
                text = f.read()
        json.loads(text)  # validate early
        body, ctype = text.encode(), "application/json"

    if args.all and args.method == "GET":
        # OJS paginates with count/offset; list endpoints return
        # {"itemsMax": N, "items": [...]}
        merged, offset = [], 0
        count = int(dict(params).get("count", 100))
        base_params = [(k, v) for k, v in params if k not in ("count", "offset")]
        while True:
            page_params = base_params + [("count", str(count)), ("offset", str(offset))]
            url = build_url(args.base, args.endpoint, page_params)
            status, raw = make_request(url, "GET", args.token, insecure=args.insecure)
            if status >= 400:
                print(pretty(raw), file=sys.stderr)
                return 1
            data = json.loads(raw)
            items = data.get("items")
            if items is None:  # not a paginated list endpoint
                print(pretty(raw))
                return 0
            merged.extend(items)
            if len(merged) >= data.get("itemsMax", 0) or not items:
                break
            offset += count
        print(json.dumps({"itemsMax": len(merged), "items": merged},
                         indent=2, ensure_ascii=False))
        return 0

    url = build_url(args.base, args.endpoint, params)
    status, raw = make_request(url, args.method, args.token, body, ctype,
                               insecure=args.insecure)
    out = sys.stdout if status < 400 else sys.stderr
    print(f"HTTP {status}", file=sys.stderr)
    print(pretty(raw), file=out)
    return 0 if status < 400 else 1


if __name__ == "__main__":
    sys.exit(main())
