import csv
import json
import os
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request

try:
    from user_agents import parse as ua_parse
    UA_LIB = True
except ImportError:
    UA_LIB = False

app = Flask(__name__)

LOG_FILE = os.path.join(os.path.dirname(__file__), "logs", "requests.csv")

# Known bot/crawler user-agent substrings (case-insensitive)
BOT_UA_PATTERNS = [
    "bot", "crawl", "spider", "scrape", "wget", "curl", "python-requests",
    "httpx", "scrapy", "mechanize", "libwww", "java/", "go-http-client",
    "gptbot", "claudebot", "anthropic", "ccbot", "petalbot", "semrush",
    "ahrefsbot", "mj12bot", "dotbot", "rogerbot", "baiduspider",
    "googlebot", "bingbot", "yandexbot", "duckduckbot",
]

POSTS = [
    {
        "slug": "rough-tuesday",
        "title": "rough tuesday tbh",
        "date": "May 6, 2026",
        "preview": "woke up late, missed the 8am bus, had to speed-walk to class in the rain. my shoes are still damp...",
        "body": """<p>woke up late, missed the 8am bus, had to speed-walk to class in the rain. my shoes are still damp as i'm writing this at 11pm. not my finest moment.</p>
<p>lecture was fine. took notes but honestly my brain was half somewhere else the whole time. kept thinking about the text i sent yesterday that still hasn't been replied to. maybe i'm overthinking it. probably overthinking it.</p>
<p>lunch was good at least — the dining hall had that lemon pasta i like. small wins.</p>
<p>spent the afternoon at the library trying to read for my ethics class. got through maybe 20 pages before i gave up and watched youtube for an hour. very productive. very adult behavior.</p>
<p>called mom on the walk home. she asked if i was eating enough vegetables. i said yes. (i am not eating enough vegetables.)</p>""",
    },
    {
        "slug": "found-a-coffee-spot",
        "title": "found a new coffee spot and it might change my life",
        "date": "May 3, 2026",
        "preview": "okay so there's this tiny café two blocks from campus that i somehow never noticed...",
        "body": """<p>okay so there's this tiny café two blocks from campus that i somehow never noticed until yesterday. it's called <em>Groundwork</em> and it has exactly four tables, mismatched chairs, and a cat named Biscuit who sits by the register.</p>
<p>i got an oat milk latte and it was genuinely one of the best things i've had in weeks. not like, objectively amazing, but the vibe was so good. lo-fi music, no one on their laptops being loud, just quiet and warm.</p>
<p>i ended up staying two hours and actually finished the chapter i'd been putting off. something about the change of scenery just works for my brain.</p>
<p>going back tomorrow. might become a regular. might name my firstborn Biscuit. who knows.</p>""",
    },
    {
        "slug": "weekend-trip-michigan",
        "title": "quick weekend in michigan",
        "date": "Apr 27, 2026",
        "preview": "drove up to traverse city with a couple friends for the weekend. needed to get out of the city so bad...",
        "body": """<p>drove up to traverse city with a couple friends for the weekend. needed to get out of the city so bad — we've all been stuck in finals-prep mode for weeks and were starting to go a little insane.</p>
<p>the drive up took about four hours. we listened to a podcast about cults for two of those hours and honestly it made the time fly by.</p>
<p>stayed in this little Airbnb that had a wood-burning fireplace and a deck that looked out over the water. we made pasta the first night and sat outside until like 1am just talking. i forgot how good it feels to not look at your phone for a few hours.</p>
<p>saturday we went to the beach even though it was still pretty cold. walked along the shore, found some cool rocks. got cherry pie from a bakery in town. it was perfect.</p>
<p>came back sunday feeling actually human again. already want to go back.</p>""",
    },
    {
        "slug": "insomnia-again",
        "title": "3am and i can't sleep again",
        "date": "Apr 22, 2026",
        "preview": "it's 3:17am. i've been lying in bed for two hours. brain won't stop...",
        "body": """<p>it's 3:17am. i've been lying in bed for two hours. brain won't stop doing that thing where it replays every slightly embarrassing thing i've ever done in chronological order.</p>
<p>tonight's feature presentation: the time in 7th grade when i pronounced "hyperbole" as "hyper-bowl" in front of the whole class. why. why is this the thing my brain chose tonight.</p>
<p>i made chamomile tea. it helped a little. now i'm sitting at my desk in the dark writing this which probably isn't helping me sleep but at least i'm doing something.</p>
<p>i've been more anxious lately in general. i think it's the end-of-semester stuff piling up. i have three assignments due next week and a group project where i'm pretty sure i'm doing 70% of the work. love that for me.</p>
<p>anyway. going to try to sleep again. wish me luck. (update from the morning: it worked eventually, woke up at 9 feeling weirdly okay)</p>""",
    },
    {
        "slug": "cooking-for-myself",
        "title": "i've been cooking actual meals and it's kind of healing",
        "date": "Apr 18, 2026",
        "preview": "for most of this year i was surviving on dining hall food and the occasional sad desk sandwich...",
        "body": """<p>for most of this year i was surviving on dining hall food and the occasional sad desk sandwich. last month i decided to actually try cooking real meals in my apartment and it's been really good for me in ways i didn't expect.</p>
<p>this week i made: roasted chicken thighs with garlic and lemon, a big pot of lentil soup that lasted four days, and scrambled eggs that were genuinely fluffy (the secret is lower heat and more butter than you think is reasonable).</p>
<p>there's something about cooking that quiets my brain in a way most things don't. you have to pay attention to what's in front of you. you can't really doom-scroll while you're chopping an onion. the stakes feel low enough to be relaxing but high enough to be engaging.</p>
<p>also it's just cheaper. and i know exactly what's in my food. and it tastes better. honestly don't know why i waited this long.</p>
<p>next goal: learn to make proper fried rice. my roommate says it's all about the wok and she's probably right.</p>""",
    },
    {
        "slug": "on-being-far-from-home",
        "title": "on being far from home",
        "date": "Apr 10, 2026",
        "preview": "my hometown is about 1,400 miles from here. i don't go back very often...",
        "body": """<p>my hometown is about 1,400 miles from here. i don't go back very often — flights are expensive, breaks are short, and there's always something here that "needs" my attention, even when it probably doesn't.</p>
<p>i've been thinking about home a lot this week. not sure why exactly. maybe because the weather's finally warming up and spring always makes me nostalgic. or maybe because my parents mentioned they're repainting my old room and it gave me this weird hollow feeling.</p>
<p>it's strange how homesickness doesn't really go away, it just... changes shape. freshman year it was acute and heavy. now it's more like a low hum. present but not overwhelming. sometimes i'll smell something — certain dish soap, a particular food — and get hit with it out of nowhere.</p>
<p>i talked to my little sister for two hours on sunday. she's in high school now and has opinions about everything and it was the best conversation i've had in weeks.</p>
<p>going home for a bit this summer. can't wait.</p>""",
    },
    {
        "slug": "book-recs-this-year",
        "title": "books i've actually finished this year (a short list)",
        "date": "Apr 4, 2026",
        "preview": "i'm not going to pretend i've been reading as much as i said i would. but here's what actually got finished...",
        "body": """<p>i'm not going to pretend i've been reading as much as i said i would at the start of the year. but here's what actually got finished:</p>
<p><strong>Never Let Me Go — Kazuo Ishiguro.</strong> Read this in like two days. Quietly devastating. Couldn't stop thinking about it for a week. If you know, you know.</p>
<p><strong>Slouching Towards Bethlehem — Joan Didion.</strong> Assigned for class but ended up being one of my favorites. Her sentences are so precise. Made me want to pay more attention to the world around me.</p>
<p><strong>The Buried Giant — Ishiguro again.</strong> Okay apparently i'm on an Ishiguro kick. This one's slower but the last 50 pages hit hard.</p>
<p><strong>On Earth We're Briefly Gorgeous — Ocean Vuong.</strong> This one i've actually been recommending to everyone. It's a letter from a son to his mother. I cried on the train reading it like a normal person.</p>
<p>currently mid-way through Demon Copperhead by Barbara Kingsolver and it's very good. will report back.</p>""",
    },
    {
        "slug": "gym-journey",
        "title": "six months of going to the gym (honest review)",
        "date": "Mar 29, 2026",
        "preview": "i started going to the gym in october mostly because i needed somewhere to put my anxiety...",
        "body": """<p>i started going to the gym in october mostly because i needed somewhere to put my anxiety. it was either that or adopt a dog, and my lease doesn't allow dogs.</p>
<p>for the first month i had absolutely no idea what i was doing. i would just pick a machine that looked unthreatening and stay on it for 30 minutes and then leave. very effective. very scientific.</p>
<p>around month two i started actually learning things — watching youtube videos, asking a friend who actually knows about lifting, not being embarrassed to use the beginner weights. game changer.</p>
<p>now, six months in: i'm going 3-4 times a week, i actually have a real routine, and i genuinely look forward to it most days. my sleep is better. my baseline anxiety is lower. i feel more capable in a general way that's kind of hard to explain.</p>
<p>it's not about how i look. it's more that i feel like i'm in my body in a way i wasn't before. hard to articulate. but yeah — 10/10 would recommend just going and figuring it out as you go.</p>""",
    },
    {
        "slug": "friend-moved-away",
        "title": "my best friend moved to seattle",
        "date": "Mar 20, 2026",
        "preview": "she got a job offer she couldn't say no to. we all knew it was coming...",
        "body": """<p>she got a job offer she couldn't say no to. we all knew it was coming — it was a great opportunity and of course she took it — but knowing something is coming doesn't really soften it when it actually happens.</p>
<p>we've been close since sophomore year. she's one of those people who makes you feel like the smartest, funniest version of yourself. every city she's lived in, i've had a reason to visit. now that reason is seattle.</p>
<p>we had a long dinner the night before she left. we talked about everything and nothing, the way you do when you know you're trying to stretch time. then i helped her load the last boxes into her car and we hugged for too long in the parking lot.</p>
<p>she called me from the road the next day and we talked for most of her drive through Montana. so maybe the distance doesn't change as much as i feared.</p>
<p>still. miss her already.</p>""",
    },
    {
        "slug": "spring-in-the-city",
        "title": "finally — spring",
        "date": "Mar 14, 2026",
        "preview": "it hit 62 degrees yesterday and i swear the whole city changed overnight...",
        "body": """<p>it hit 62 degrees yesterday and i swear the whole city changed overnight. people were out everywhere — sitting on stoops, running in the park, eating lunch outside even though it was still kind of cold if you were in the shade. we've all been so deprived.</p>
<p>i went for a long walk after class with no destination, just wandered. ended up in a neighborhood i didn't know very well, found a bookstore i'd never been in, bought nothing but spent 45 minutes browsing. perfect afternoon.</p>
<p>there's something about the first real spring days that makes everything feel more possible. like the world is rebooting. i always feel more like myself in spring.</p>
<p>looking forward to: eating outside, longer evenings, not wearing a coat, farmers markets starting up again, all of it.</p>""",
    },
]

ARTICLES = {p["slug"]: p for p in POSTS}


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def _ensure_log():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "ip", "method", "path", "status_code",
                "user_agent", "is_bot", "bot_reason", "referer",
                "accept_language", "response_ms",
            ])


def _classify_bot(ua_string: str) -> tuple[bool, str]:
    """Return (is_bot, reason). Checks known UA patterns then user-agents lib."""
    ua_lower = ua_string.lower()
    for pattern in BOT_UA_PATTERNS:
        if pattern in ua_lower:
            return True, f"ua_pattern:{pattern}"
    if UA_LIB:
        parsed = ua_parse(ua_string)
        if parsed.is_bot:
            return True, "ua_lib:is_bot"
    return False, ""


def _log_request(response):
    _ensure_log()
    ua_string = request.headers.get("User-Agent", "")
    is_bot, bot_reason = _classify_bot(ua_string)

    elapsed_ms = round((time.time() - request.environ.get("_start_time", time.time())) * 1000, 1)

    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now(timezone.utc).isoformat(),
            request.remote_addr,
            request.method,
            request.path,
            response.status_code,
            ua_string,
            is_bot,
            bot_reason,
            request.headers.get("Referer", ""),
            request.headers.get("Accept-Language", ""),
            elapsed_ms,
        ])
    return response


@app.before_request
def _stamp_start():
    request.environ["_start_time"] = time.time()


app.after_request(_log_request)


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html", posts=POSTS)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/archive")
def archive():
    return render_template("index.html", posts=POSTS)


@app.route("/posts/<slug>")
def post(slug):
    data = ARTICLES.get(slug)
    if not data:
        return "Not found", 404
    return render_template("article.html", **data)


@app.route("/robots.txt")
def robots():
    content = (
        "User-agent: *\n"
        "Disallow: /secret\n"
        "Disallow: /dashboard\n"
        "Disallow: /api/\n"
    )
    return app.response_class(content, mimetype="text/plain")


# ---------------------------------------------------------------------------
# Honeypot / trap
# ---------------------------------------------------------------------------

@app.route("/secret")
def secret():
    # Any visit here is flagged — it's hidden from humans and disallowed in robots.txt
    return render_template("secret.html"), 200


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.route("/dashboard")
def dashboard():
    rows = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    rows.reverse()  # newest first

    total = len(rows)
    bots = sum(1 for r in rows if r["is_bot"] == "True")
    honeypot_hits = sum(1 for r in rows if r["path"] == "/secret")
    robots_ignored = sum(
        1 for r in rows
        if r["path"] in ("/secret", "/dashboard", "/api/")
        and r["is_bot"] == "True"
    )

    stats = {
        "total_requests": total,
        "bot_requests": bots,
        "human_requests": total - bots,
        "honeypot_hits": honeypot_hits,
        "robots_txt_violations": robots_ignored,
    }
    return render_template("dashboard.html", rows=rows[:200], stats=stats)


@app.route("/api/logs")
def api_logs():
    rows = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    return jsonify(rows)


if __name__ == "__main__":
    _ensure_log()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", debug=False, port=port)
