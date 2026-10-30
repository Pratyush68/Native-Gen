#!/usr/bin/env python3
"""Local front-end server + Comfy Cloud proxy. Stdlib only.

  python server.py            # asks for your Comfy Cloud API key (hidden input), serves http://localhost:8188
  COMFY_API_KEY=... python server.py
  python server.py --mock     # fake backend for UI testing, no key, no credits

The key stays in this process; the page never sees it. /api/* is forwarded to
https://cloud.comfy.org with X-API-Key. /api/view redirects to a signed URL;
this proxy follows it server-side (no CORS problems in the browser).
"""
import os, sys, json, io, struct, getpass, mimetypes, threading, uuid, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = "https://cloud.comfy.org"
HERE = os.path.dirname(os.path.abspath(__file__))
MOCK = "--mock" in sys.argv
PORT = int(os.environ.get("PORT", 8188))
def _keyfile():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "key.txt")
    try: return open(p, encoding="utf-8-sig").read()
    except OSError: return ""
KEY = "" if MOCK else (os.environ.get("COMFY_API_KEY") or _keyfile().strip() or getpass.getpass("Comfy Cloud API key (hidden): "))
KEY = KEY.strip().strip('"').strip("'")

# ---------------- mock backend ----------------
JOBS = {}
def _png(color, ellipse=False, size=256):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (size, size), (0, 0, 0) if ellipse else color)
    if ellipse:
        ImageDraw.Draw(im).ellipse((40, 60, size - 40, size - 40), fill=(255, 255, 255))
    else:
        d = ImageDraw.Draw(im); d.rectangle((50, 80, size - 50, size - 30), fill=(255, 255, 255)); d.ellipse((60, 40, size - 60, 140), fill=tuple(255 - c for c in color))
    b = io.BytesIO(); im.save(b, "PNG"); return b.getvalue()
def _glb(color):
    pos = [(-.5,0,-.5),(.5,0,-.5),(.5,1,-.5),(-.5,1,-.5),(-.5,0,.5),(.5,0,.5),(.5,1,.5),(-.5,1,.5)]
    idx = [0,1,2,0,2,3,4,6,5,4,7,6,0,4,5,0,5,1,3,2,6,3,6,7,1,5,6,1,6,2,0,3,7,0,7,4]
    pb = b"".join(struct.pack("<3f", *p) for p in pos); ib = struct.pack(f"<{len(idx)}H", *idx); ib += b"\0" * (-len(ib) % 4)
    j = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1, "material": 0}]}],
         "materials": [{"pbrMetallicRoughness": {"baseColorFactor": [*color, 1], "metallicFactor": 0, "roughnessFactor": .8}}],
         "buffers": [{"byteLength": len(pb) + len(ib)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(pb), "target": 34962}, {"buffer": 0, "byteOffset": len(pb), "byteLength": len(idx) * 2, "target": 34963}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 8, "type": "VEC3", "min": [-.5,0,-.5], "max": [.5,1,.5]}, {"bufferView": 1, "componentType": 5123, "count": len(idx), "type": "SCALAR"}]}
    jb = json.dumps(j).encode(); jb += b" " * (-len(jb) % 4); bin_ = pb + ib
    return struct.pack("<4sII", b"glTF", 2, 28 + len(jb) + len(bin_)) + struct.pack("<I4s", len(jb), b"JSON") + jb + struct.pack("<I4s", len(bin_), b"BIN\0") + bin_
def mock_prompt(body):
    pid = uuid.uuid4().hex; p = body["prompt"]; out = {}
    if any(n["class_type"] == "TextGenerate" for n in p.values()):
        out["b"] = {"text": ["Bed, desk, office chair, bookshelf, rug, television, backpack, door, wardrobe, table lamp, potted plant, dresser, wall, floor."]}
    elif any(n["class_type"] == "SAM3_Detect" for n in p.values()):
        from PIL import Image, ImageDraw
        k = 2 if "bed" in json.dumps(p) else 1
        boxes = [{"x": 40 + 120 * i, "y": 80 + 30 * i, "width": 100, "height": 120, "score": .9} for i in range(k)]
        for i, b in enumerate(boxes):
            im = Image.new("RGB", (500, 500)); ImageDraw.Draw(im).ellipse((b["x"], b["y"], b["x"] + b["width"], b["y"] + b["height"]), fill=(255, 255, 255))
            bt = io.BytesIO(); im.save(bt, "PNG"); FILES[f"{pid}_mask_{i}.png"] = bt.getvalue()
        out["b"] = {"text": [json.dumps([boxes])]}
        out["v"] = {"images": [{"filename": f"{pid}_mask_{i}.png", "subfolder": "room", "type": "output"} for i in range(k)]}
    elif any(n["class_type"] == "TextEncodeQwenImageEditPlus" for n in p.values()):
        from PIL import Image, ImageDraw
        import random
        im = Image.new("RGB", (1024, 1024), (128, 128, 128)); ImageDraw.Draw(im).rectangle((250, 250, 770, 770), fill=tuple(random.randint(60, 220) for _ in range(3)))
        bt = io.BytesIO(); im.save(bt, "PNG"); FILES[f"{pid}_ref.png"] = bt.getvalue()
        out["sv"] = {"images": [{"filename": f"{pid}_ref.png", "subfolder": "room", "type": "output"}]}
    else:
        n = len(FILES); FILES[f"{pid}.glb"] = _glb([(.8,.4,.3),(.3,.6,.8),(.4,.7,.4)][n % 3])
        out["322"] = {"3d": [{"filename": f"{pid}.glb", "subfolder": "room", "type": "output"}]}
    JOBS[pid] = out; return {"prompt_id": pid}
FILES = {}

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, code, data, ctype="application/json"):
        if isinstance(data, (dict, list)): data = json.dumps(data).encode()
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self): self.route("GET")
    def do_POST(self): self.route("POST")
    def route(self, method):
        path = self.path
        if not path.startswith("/api/"):
            f = "index.html" if path in ("/", "") else path.lstrip("/").split("?")[0]
            fp = os.path.normpath(os.path.join(HERE, f))
            if not fp.startswith(HERE) or not os.path.isfile(fp) or fp.endswith("server.py"): return self._send(404, b"not found", "text/plain")
            return self._send(200, open(fp, "rb").read(), mimetypes.guess_type(fp)[0] or "application/octet-stream")
        n = int(self.headers.get("Content-Length") or 0); body = self.rfile.read(n) if n else b""
        if MOCK: return self.mock(method, path, body)
        req = urllib.request.Request(BASE + path, data=body if method == "POST" else None, method=method)
        req.add_header("X-API-Key", KEY)
        if self.headers.get("Content-Type"): req.add_header("Content-Type", self.headers["Content-Type"])
        try:
            if path.startswith("/api/view"):
                class NoRedir(urllib.request.HTTPRedirectHandler):
                    def redirect_request(self, *a, **k): return None
                try: r = urllib.request.build_opener(NoRedir).open(req)
                except urllib.error.HTTPError as e:
                    if e.code in (301, 302, 303, 307, 308):
                        r = urllib.request.urlopen(urllib.request.Request(e.headers["Location"]))  # signed URL: no auth header
                    else: raise
            else: r = urllib.request.urlopen(req)
            data = r.read(); self._send(r.status, data, r.headers.get("Content-Type", "application/octet-stream"))
        except urllib.error.HTTPError as e: self._send(e.code, e.read() or b"{}", e.headers.get("Content-Type", "application/json"))
        except Exception as e: self._send(502, {"error": str(e)})
    def mock(self, method, path, body):
        if path.startswith("/api/upload/image"): return self._send(200, {"name": "mock_upload.png", "subfolder": ""})
        if path.startswith("/api/prompt"): return self._send(200, mock_prompt(json.loads(body)))
        if path.startswith("/api/jobs/"):
            pid = path.rstrip("/").split("/")[-1]; return self._send(200, {"status": "completed", "outputs": JOBS.get(pid, {})})
        if "/status" in path: return self._send(200, {"status": "success"})
        if path.startswith("/api/history"):
            pid = path.rstrip("/").split("/")[-1].split("?")[0]; return self._send(200, {pid: {"outputs": JOBS.get(pid, {}), "status": {"status_str": "success"}}})
        if path.startswith("/api/view"):
            from urllib.parse import urlparse, parse_qs
            fn = parse_qs(urlparse(path).query).get("filename", [""])[0]
            return self._send(200, FILES.get(fn, b""), "model/gltf-binary" if fn.endswith(".glb") else "image/png")
        self._send(404, {"error": "mock: unhandled " + path})

if __name__ == "__main__":
    if not MOCK:
        print(f"key loaded: {len(KEY)} characters, starts with '{KEY[:8]}'  (a Comfy key is about 72 characters and starts with 'comfyui-')")
        try:
            r = urllib.request.urlopen(urllib.request.Request(BASE + "/api/user", headers={"X-API-Key": KEY}))
            print("cloud check: OK", r.status)
        except urllib.error.HTTPError as e:
            print("cloud check: FAILED", e.code, e.read()[:200])
        except Exception as e:
            print("cloud check: error", e)
    print(f"{'MOCK ' if MOCK else ''}serving http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
