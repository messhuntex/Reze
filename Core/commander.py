"""
commander.py — Universal Android App Controller (No Root)
=========================================================
Handles voice commands for ANY Android app using:
  1. Deep Links  (YouTube search, WhatsApp, Spotify, Maps …)
  2. Android Intents via `am start`
  3. Termux:API for system controls
  4. termux-open-url fallback

Master: Master Jit | Assistant: Reze
"""

import subprocess
import json
import re
import urllib.parse
import datetime
from core.logger import log


# ─────────────────────────────────────────────────────────────────
#  APP REGISTRY
#  Add any app here → it becomes instantly voice-controllable
#  Keys: pkg, launch, search (optional), message (optional),
#        navigate (optional), aliases
# ─────────────────────────────────────────────────────────────────
APP_REGISTRY = {

    # ── Video / Streaming ──────────────────────────────────────
    "youtube": {
        "pkg":    "com.google.android.youtube",
        "launch": "com.google.android.youtube/com.google.android.apps.youtube.app.WatchWhileActivity",
        "search": "https://www.youtube.com/results?search_query={query}",
        "aliases": ["yt", "tube"],
    },
    "netflix": {
        "pkg":    "com.netflix.mediaclient",
        "launch": "com.netflix.mediaclient/.ui.launch.UIWebViewActivity",
        "search": "https://www.netflix.com/search?q={query}",
        "aliases": [],
    },
    "spotify": {
        "pkg":    "com.spotify.music",
        "launch": "com.spotify.music/.MainActivity",
        "search": "spotify:search:{query}",
        "aliases": ["music"],
    },
    "amazon prime": {
        "pkg":    "com.amazon.avod.thirdpartyclient",
        "launch": "com.amazon.avod.thirdpartyclient/.LaunchActivity",
        "aliases": ["prime", "prime video"],
    },
    "hotstar": {
        "pkg":    "in.startv.hotstar",
        "launch": "in.startv.hotstar/.HomeActivity",
        "aliases": ["disney", "disney hotstar"],
    },
    "vlc": {
        "pkg":    "org.videolan.vlc",
        "launch": "org.videolan.vlc/.StartActivity",
        "aliases": [],
    },

    # ── Messaging ──────────────────────────────────────────────
    "whatsapp": {
        "pkg":    "com.whatsapp",
        "launch": "com.whatsapp/.Main",
        "message": "https://api.whatsapp.com/send?phone={number}&text={text}",
        "aliases": ["wa", "whats app"],
    },
    "telegram": {
        "pkg":    "org.telegram.messenger",
        "launch": "org.telegram.messenger/.DefaultIcon",
        "message": "tg://msg?to={number}&text={text}",
        "aliases": ["tg"],
    },
    "instagram": {
        "pkg":    "com.instagram.android",
        "launch": "com.instagram.android/.activity.MainTabActivity",
        "aliases": ["insta", "ig"],
    },
    "twitter": {
        "pkg":    "com.twitter.android",
        "launch": "com.twitter.android/.StartActivity",
        "search": "twitter://search?query={query}",
        "aliases": ["x"],
    },
    "facebook": {
        "pkg":    "com.facebook.katana",
        "launch": "com.facebook.katana/.LoginActivity",
        "aliases": ["fb"],
    },
    "snapchat": {
        "pkg":    "com.snapchat.android",
        "launch": "com.snapchat.android/.LandingPageActivity",
        "aliases": ["snap"],
    },
    "discord": {
        "pkg":    "com.discord",
        "launch": "com.discord/.app.AppActivity$Main",
        "aliases": [],
    },
    "gmail": {
        "pkg":    "com.google.android.gm",
        "launch": "com.google.android.gm/.ConversationListActivityGmail",
        "compose": "googlegmail://co?to={to}&subject={subject}&body={body}",
        "aliases": ["email", "mail"],
    },

    # ── Browsers ───────────────────────────────────────────────
    "chrome": {
        "pkg":    "com.android.chrome",
        "launch": "com.android.chrome/com.google.android.apps.chrome.Main",
        "search": "https://www.google.com/search?q={query}",
        "url":    "{url}",
        "aliases": ["browser", "google chrome"],
    },
    "brave": {
        "pkg":    "com.brave.browser",
        "launch": "com.brave.browser/com.google.android.apps.chrome.Main",
        "search": "https://search.brave.com/search?q={query}",
        "aliases": [],
    },
    "firefox": {
        "pkg":    "org.mozilla.firefox",
        "launch": "org.mozilla.firefox/.App",
        "aliases": ["mozilla"],
    },

    # ── Maps / Navigation ──────────────────────────────────────
    "google maps": {
        "pkg":    "com.google.android.apps.maps",
        "launch": "com.google.android.apps.maps/com.google.android.maps.MapsActivity",
        "navigate": "google.navigation:q={query}&mode=d",
        "search":   "geo:0,0?q={query}",
        "aliases": ["maps", "navigation", "gps"],
    },
    "ola": {
        "pkg":    "com.olacabs.customer",
        "launch": "com.olacabs.customer/.ui.activity.HomeActivity",
        "aliases": ["ola cab"],
    },
    "uber": {
        "pkg":    "com.ubercab",
        "launch": "com.ubercab/.app.RootActivity",
        "aliases": [],
    },

    # ── Shopping ───────────────────────────────────────────────
    "amazon": {
        "pkg":    "in.amazon.mShop.android.shopping",
        "launch": "in.amazon.mShop.android.shopping/.App",
        "search": "https://www.amazon.in/s?k={query}",
        "aliases": ["amazon shopping", "amazon india"],
    },
    "flipkart": {
        "pkg":    "com.flipkart.android",
        "launch": "com.flipkart.android/.activity.HomeActivity",
        "search": "https://www.flipkart.com/search?q={query}",
        "aliases": [],
    },
    "meesho": {
        "pkg":    "com.meesho.supply",
        "launch": "com.meesho.supply/.ui.activity.SplashActivity",
        "aliases": [],
    },
    "play store": {
        "pkg":    "com.android.vending",
        "launch": "com.android.vending/.AssetBrowserActivity",
        "search": "market://search?q={query}",
        "aliases": ["google play", "playstore", "app store"],
    },

    # ── Payments ───────────────────────────────────────────────
    "gpay": {
        "pkg":    "com.google.android.apps.nbu.paisa.user",
        "launch": "com.google.android.apps.nbu.paisa.user/.ui.home.HomeActivity",
        "aliases": ["google pay"],
    },
    "phonepe": {
        "pkg":    "com.phonepe.app",
        "launch": "com.phonepe.app/.ui.activity.HomeActivity",
        "aliases": ["phone pe"],
    },
    "paytm": {
        "pkg":    "net.one97.paytm",
        "launch": "net.one97.paytm/.AliPayMainActivity",
        "aliases": [],
    },

    # ── Productivity ───────────────────────────────────────────
    "calendar": {
        "pkg":    "com.google.android.calendar",
        "launch": "com.google.android.calendar/.LaunchActivity",
        "aliases": ["google calendar"],
    },
    "clock": {
        "pkg":    "com.google.android.deskclock",
        "launch": "com.google.android.deskclock/.DeskClock",
        "aliases": ["alarm", "timer", "stopwatch"],
    },
    "camera": {
        "pkg":    "com.android.camera2",
        "launch": "com.android.camera2/.CameraActivity",
        "aliases": ["photo", "selfie"],
    },
    "gallery": {
        "pkg":    "com.google.android.apps.photos",
        "launch": "com.google.android.apps.photos/.home.HomeActivity",
        "aliases": ["photos", "pictures"],
    },
    "calculator": {
        "pkg":    "com.google.android.calculator",
        "launch": "com.google.android.calculator/.Calculator",
        "aliases": ["calc"],
    },
    "settings": {
        "pkg":    "com.android.settings",
        "launch": "com.android.settings/.Settings",
        "aliases": ["android settings", "phone settings"],
    },
    "files": {
        "pkg":    "com.google.android.apps.nbu.files",
        "launch": "com.google.android.apps.nbu.files/.home.HomeActivity",
        "aliases": ["file manager", "my files"],
    },
    "notes": {
        "pkg":    "com.google.android.keep",
        "launch": "com.google.android.keep/.activities.BrowseActivity",
        "aliases": ["keep", "google keep"],
    },
    "contacts": {
        "pkg":    "com.google.android.contacts",
        "launch": "com.google.android.contacts/.activities.PeopleActivity",
        "aliases": ["phone contacts"],
    },
    "phone": {
        "pkg":    "com.google.android.dialer",
        "launch": "com.google.android.dialer/.extensions.GoogleDialtactsActivity",
        "aliases": ["dialer"],
    },
    "messages": {
        "pkg":    "com.google.android.apps.messaging",
        "launch": "com.google.android.apps.messaging/.ui.ConversationListActivity",
        "aliases": ["sms app", "text messages"],
    },

    # ── Food ───────────────────────────────────────────────────
    "swiggy": {
        "pkg":    "in.swiggy.android",
        "launch": "in.swiggy.android/.app.ui.SplashActivity",
        "aliases": ["food delivery"],
    },
    "zomato": {
        "pkg":    "com.application.zomato",
        "launch": "com.application.zomato/.activities.NewSplashActivity",
        "aliases": [],
    },

    # ── Meetings ───────────────────────────────────────────────
    "zoom": {
        "pkg":    "us.zoom.videomeetings",
        "launch": "us.zoom.videomeetings/.mm.WelcomeActivity",
        "aliases": [],
    },
    "meet": {
        "pkg":    "com.google.android.apps.meetings",
        "launch": "com.google.android.apps.meetings/.MainActivity",
        "aliases": ["google meet"],
    },
}


# Build alias lookup once at import time
def _build_lookup():
    table = {}
    for name, info in APP_REGISTRY.items():
        table[name] = info
        for alias in info.get("aliases", []):
            table[alias] = info
    return table

APP_LOOKUP = _build_lookup()


# ─────────────────────────────────────────────────────────────────
class AndroidCommander:

    def __init__(self):
        self._has_termux_api = self._check_termux_api()

    # ─── Main dispatcher ──────────────────────────────────────
    def try_handle(self, text: str) -> str:
        t = text.lower().strip()

        # 1. YouTube search / play
        q = self._match_youtube(t)
        if q is not None:
            return self._youtube_search(q) if q else self._open_app_by_name("youtube")

        # 2. WhatsApp message
        wa = self._match_whatsapp(t)
        if wa:
            return self._whatsapp_send(wa["contact"], wa["message"])

        # 3. Generic app search: "search <app> for <query>"
        m = re.search(r'search\s+([\w\s]+?)\s+for\s+(.+)', t)
        if m:
            return self._app_search(m.group(1).strip(), m.group(2).strip())

        # 4. Navigate / directions
        m = re.search(r'(?:navigate|directions?|take me|go)\s+to\s+(.+)', t)
        if m:
            return self._navigate(m.group(1).strip())

        # 5. Open app
        m = re.search(r'open\s+([\w\s]+?)(?:\s+app)?$', t)
        if m:
            return self._open_app_by_name(m.group(1).strip())

        # 6. Send SMS
        m = re.search(r'send\s+(?:message|sms|text)\s+(?:to\s+)?([\w\s]+?)\s+saying\s+(.+)', t)
        if m:
            return self._send_sms(m.group(1).strip(), m.group(2).strip())

        # 7. Call
        m = re.search(r'^call\s+([\w\s\+\d]+)', t)
        if m:
            return self._make_call(m.group(1).strip())

        # 8. System shortcuts
        if re.search(r'\btime\b', t):           return self._get_time()
        if re.search(r'\bdate\b|\btoday\b', t): return self._get_date()
        if re.search(r'battery|charge level', t): return self._get_battery()
        if re.search(r'torch off|flashlight off|light off', t): return self._torch(False)
        if re.search(r'torch|flashlight|light on', t): return self._torch(True)
        if re.search(r'volume up|louder', t):    return self._volume(8)
        if re.search(r'volume down|quieter|lower', t): return self._volume(3)
        if re.search(r'screenshot', t):          return self._screenshot()
        if re.search(r'wifi|wi-fi info', t):     return self._wifi_info()
        if re.search(r'location|where am i', t): return self._get_location()
        if re.search(r'vibrat', t):              return self._vibrate()
        if re.search(r'clipboard', t):           return self._get_clipboard()
        if re.search(r'notification', t):        return self._get_notifications()

        return ""  # not handled — AI Brain takes over

    # ═══════════════════════════════════════════════════════════
    #  YOUTUBE
    # ═══════════════════════════════════════════════════════════
    def _match_youtube(self, t: str):
        """Returns query string, '' for plain open, None if not a YouTube command."""
        patterns = [
            r'(?:search|find|look up|play)\s+(.+?)\s+on\s+youtube',
            r'youtube\s+(?:search|play|find)\s+(?:for\s+)?(.+)',
            r'search\s+youtube\s+(?:for\s+)?(.+)',
            r'open\s+youtube\s+(?:and\s+)?(?:search|play|find)\s+(?:for\s+)?(.+)',
        ]
        for p in patterns:
            m = re.search(p, t)
            if m:
                return m.group(1).strip()
        if re.search(r'^open\s+youtube$', t):
            return ''   # just open, no search
        return None

    def _youtube_search(self, query: str) -> str:
        encoded = urllib.parse.quote(query)
        url     = f"https://www.youtube.com/results?search_query={encoded}"
        self._open_url("com.google.android.youtube", url)
        return f"Searching YouTube for '{query}', Master Jit~"

    # ═══════════════════════════════════════════════════════════
    #  WHATSAPP
    # ═══════════════════════════════════════════════════════════
    def _match_whatsapp(self, t: str):
        patterns = [
            r'(?:send\s+)?whatsapp\s+(?:message\s+)?(?:to\s+)?([\w\s\+\d]+?)\s+(?:saying|say|that|:)\s+(.+)',
            r'message\s+([\w\s]+?)\s+on\s+whatsapp\s+(?:saying\s+)?(.+)',
            r'send\s+(?:a\s+)?whatsapp\s+(?:message\s+)?to\s+([\w\s\+\d]+?)\s+saying\s+(.+)',
        ]
        for p in patterns:
            m = re.search(p, t)
            if m:
                return {"contact": m.group(1).strip(), "message": m.group(2).strip()}
        return None

    def _whatsapp_send(self, contact: str, message: str) -> str:
        encoded = urllib.parse.quote(message)
        is_number = bool(re.match(r'^[\d\+\s\-]+$', contact))

        if is_number:
            number = re.sub(r'[\s\-]', '', contact)
            if not number.startswith('+'):
                number = '+91' + number   # default India country code — change if needed
            url = f"https://api.whatsapp.com/send?phone={number}&text={encoded}"
            self._open_url("com.whatsapp", url)
            return f"Opening WhatsApp to send '{message}' to {contact}, Master."
        else:
            # WhatsApp doesn't allow name-based deep links without Contacts API access.
            # Best we can do: open WhatsApp and tell the user the message to send.
            self._open_app_pkg("com.whatsapp")
            return (
                f"WhatsApp is open, Master. Find '{contact}' and send them: \"{message}\". "
                f"I can't auto-select by name — use a phone number for full automation~"
            )

    # ═══════════════════════════════════════════════════════════
    #  GENERIC APP SEARCH & OPEN
    # ═══════════════════════════════════════════════════════════
    def _app_search(self, app_name: str, query: str) -> str:
        info = self._find_app(app_name)
        if not info:
            return f"I don't have '{app_name}' in my registry yet, Master."

        encoded = urllib.parse.quote(query)

        if "search" in info:
            url = info["search"].replace("{query}", encoded)
            self._open_url(info["pkg"], url)
            return f"Searching {app_name} for '{query}', Master~"

        # No search deep link — just open
        self._open_app_pkg(info["pkg"])
        return f"Opened {app_name}. No search shortcut available for it, Master."

    def _open_app_by_name(self, name: str) -> str:
        info = self._find_app(name)
        if info:
            self._open_app_pkg(info["pkg"])
            return f"Opening {name}, Master."
        return f"I couldn't find '{name}' in my app list, Master."

    def _find_app(self, name: str):
        name = name.lower().strip()
        if name in APP_LOOKUP:
            return APP_LOOKUP[name]
        for key, info in APP_LOOKUP.items():
            if name in key or key in name:
                return info
        return None

    # ─── Low-level launchers ───────────────────────────────────
    def _open_url(self, pkg: str, url: str):
        """Open deep link / URL — Android routes it to the correct app."""
        try:
            subprocess.run(
                ["am", "start",
                 "-a", "android.intent.action.VIEW",
                 "-d", url,
                 "--package", pkg],
                capture_output=True, timeout=5
            )
        except Exception:
            try:
                subprocess.run(["termux-open-url", url], timeout=5)
            except Exception as e:
                log.debug(f"open_url fallback failed: {e}")

    def _open_app_pkg(self, pkg: str):
        """Launch an app by package name using monkey (always works, no root)."""
        try:
            subprocess.run(
                ["monkey", "-p", pkg, "-c",
                 "android.intent.category.LAUNCHER", "1"],
                capture_output=True, timeout=5
            )
        except Exception as e:
            log.debug(f"monkey launch failed for {pkg}: {e}")

    # ═══════════════════════════════════════════════════════════
    #  NAVIGATION
    # ═══════════════════════════════════════════════════════════
    def _navigate(self, destination: str) -> str:
        encoded = urllib.parse.quote(destination)
        self._open_url(
            "com.google.android.apps.maps",
            f"google.navigation:q={encoded}&mode=d"
        )
        return f"Starting navigation to {destination}, Master."

    # ═══════════════════════════════════════════════════════════
    #  SMS / CALLS
    # ═══════════════════════════════════════════════════════════
    def _send_sms(self, contact: str, message: str) -> str:
        try:
            subprocess.run(
                ["termux-sms-send", "-n", contact, message],
                capture_output=True, timeout=10
            )
            return f"SMS sent to {contact}, Master."
        except Exception as e:
            log.debug(f"SMS error: {e}")
            return f"Couldn't send SMS to {contact}."

    def _make_call(self, contact: str) -> str:
        try:
            subprocess.run(["termux-telephony-call", contact], timeout=5)
            return f"Calling {contact} now, Master."
        except Exception as e:
            return f"Call failed: {e}"

    # ═══════════════════════════════════════════════════════════
    #  SYSTEM CONTROLS (Termux:API)
    # ═══════════════════════════════════════════════════════════
    def _get_time(self) -> str:
        return f"It's {datetime.datetime.now().strftime('%I:%M %p')}, Master Jit."

    def _get_date(self) -> str:
        return f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}, Master."

    def _get_battery(self) -> str:
        try:
            r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=5)
            d = json.loads(r.stdout)
            lvl  = d.get("percentage", "?")
            plug = "charging" if d.get("status", "").lower() in ["charging", "full"] else "not charging"
            return f"Battery at {lvl}%, {plug}, Master."
        except Exception:
            return "Couldn't read battery status."

    def _torch(self, on: bool) -> str:
        try:
            subprocess.run(["termux-torch", "on" if on else "off"], timeout=3)
            return f"Flashlight {'on' if on else 'off'}, Master."
        except Exception:
            return "Flashlight unavailable."

    def _volume(self, level: int) -> str:
        try:
            subprocess.run(["termux-volume", "music", str(level)], timeout=3)
            return f"Volume {'up' if level > 5 else 'down'}, Master."
        except Exception:
            return "Volume control unavailable."

    def _screenshot(self) -> str:
        try:
            path = "/storage/emulated/0/Pictures/reze_screenshot.png"
            subprocess.run(["termux-screenshot", "-f", path], timeout=5)
            return "Screenshot saved to Pictures, Master."
        except Exception:
            return "Screenshot unavailable."

    def _wifi_info(self) -> str:
        try:
            r = subprocess.run(["termux-wifi-connectioninfo"], capture_output=True, text=True, timeout=5)
            d = json.loads(r.stdout)
            return f"Connected to {d.get('ssid','?')}, IP {d.get('ip','?')}."
        except Exception:
            return "Couldn't read Wi-Fi info."

    def _get_location(self) -> str:
        try:
            r = subprocess.run(["termux-location"], capture_output=True, text=True, timeout=15)
            d = json.loads(r.stdout)
            return f"You're at {round(d.get('latitude',0),4)}, {round(d.get('longitude',0),4)}, Master."
        except Exception:
            return "Couldn't get your location."

    def _vibrate(self) -> str:
        try:
            subprocess.run(["termux-vibrate", "-d", "500"], timeout=3)
            return "Vibrating!"
        except Exception:
            return "Vibration unavailable."

    def _get_clipboard(self) -> str:
        try:
            r = subprocess.run(["termux-clipboard-get"], capture_output=True, text=True, timeout=3)
            c = r.stdout.strip()
            return f"Clipboard says: {c}" if c else "Clipboard is empty."
        except Exception:
            return "Couldn't read clipboard."

    def _get_notifications(self) -> str:
        try:
            r = subprocess.run(["termux-notification-list"], capture_output=True, text=True, timeout=5)
            notifs = json.loads(r.stdout)
            if not notifs:
                return "No notifications, Master."
            apps = list({n.get("packageName","?").split(".")[-1] for n in notifs[:5]})
            return f"{len(notifs)} notifications from: {', '.join(apps)}."
        except Exception:
            return "Couldn't fetch notifications."

    def _check_termux_api(self) -> bool:
        return subprocess.run(["which", "termux-battery-status"], capture_output=True).returncode == 0
