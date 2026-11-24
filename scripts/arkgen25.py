#!/usr/bin/env python3
"""
arkgen25 — scroll-world 大世界项目专用的 Ark 生成封装（Seedream 5.5 / Seedance 2.5）。

在 skill 版 arkgen.py 基础上：
  - 默认模型换成 doubao-seedream-5-5-261028 / doubao-seedance-2-5-260628
  - still 支持 --ref 参考图（一张或多张，只借风格不搬内容，约束写在 prompt 里）
  - 视频任务体与 2.0 兼容：content[] 里 first_frame / last_frame，base64 data URL
  - 打印任务 usage，方便按量核算

用法：
  arkgen25.py still --prompt <file> --out <png> [--size 2048x1152] [--ref a.webp ...]
  arkgen25.py dive  --prompt <file> --start <png> --out <mp4>
                    [--ratio 16:9] [--res 480p] [--dur 8]
  arkgen25.py conn  --prompt <file> --start <png> --end <png> --out <mp4>
                    [--ratio 16:9] [--res 480p] [--dur 5]
"""
import argparse, base64, json, os, ssl, sys, time, urllib.request, urllib.error

try:
    import certifi
    _SSLCTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _SSLCTX = ssl.create_default_context()

BASE = os.environ.get("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
VIDEO_MODEL = os.environ.get("ARK_VIDEO_MODEL", "doubao-seedance-2-5-260628")
IMAGE_MODEL = os.environ.get("ARK_IMAGE_MODEL", "doubao-seedream-5-5-261028")


def key():
    k = os.environ.get("ARK_API_KEY")
    if not k:
        sys.stderr.write("arkgen25: ARK_API_KEY not set\n")
        sys.exit(1)
    return k


def api(method, path, body=None, timeout=60):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + key())
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_SSLCTX) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        txt = e.read().decode(errors="replace")
        sys.stderr.write(f"arkgen25: HTTP {e.code} from {path}: {txt[:800]}\n")
        sys.exit(1)


def b64_dataUrl(path):
    with open(path, "rb") as f:
        b = base64.b64encode(f.read()).decode()
    ext = path.rsplit(".", 1)[-1].lower()
    mime = "image/webp" if ext == "webp" else ("image/jpeg" if ext in ("jpg", "jpeg") else "image/png")
    return f"data:{mime};base64,{b}"


def poll_task(task_id, timeout=1800, interval=8):
    deadline = time.time() + timeout
    while True:
        t = api("GET", f"/contents/generations/tasks/{task_id}")
        st = t.get("status")
        if st in ("succeeded", "failed", "cancelled", "expired"):
            return t
        if time.time() > deadline:
            sys.stderr.write(f"arkgen25: poll timeout after {timeout}s (last status={st})\n")
            return t
        time.sleep(interval)


def download(url, out):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=300, context=_SSLCTX) as r, open(out, "wb") as f:
        f.write(r.read())


def gen_still(args):
    prompt = open(args.prompt, encoding="utf-8").read().strip()
    body = {
        "model": IMAGE_MODEL,
        "prompt": prompt,
        "size": args.size,
        "response_format": "url",
        "watermark": False,
    }
    if args.ref:
        # Seedream 图生图/参考图：image 字段，URL 或 data URL 列表
        body["image"] = [b64_dataUrl(p) for p in args.ref]
    res = api("POST", "/images/generations", body, timeout=300)
    items = res.get("data") or []
    if not items or not items[0].get("url"):
        print(f"arkgen25 still FAIL: {json.dumps(res, ensure_ascii=False)[:400]}")
        sys.exit(1)
    download(items[0]["url"], args.out)
    print(f"arkgen25 still ok -> {args.out}")
    if res.get("usage"):
        print("usage:", json.dumps(res["usage"], ensure_ascii=False))


def gen_video(args, has_end):
    prompt = open(args.prompt, encoding="utf-8").read().strip()
    content = [{"type": "text", "text": prompt}]
    content.append({
        "type": "image_url",
        "image_url": {"url": b64_dataUrl(args.start)},
        "role": "first_frame",
    })
    if has_end:
        content.append({
            "type": "image_url",
            "image_url": {"url": b64_dataUrl(args.end)},
            "role": "last_frame",
        })
    body = {
        "model": VIDEO_MODEL,
        "content": content,
        # Seedance 2.5：带首帧时 ratio 跟随首帧图，传 ratio 会 400，故省略。
        # 竖屏链的正确做法是喂 9:16 竖屏首帧。
        "duration": args.dur,
        "generate_audio": False,
    }
    if args.res:
        body["resolution"] = args.res
    created = api("POST", "/contents/generations/tasks", body)
    task_id = created.get("id")
    if not task_id:
        print(f"arkgen25 video FAIL (no id): {json.dumps(created, ensure_ascii=False)[:400]}")
        sys.exit(1)
    print(f"arkgen25 video submitted task={task_id} model={VIDEO_MODEL} ratio=follow-first-frame dur={args.dur} res={args.res or 'auto'}", flush=True)
    t = poll_task(task_id, timeout=args.timeout)
    if t.get("status") != "succeeded":
        err = t.get("error") or {}
        print(f"arkgen25 video FAIL ({t.get('status')}): {err.get('message') or json.dumps(t, ensure_ascii=False)[:400]}")
        sys.exit(1)
    url = (t.get("content") or {}).get("video_url")
    if not url:
        print(f"arkgen25 video FAIL (no video_url): {json.dumps(t, ensure_ascii=False)[:400]}")
        sys.exit(1)
    download(url, args.out)
    usage = t.get("usage") or {}
    print(f"arkgen25 video ok -> {args.out} (tokens={usage.get('total_tokens', '?')})")


def main():
    p = argparse.ArgumentParser(prog="arkgen25")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("still")
    s.add_argument("--prompt", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--size", default="2048x1152")
    s.add_argument("--ref", nargs="*", default=[])

    d = sub.add_parser("dive")
    d.add_argument("--prompt", required=True)
    d.add_argument("--start", required=True)
    d.add_argument("--out", required=True)
    d.add_argument("--ratio", default="16:9")
    d.add_argument("--res", default="480p")
    d.add_argument("--dur", type=int, default=8)
    d.add_argument("--timeout", type=int, default=1800)

    c = sub.add_parser("conn")
    c.add_argument("--prompt", required=True)
    c.add_argument("--start", required=True)
    c.add_argument("--end", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--ratio", default="16:9")
    c.add_argument("--res", default="480p")
    c.add_argument("--dur", type=int, default=5)
    c.add_argument("--timeout", type=int, default=1800)

    a = p.parse_args()
    if a.cmd == "still":
        gen_still(a)
    elif a.cmd == "dive":
        gen_video(a, has_end=False)
    elif a.cmd == "conn":
        gen_video(a, has_end=True)


if __name__ == "__main__":
    main()
