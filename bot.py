#!/usr/bin/env python3
"""
Daily Shorts pipeline: render -> Telegram approval -> YouTube upload -> report.

  python bot.py render [index]   # make today's video and send it to Telegram with buttons
  python bot.py check            # read Telegram button presses; upload approved videos
  python bot.py report           # send channel stats to Telegram

Environment (GitHub Secrets):
  TG_TOKEN, TG_CHAT_ID, YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
Optional: START_DATE (YYYY-MM-DD, day #1 of the topic list), YT_PRIVACY (public|unlisted|private)
"""
import datetime, json, os, subprocess, sys, tempfile, traceback
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.environ.get("TG_TOKEN", "").strip()
CHAT = os.environ.get("TG_CHAT_ID", "").strip()
API = f"https://api.telegram.org/bot{TOKEN}"
TZ = datetime.timezone(datetime.timedelta(hours=5))   # Tashkent
START = os.environ.get("START_DATE") or "2026-11-15"
PRIVACY = os.environ.get("YT_PRIVACY") or "public"


def tg(method, files=None, **params):
    for k, v in list(params.items()):
        if isinstance(v, (dict, list)):
            params[k] = json.dumps(v)
    r = requests.post(f"{API}/{method}", data=params, files=files, timeout=300)
    j = r.json()
    if not j.get("ok"):
        raise RuntimeError(f"Telegram {method}: {j}")
    return j["result"]


def say(text, **kw):
    return tg("sendMessage", chat_id=CHAT, text=text, disable_web_page_preview=True, **kw)


def topics():
    with open(os.path.join(HERE, "topics.json"), encoding="utf-8") as f:
        return json.load(f)


def today_index(n):
    today = datetime.datetime.now(TZ).date()
    start = datetime.date.fromisoformat(START)
    return (today - start).days % n


def find_topic(tid):
    for i, t in enumerate(topics()):
        if t["id"] == tid:
            return i, t
    raise KeyError(tid)


def description(t):
    tags = " ".join("#" + x.replace(" ", "").replace("'", "") for x in t["tags"][:5])
    return (f"{t['desc']}\n\n"
            f"Every day Bolt answers a new 'why' about tech, AI, cars and our amazing world! "
            f"Subscribe so you don't miss tomorrow's answer. 🔔\n\n"
            f"{tags} #shorts #didyouknow")


# ------------------------------------------------------------------ render
def cmd_render(arg=None):
    T = topics()
    idx = int(arg) % len(T) if arg is not None else today_index(len(T))
    t = T[idx]
    out = os.path.join(HERE, "out", f"{t['id']}.mp4")
    subprocess.run([sys.executable, os.path.join(HERE, "make_video.py"), "--topic", str(idx), "--out", out], check=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out],
                         capture_output=True, text=True).stdout.strip()
    size = os.path.getsize(out) / 1e6
    caption = (f"🎬 #{idx + 1} — {t['title']}\n\n"
               f"📝 {t['desc']}\n\n"
               f"⏱ {float(dur):.0f} s · {size:.1f} MB · id: {t['id']}\n"
               f"YouTube'ga yuklaymi?")
    kb = {"inline_keyboard": [[{"text": "✅ Yuklash", "callback_data": f"ok:{t['id']}"},
                               {"text": "❌ Bekor", "callback_data": f"no:{t['id']}"}]]}
    with open(out, "rb") as f:
        tg("sendVideo", files={"video": f}, chat_id=CHAT, caption=caption[:1024],
           supports_streaming="true", width="1080", height="1920", reply_markup=kb)
    print("sent", t["id"])


# ------------------------------------------------------------------ youtube
def yt_client():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    import re
    pats = {"YT_CLIENT_ID": r"[0-9]+-[a-z0-9]+\.apps\.googleusercontent\.com",
            "YT_CLIENT_SECRET": r"GOCSPX-[A-Za-z0-9_\-]+",
            "YT_REFRESH_TOKEN": r"1//[A-Za-z0-9_\-]+"}
    def env(k):   # tolerate copy-paste extras: spaces, line breaks, other lines, "NAME = value"
        v = os.environ.get(k, "")
        m = re.search(pats[k], "".join(v.split()) if k == "YT_REFRESH_TOKEN" else v)
        return m.group(0) if m else v.strip()
    creds = Credentials(None, refresh_token=env("YT_REFRESH_TOKEN"),
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=env("YT_CLIENT_ID"), client_secret=env("YT_CLIENT_SECRET"))
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def recent_upload(title):
    """Return the video id if a video with this title was among our last uploads (avoids duplicates on retries)."""
    yt = yt_client()
    ch = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    items = yt.playlistItems().list(part="snippet", playlistId=up, maxResults=6).execute().get("items", [])
    for it in items:
        if it["snippet"]["title"].strip() == title[:100].strip():
            return it["snippet"]["resourceId"]["videoId"]
    return None


def yt_upload(path, t):
    from googleapiclient.http import MediaFileUpload
    yt = yt_client()
    body = {
        "snippet": {"title": t["title"][:100], "description": description(t), "tags": t["tags"] + ["shorts", "did you know", "bolt knows why"],
                    "categoryId": "27", "defaultLanguage": "en", "defaultAudioLanguage": "en"},
        "status": {"privacyStatus": PRIVACY, "selfDeclaredMadeForKids": False},
    }
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(path, mimetype="video/mp4", chunksize=-1, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return resp["id"], resp.get("status", {}).get("privacyStatus", "?")


# ------------------------------------------------------------------ check
def cmd_check():
    ups = tg("getUpdates", timeout=0, allowed_updates=["message", "callback_query"])
    if not ups:
        print("no updates")
        return
    for u in ups:
        try:
            handle(u)
        except Exception as e:
            traceback.print_exc()
            try:
                say(f"⚠️ Xatolik: {e}")
            except Exception:
                pass
    tg("getUpdates", offset=ups[-1]["update_id"] + 1, timeout=0)   # mark as read


def handle(u):
    if "message" in u:
        m = u["message"]
        chat = str(m["chat"]["id"])
        text = (m.get("text") or "").strip()
        if chat != CHAT:
            tg("sendMessage", chat_id=chat, text=f"Sizning chat ID: {chat}\nUni GitHub Secrets'ga TG_CHAT_ID nomi bilan qo'shing.")
            return
        if text.startswith("/report"):
            cmd_report()
        elif text.startswith("/next"):
            T = topics()
            i = (today_index(len(T)) + 1) % len(T)
            say(f"Ertangi mavzu: #{i + 1} {T[i]['label']}")
        elif text.startswith("/start") or text.startswith("/help"):
            say("Salom! Har kuni ertalab yangi video yuboraman.\n✅ — YouTube'ga yuklayman\n❌ — bekor qilaman\n"
                "/report — kanal statistikasi\n/next — ertangi mavzu")
        return
    if "callback_query" not in u:
        return
    q = u["callback_query"]
    if str(q["from"]["id"]) != CHAT and str(q["message"]["chat"]["id"]) != CHAT:
        return
    action, _, tid = q.get("data", "").partition(":")
    msg = q["message"]
    try:
        tg("answerCallbackQuery", callback_query_id=q["id"], text="Qabul qilindi")
    except Exception:
        pass
    tg("editMessageReplyMarkup", chat_id=msg["chat"]["id"], message_id=msg["message_id"],
       reply_markup={"inline_keyboard": []})
    idx, t = find_topic(tid)
    if action == "no":
        say(f"❌ Bekor qilindi: {t['label']}", reply_to_message_id=msg["message_id"])
        return
    if action != "ok":
        return
    f = tg("getFile", file_id=msg["video"]["file_id"])
    path = os.path.join(tempfile.mkdtemp(), "v.mp4")
    with requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{f['file_path']}", stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(path, "wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk)
    try:
        vid, status = yt_upload(path, t)
    except Exception as e:
        say(f"⚠️ YouTube'ga yuklab bo'lmadi: {e}\n\nQo'lda yuklash uchun:\n\nSARLAVHA:\n{t['title']}\n\nTAVSIF:\n{description(t)}",
            reply_to_message_id=msg["message_id"])
        return
    now = datetime.datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    say(f"✅ Yuklandi! ({now})\n🎬 {t['title']}\n🔗 https://youtube.com/shorts/{vid}\n🔒 Holat: {status}",
        reply_to_message_id=msg["message_id"])


# ------------------------------------------------------------------ report
def cmd_report():
    yt = yt_client()
    ch = yt.channels().list(part="statistics,snippet,contentDetails", mine=True).execute()["items"][0]
    st = ch["statistics"]
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    items = yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=7).execute()["items"]
    ids = [i["contentDetails"]["videoId"] for i in items]
    lines = []
    if ids:
        vs = yt.videos().list(part="statistics,snippet", id=",".join(ids)).execute()["items"]
        for v in vs:
            s = v["statistics"]
            lines.append(f"• {v['snippet']['title'][:45]} — 👁 {s.get('viewCount', 0)} · 👍 {s.get('likeCount', 0)}")
    say(f"📊 {ch['snippet']['title']}\n"
        f"👥 Obunachilar: {st.get('subscriberCount', '?')}\n"
        f"👁 Jami ko'rishlar: {st.get('viewCount', '?')}\n"
        f"🎬 Videolar: {st.get('videoCount', '?')}\n\n"
        f"Oxirgi videolar:\n" + ("\n".join(lines) or "—"))


if __name__ == "__main__":
    if not TOKEN or not CHAT and (len(sys.argv) < 2 or sys.argv[1] != "check"):
        sys.exit("TG_TOKEN / TG_CHAT_ID yo'q (GitHub Secrets'ni tekshiring)")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "render"
    {"render": lambda: cmd_render(sys.argv[2] if len(sys.argv) > 2 else None),
     "check": cmd_check, "report": cmd_report}[cmd]()
