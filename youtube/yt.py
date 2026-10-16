"""YouTube channel helper: upload + schedule videos and Shorts, set thumbnails, add to playlists, read stats.

Credentials come from the environment (never from the repo): YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
(OAuth scopes: youtube, yt-analytics.readonly). Standard library only.

usage:
  python3 youtube/yt.py check
  python3 youtube/yt.py upload <video.mp4> --meta <youtube_metadata.txt> [--thumb <jpg>] [--at 2026-10-21T12:00] [--playlist "How Ancient Humans Lived"]
  python3 youtube/yt.py upload-short <short.mp4> --shorts-meta shorts_v2/shorts_metadata.txt [--at 2026-10-21T15:00]
  python3 youtube/yt.py stats [--days 28]
--at is New York time (America/New_York); without it the video stays private (a draft).
Unverified API projects can only upload private videos: then --at is ignored by YouTube until the project passes Google's audit.
"""
import argparse, datetime, json, mimetypes, os, re, sys, urllib.error, urllib.parse, urllib.request
from zoneinfo import ZoneInfo

API = "https://www.googleapis.com/youtube/v3"
NY = ZoneInfo("America/New_York")

def token():
    try:
        body = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                                       "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    except KeyError as e:
        sys.exit(f"missing environment variable {e}; add it in the cloud environment settings")
    return json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", body))["access_token"]

TOK = None
def call(method, url, params=None, body=None, data=None, ctype=None, raw=False):
    global TOK
    TOK = TOK or token()
    if params: url += "?" + urllib.parse.urlencode(params)
    headers = {"Authorization": f"Bearer {TOK}"}
    if body is not None: data, ctype = json.dumps(body).encode(), "application/json; charset=UTF-8"
    if ctype: headers["Content-Type"] = ctype
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        r = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {url.split('?')[0]} -> {e.code}: {e.read().decode()[:800]}")
    return r if raw else json.loads(r.read() or b"{}")

def my_channel():
    return call("GET", f"{API}/channels", {"part": "snippet,statistics,contentDetails", "mine": "true"})["items"][0]

def parse_meta(path):
    sec, cur = {}, None
    for ln in open(path, encoding="utf-8").read().split("\n"):
        if ln.strip() in ("TITLE", "ALT TITLES (A/B test)", "DESCRIPTION", "TAGS", "THUMBNAILS", "SETTINGS"): cur = ln.strip(); sec[cur] = []
        elif cur: sec[cur].append(ln)
    g = lambda k: "\n".join(sec.get(k, [])).strip()
    return {"title": g("TITLE").split("\n")[0], "description": g("DESCRIPTION"), "tags": [t.strip() for t in g("TAGS").split(",") if t.strip()]}

def parse_short(path, filename):
    block = open(path, encoding="utf-8").read().split(f"=== {filename} ")[1].split("\n===")[0]
    pick = lambda k: block.split(f"\n{k}\n")[1].split("\n")[0].strip()
    return {"title": pick("TITLE"), "description": pick("DESCRIPTION"), "tags": [t.strip() for t in pick("TAGS").split(",")],
            "related": re.search(r"RELATED VIDEO: (.+)", block).group(1).strip()}

def publish_at(s):
    if not s: return None
    dt = datetime.datetime.fromisoformat(s).replace(tzinfo=NY)
    return dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def upload(path, meta, at):
    status = {"privacyStatus": "private", "selfDeclaredMadeForKids": False, "embeddable": True}
    if at: status["publishAt"] = publish_at(at)
    tags, total = [], 0
    for t in meta["tags"]:                                    # YouTube caps tags at 500 characters in total
        if total + len(t) + 1 > 480: break
        tags.append(t); total += len(t) + 1
    body = {"snippet": {"title": meta["title"][:100], "description": meta["description"][:5000], "tags": tags,
                        "categoryId": "27", "defaultLanguage": "en", "defaultAudioLanguage": "en"}, "status": status}
    size = os.path.getsize(path)
    r = call("POST", "https://www.googleapis.com/upload/youtube/v3/videos", {"uploadType": "resumable", "part": "snippet,status"},
             body=body, raw=True)
    loc = r.headers["Location"]
    with open(path, "rb") as f:
        req = urllib.request.Request(loc, data=f, method="PUT",
                                     headers={"Authorization": f"Bearer {TOK}", "Content-Type": "video/mp4", "Content-Length": str(size)})
        vid = json.loads(urllib.request.urlopen(req, timeout=3600).read())
    print(f"uploaded {vid['id']}  https://youtu.be/{vid['id']}  privacy={vid['status']['privacyStatus']}"
          f"  publishAt={vid['status'].get('publishAt', '-')}")
    return vid["id"]

def set_thumb(vid, jpg):
    call("POST", "https://www.googleapis.com/upload/youtube/v3/thumbnails/set", {"videoId": vid},
         data=open(jpg, "rb").read(), ctype=mimetypes.guess_type(jpg)[0] or "image/jpeg")
    print("thumbnail set:", os.path.basename(jpg))

def add_to_playlist(vid, name):
    pls = call("GET", f"{API}/playlists", {"part": "snippet", "mine": "true", "maxResults": 50})["items"]
    pl = next((p for p in pls if p["snippet"]["title"].lower() == name.lower()), None)
    if not pl: print(f"playlist '{name}' not found, skipped"); return
    call("POST", f"{API}/playlistItems", {"part": "snippet"},
         body={"snippet": {"playlistId": pl["id"], "resourceId": {"kind": "youtube#video", "videoId": vid}}})
    print("added to playlist:", name)

def stats(days):
    ch = my_channel(); cid = ch["id"]; s = ch["statistics"]
    print(f"{ch['snippet']['title']}: {s.get('subscriberCount')} subscribers, {s.get('viewCount')} views, {s.get('videoCount')} videos")
    end = datetime.date.today(); start = end - datetime.timedelta(days=days)
    q = lambda **kw: call("GET", "https://youtubeanalytics.googleapis.com/v2/reports",
                          {"ids": "channel==MINE", "startDate": str(start), "endDate": str(end), **kw})
    rep = q(metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost", dimensions="video",
            sort="-views", maxResults=50)
    ids = [r[0] for r in rep.get("rows", [])]
    titles = {}
    for i in range(0, len(ids), 50):
        for it in call("GET", f"{API}/videos", {"part": "snippet,contentDetails", "id": ",".join(ids[i:i + 50])})["items"]:
            titles[it["id"]] = it["snippet"]["title"]
    print(f"\nlast {days} days, by video:")
    print(f"{'views':>7} {'avg s':>6} {'+subs':>5}  title")
    for r in rep.get("rows", []):
        print(f"{r[1]:>7} {r[3]:>6} {r[4]:>5}  {titles.get(r[0], r[0])[:70]}")
    src = q(metrics="views", dimensions="insightTrafficSourceType", sort="-views")
    print("\ntraffic sources:", ", ".join(f"{r[0]}={r[1]}" for r in src.get("rows", [])))

ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="cmd", required=True)
sub.add_parser("check")
u = sub.add_parser("upload"); u.add_argument("video"); u.add_argument("--meta", required=True); u.add_argument("--thumb")
u.add_argument("--at"); u.add_argument("--playlist")
us = sub.add_parser("upload-short"); us.add_argument("video"); us.add_argument("--shorts-meta", required=True); us.add_argument("--at")
st = sub.add_parser("stats"); st.add_argument("--days", type=int, default=28)
a = ap.parse_args()

if a.cmd == "check":
    ch = my_channel(); print("connected to:", ch["snippet"]["title"], ch["id"])
elif a.cmd == "upload":
    vid = upload(a.video, parse_meta(a.meta), a.at)
    if a.thumb: set_thumb(vid, a.thumb)
    if a.playlist: add_to_playlist(vid, a.playlist)
elif a.cmd == "upload-short":
    m = parse_short(a.shorts_meta, os.path.basename(a.video))
    upload(a.video, m, a.at)
    print(f"by hand in Studio: Related video = {m['related']} (the API cannot set it)")
elif a.cmd == "stats":
    stats(a.days)
