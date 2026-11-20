"""Package a finished clip for posting: cover, per-platform captions, queue row.

The gtavi-claudecode scripts stop at a local MP4; this fills the gap between "clip is
ready" and "upload it". It never talks to a network: it writes one folder per clip that
holds everything a human (or an uploader with your API keys) needs.

usage:
  python tools/publish.py jobs/<id>/edits/clip_1.mp4 --platforms all \
      --credit "@caseoh_" --hook "Nobody noticed this" --hashtags gta6,gta6clips,vicecity

writes:
  publish/<date>-<slug>/clip.mp4        hardlink (or copy) of the clip
  publish/<date>-<slug>/cover.jpg       frame at --cover-sec, <= 1080x1920
  publish/<date>-<slug>/caption.txt     per-platform captions, ready to paste
  publish/<date>-<slug>/caption_<p>.txt one file per platform, for uploaders
  publish/<date>-<slug>/meta.json       source, credit, campaign, specs
  publish/queue.csv                     one row per publish job (status=pending)
"""
import argparse, csv, json, re, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

LIMITS = {"shorts": 5000, "reels": 2200, "tiktok": 2200, "x": 280, "facebook": 63206}
TITLE_LIMITS = {"shorts": 100, "reels": 0, "tiktok": 0, "x": 0, "facebook": 0}
HASHTAG_CAP = {"shorts": 3, "reels": 10, "tiktok": 5, "x": 2, "facebook": 3}
MAX_TAGS = {  # hard platform caps
    "shorts": 15, "reels": 30, "tiktok": 20, "x": 5, "facebook": 30,
}


def ffprobe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration:stream=codec_type,width,height,r_frame_rate", "-of", "json", str(path)],
                       capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def specs(path):
    p = ffprobe(path)
    v = next((s for s in p["streams"] if s["codec_type"] == "video"), {})
    a = next((s for s in p["streams"] if s["codec_type"] == "audio"), None)
    return {"duration": round(float(p["format"]["duration"]), 2), "width": v.get("width"), "height": v.get("height"),
            "fps": v.get("r_frame_rate"), "audio": bool(a)}


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return (s or "clip")[:48]


def siblings(mp4):
    """clip_<n>.json written by cut.py, if it is there."""
    meta = mp4.with_suffix(".json")
    if meta.exists():
        try:
            return json.loads(meta.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def caption_for(platform, body, credit, tags, source_url):
    tags = ["#" + t.lstrip("#") for t in tags if t.strip()][:min(HASHTAG_CAP.get(platform, 3), MAX_TAGS.get(platform, 20))]
    lines = [body.strip()]
    if platform != "shorts":
        lines.append("")
    if credit:
        lines.append(f"clip: {credit}")
    if tags:
        lines.append(" ".join(tags))
    text = "\n".join(x for x in lines if x is not None).strip()
    limit = LIMITS.get(platform, 2200)
    if len(text) > limit:  # trim the body, never the credit or the tags
        tag_line = " ".join(tags)
        keep = limit - len(tag_line) - len(credit) - 8
        text = body.strip()[:max(0, keep)].rstrip() + ("…" if keep > 0 else "")
        text = "\n".join(x for x in [text, f"clip: {credit}" if credit else "", tag_line] if x)
    return text


def make_cover(mp4, out, sec):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{sec}", "-i", str(mp4), "-frames:v", "1",
                    "-vf", "scale='min(1080,iw)':-2", "-q:v", "2", str(out)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("--platforms", default="all", help="all or a comma list: shorts,reels,tiktok,x,facebook")
    ap.add_argument("--hook", default="", help="first line of the caption (default: hook from cut.py)")
    ap.add_argument("--caption", default="", help="full caption body; overrides --hook")
    ap.add_argument("--credit", default="")
    ap.add_argument("--hashtags", default="gta6,gta6clips,gta,rockstar")
    ap.add_argument("--campaign", default="", help="campaign name for the queue row")
    ap.add_argument("--cover-sec", type=float, default=1.2)
    ap.add_argument("--root", default=".", help="clip desk root (default: cwd)")
    a = ap.parse_args()

    plat_all = ["shorts", "reels", "tiktok", "x"]
    platforms = plat_all if a.platforms == "all" else [p.strip() for p in a.platforms.split(",") if p.strip()]
    unknown = [p for p in platforms if p not in LIMITS]
    if unknown:
        sys.exit(f"unknown platform(s): {', '.join(unknown)} (known: {', '.join(LIMITS)})")

    mp4 = Path(a.clip).resolve()
    if not mp4.exists():
        sys.exit(f"clip not found: {mp4}")
    meta = siblings(mp4)
    hook = a.caption or a.hook or meta.get("hook") or meta.get("title") or ""
    credit = a.credit or meta.get("credit") or ""
    source = meta.get("source_url") or ""
    s = specs(mp4)
    if s["width"] != 1080 or s["height"] != 1920:
        print(f"warning: {s['width']}x{s['height']} is not 1080x1920 — most feeds crop it", file=sys.stderr)
    if not s["audio"]:
        print("warning: no audio stream (muted viewers are fine, but feeds push silent clips less)", file=sys.stderr)

    date = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    tag = slugify(hook or mp4.stem)
    outdir = Path(a.root) / "publish" / f"{date}-{tag}"
    outdir.mkdir(parents=True, exist_ok=True)

    dest = outdir / "clip.mp4"
    if not dest.exists():
        try:
            dest.hardlink_to(mp4)
        except OSError:
            shutil.copy2(mp4, dest)

    make_cover(dest, outdir / "cover.jpg", a.cover_sec)

    tags = [t for t in a.hashtags.split(",") if t.strip()]
    title = (hook or "").strip()[:100]
    lines, per_platform, titles = ["# captions", ""], {}, {}
    for p in platforms:
        text = caption_for(p, hook, credit, tags, source)
        per_platform[p] = text
        (outdir / f"caption_{p}.txt").write_text(text, encoding="utf-8")
        lines += [f"## {p}  ({len(text)}/{LIMITS[p]} chars)", "", text, ""]
        if TITLE_LIMITS.get(p):
            titles[p] = title
            lines += [f"## {p} title  ({len(title)}/{TITLE_LIMITS[p]} chars)", "", title, ""]
    (outdir / "caption.txt").write_text("\n".join(lines), encoding="utf-8")

    info = {"clip": str(dest), "created": datetime.now().astimezone().isoformat(timespec="seconds"),
            "hook": hook, "credit": credit, "hashtags": tags, "platforms": platforms,
            "source_url": source, "source_title": meta.get("source_title"), "source_channel": meta.get("source_channel"),
            "campaign": a.campaign, "specs": s, "captions": per_platform, "titles": titles}
    (outdir / "meta.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")

    queue = Path(a.root) / "publish" / "queue.csv"
    new = not queue.exists()
    with queue.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["created", "folder", "clip", "platforms", "hook", "credit", "campaign",
                        "source_url", "duration_sec", "status", "posted_url", "posted_at"])
        for p in platforms:
            w.writerow([info["created"], str(outdir), dest.name, p, hook, credit, a.campaign, source,
                        s["duration"], "pending", "", ""])

    print(f"{outdir}")
    for p in platforms:
        extra = f", title {len(titles[p])} chars" if p in titles else ""
        print(f"  {p:<7} caption {len(per_platform[p]):>4} chars -> caption_{p}.txt{extra}")
    print(f"  queue: {queue}")


if __name__ == "__main__":
    main()
