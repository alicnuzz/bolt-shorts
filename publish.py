#!/usr/bin/env python3
"""
Twice-daily Shorts publisher for "Bolt Knows Why".

  python publish.py slot 06:30      # run ~1 hour before 06:30 Tashkent time
  python publish.py slot 17:00

Flow for one slot:
  1. pick the next story (stories/*.json, in name order, two per day)
  2. render it with the Mac "Daniel" voice  (runs on a macOS GitHub runner)
  3. at slot time - 30 min: send the video to Telegram with  ✅ / ❌  buttons
  4. wait until slot time:  ❌ = cancel,  ✅ or no answer = publish
  5. upload to YouTube (public) and report the link in Telegram
"""
import datetime, glob, json, os, subprocess, sys, tempfile, time
import bot   # tg(), say(), yt_upload(), description()

HERE = os.path.dirname(os.path.abspath(__file__))
TZ = datetime.timezone(datetime.timedelta(hours=5))          # Asia/Tashkent
SLOTS = ["06:30", "17:00"]
START = datetime.date.fromisoformat(os.environ.get("START_DATE") or "2026-11-16")
ASK_BEFORE = datetime.timedelta(minutes=30)


def stories():
    files = sorted(glob.glob(os.path.join(HERE, "stories", "*.json")))
    return files


def pick_story(slot):
    files = stories()
    today = datetime.datetime.now(TZ).date()
    idx = ((today - START).days * len(SLOTS) + SLOTS.index(slot)) % len(files)
    return files[idx]


def slot_datetime(slot):
    h, m = map(int, slot.split(":"))
    now = datetime.datetime.now(TZ)
    t = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if t < now - datetime.timedelta(hours=2):        # job started after midnight for tomorrow's slot
        t += datetime.timedelta(days=1)
    return t


def sleep_until(t):
    while True:
        left = (t - datetime.datetime.now(TZ)).total_seconds()
        if left <= 0:
            return
        time.sleep(min(left, 60))


def wait_for_answer(message_id, deadline):
    """Long-poll Telegram until deadline. Returns 'ok', 'no' or None (no answer)."""
    offset = None
    while datetime.datetime.now(TZ) < deadline:
        left = int((deadline - datetime.datetime.now(TZ)).total_seconds())
        try:
            ups = bot.tg("getUpdates", timeout=max(1, min(50, left)), offset=offset,
                         allowed_updates=["callback_query", "message"])
        except Exception as e:
            print("poll error", e); time.sleep(5); continue
        for u in ups:
            offset = u["update_id"] + 1
            q = u.get("callback_query")
            if not q or q.get("message", {}).get("message_id") != message_id:
                continue
            if str(q["from"]["id"]) != bot.CHAT and str(q["message"]["chat"]["id"]) != bot.CHAT:
                continue
            action = q.get("data", "").split(":")[0]
            try:
                bot.tg("answerCallbackQuery", callback_query_id=q["id"],
                       text="Tasdiqlandi" if action == "ok" else "Bekor qilindi")
            except Exception:
                pass
            if action in ("ok", "no"):
                if offset:
                    bot.tg("getUpdates", offset=offset, timeout=0)
                return action
    if offset:
        bot.tg("getUpdates", offset=offset, timeout=0)
    return None


def run_slot(slot):
    t_pub = slot_datetime(slot)
    t_ask = t_pub - ASK_BEFORE
    path = pick_story(slot)
    story = json.load(open(path, encoding="utf-8"))
    out = os.path.join(HERE, "out", os.path.basename(path).replace(".json", ".mp4"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    print("story:", path, "publish at", t_pub)

    # 1) render (Mac voice when available, otherwise Edge TTS)
    args = [sys.executable, os.path.join(HERE, "story_video.py"), path, out]
    args.append("--mac-voice" if sys.platform == "darwin" else "")
    subprocess.run([a for a in args if a], check=True)

    # 2) ask 30 minutes before
    sleep_until(t_ask)
    cap = (f"🎬 {story['title']}\n\n📝 {story.get('desc', '')[:500]}\n\n"
           f"🕒 YouTube'ga {t_pub:%H:%M} da chiqadi.\n"
           f"❌ bosmasangiz, vaqtida avtomatik chiqadi.")
    kb = {"inline_keyboard": [[{"text": "✅ Tasdiqlash", "callback_data": "ok"},
                               {"text": "❌ Bekor qilish", "callback_data": "no"}]]}
    with open(out, "rb") as f:
        msg = bot.tg("sendVideo", files={"video": f}, chat_id=bot.CHAT, caption=cap[:1024],
                     supports_streaming="true", width="1080", height="1920", reply_markup=kb)
    mid = msg["message_id"]

    # 3) wait for an answer until publish time
    ans = wait_for_answer(mid, t_pub)
    try:
        bot.tg("editMessageReplyMarkup", chat_id=bot.CHAT, message_id=mid, reply_markup={"inline_keyboard": []})
    except Exception:
        pass
    if ans == "no":
        bot.say(f"❌ Bekor qilindi: {story['title']}", reply_to_message_id=mid)
        return
    sleep_until(t_pub)

    # 4) publish
    try:
        vid, status = bot.yt_upload(out, story)
    except Exception as e:
        bot.say(f"⚠️ YouTube'ga yuklab bo'lmadi: {e}\n\nQo'lda yuklash uchun:\n\nSARLAVHA:\n{story['title']}"
                f"\n\nTAVSIF:\n{bot.description(story)}", reply_to_message_id=mid)
        raise
    how = "tasdiqlangan" if ans == "ok" else "javob bo'lmagani uchun avtomatik"
    bot.say(f"✅ Chiqdi ({how})\n🎬 {story['title']}\n🔗 https://youtube.com/shorts/{vid}\n🔒 Holat: {status}",
            reply_to_message_id=mid)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "slot":
        run_slot(sys.argv[2])
    elif len(sys.argv) >= 2 and sys.argv[1] == "next":
        for s in SLOTS:
            print(s, pick_story(s))
    else:
        sys.exit(__doc__)
