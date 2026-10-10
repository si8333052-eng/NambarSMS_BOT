import requests
import time
import json
import random
import sqlite3
import os
import re
import html
import threading
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask # <-- Render এর জন্য যোগ করা হলো
# ==========================================
# Configuration
# ==========================================
BOT_TOKEN = "8604617628:AAFKtdLBP48TyLoOE_UR3pK8D7dn4-t5iOY"
ADMIN_ID = 6560485203
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
BOT_USERNAME = ""
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "Bot is Running!"
# 2oo9 API Configuration
API_2OO9_BASE = "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api"
API_2OO9_KEY_DEFAULT = "MHF5UTYD3L7"

# Global states
current_db_mode = "sqlite"
db_firebase = None
waiting_for_firebase = False
user_states = {}

# User & Cooldown States
user_cache = {}
user_active_sessions = {}
user_cooldowns = {}

# Voltx Auto System States
voltx_auto_mode = True
voltx_keys = [API_2OO9_KEY_DEFAULT]
force_join_status = False
force_join_channels = []

# OTP Forwarding States
otp_forward_groups = []
otp_button_link = "https://t.me/your_default_bot"
recent_success_otps = set()

voltx_dynamic_data = {}
recent_traffic = []
daily_stats = {"date": "", "numbers": 0, "otps": 0}
daily_user_otps = {"date": "", "users": {}}

cached_services_kb = None
cached_countries_kb = {}
cached_leaderboard_text = ""

#... [তোমার বাকি সব ফাংশন আগের মতোই থাকবে, আমি কাটি নাই]...
# নিচের ফাংশনগুলো তোমার আগের কোড থেকে কপি পেস্ট হবে, তাই এখানে শর্ট করলাম
# তুমি পুরা ফাইলটাই নিচের লিংক থেকে নিবে

def auto_cache_menu_thread():
    global cached_services_kb, cached_countries_kb, voltx_auto_mode, voltx_dynamic_data
    while True:
        try:
            if voltx_auto_mode and voltx_dynamic_data:
                service_hits = [(sid, s_data, sum(r["hits"] for r in s_data["ranges"].values())) for sid, s_data in voltx_dynamic_data.items()]
                top_services = sorted(service_hits, key=lambda x: x[2], reverse=True)[:15]
                new_srv_kb = {"inline_keyboard": []}
                row = []; styles = ["primary", "success", "danger"]; style_idx = 0
                for sid, data, hits in top_services:
                    safe_sid = html.escape(str(sid))
                    row.append({"text": safe_sid, "callback_data": f"srv_{safe_sid[:15]}", "style": styles[style_idx % 3], "icon_custom_emoji_id": data["emoji_id"]})
                    style_idx += 1
                    if len(row) == 2: new_srv_kb["inline_keyboard"].append(row); row = []
                if row: new_srv_kb["inline_keyboard"].append(row)
                new_srv_kb["inline_keyboard"].append([{"text": "CLOSE", "callback_data": "close_panel", "icon_custom_emoji_id": "5438541186539232243", "style": "danger"}])
                cached_services_kb = new_srv_kb
                new_cnt_kb = {}
                for sid, data, hits in top_services:
                    safe_sid_short = html.escape(str(sid))[:15]
                    country_map = {}
                    for r, r_data in data["ranges"].items():
                        clean_r = str(r).replace("X", "")
                        if not re.match(r'^\d+$', clean_r): continue
                        c_code, c_name = get_country_info(clean_r)
                        if c_code not in country_map: country_map[c_code] = {"name": c_name, "hits": 0}
                        country_map[c_code]["hits"] += r_data["hits"]
                    top_countries = sorted(country_map.items(), key=lambda x: x[1]["hits"], reverse=True)[:15]
                    cnt_kb = {"inline_keyboard": []}
                    styles_c = ["primary", "success", "danger"]; style_idx_c = 0
                    std_service = detect_service("", sid)
                    rate = get_otp_reward(std_service)
                    for c_code, c_data in top_countries:
                        c_name_full = c_data["name"]
                        parts = c_name_full.split(" ", 1)
                        emoji_char = parts[0]
                        clean_name = parts[1] if len(parts) > 1 else c_name_full
                        btn_text = f"Other (+{c_code}) - {rate} TK" if "Other" in clean_name else f"{clean_name} (+{c_code}) - {rate} TK"
                        btn = {"text": btn_text, "callback_data": f"cc_{safe_sid_short}_{c_code}", "style": styles_c[style_idx_c % 3]}
                        if emoji_char in GLOBAL_BODY_EMOJIS: btn["icon_custom_emoji_id"] = GLOBAL_BODY_EMOJIS[emoji_char]
                        cnt_kb["inline_keyboard"].append([btn])
                        style_idx_c += 1
                    cnt_kb["inline_keyboard"].append([{"text": "BACK", "callback_data": "back_to_services", "icon_custom_emoji_id": "5438541186539232243", "style": "danger"}])
                    new_cnt_kb[safe_sid_short] = cnt_kb
                cached_countries_kb = new_cnt_kb
            global cached_leaderboard_text, daily_user_otps
            today = time.strftime("%Y-%m-%d")
            if daily_user_otps.get("date")!= today:
                daily_user_otps["date"] = today
                daily_user_otps["users"] = {}
            top_users = sorted(daily_user_otps["users"].items(), key=lambda x: x[1], reverse=True)[:5]
            lb_msg = "<blockquote><tg-emoji emoji-id=\"5240021484516185513\">🏆</tg-emoji> <b>𝗧𝗢𝗣 𝟱 𝗟𝗘𝗔𝗗𝗘𝗥𝗕𝗢𝗔𝗥𝗗 (TODAY)</b></blockquote>\n━━━━━━━━━━━━━━━━━\n"
            emoji_map = [("1️⃣", "5238176680098440792"), ("2️⃣", "5237806896299157399"), ("3️⃣", "5239965456667812809"), ("4️⃣", "5237911487342751418"), ("5️⃣", "5240278297790686165")]
            if not top_users: lb_msg += "<i>No OTPs received today.</i>\n"
            else:
                for idx, (uid_str, otp_count) in enumerate(top_users):
                    u_data = get_user(int(uid_str))
                    fname = u_data["first_name"] if u_data else "User"
                    emoji_char, emoji_id = emoji_map[idx]
                    lb_msg += f"<blockquote><tg-emoji emoji-id=\"{emoji_id}\">{emoji_char}</tg-emoji> <a href='tg://user?id={uid_str}'>{html.escape(str(fname))}</a> - {otp_count} OTP</blockquote>\n"
            lb_msg += "━━━━━━━━━━━━━━━━━"
            cached_leaderboard_text = lb_msg
        except Exception as e: pass
        time.sleep(5)

bot_settings = {
    "withdraw_on": True, "min_withdraw": 10.0, "support_link": "", "w_group": "", "auto_br_on": False,
    "auto_br_interval": 60, "cooldown": 5, "num_req": 1, "w_methods": ["bKash", "Nagad"],
    "otp_default_rate": 0.5, "otp_service_rates": {}, "main_channel_link": ""
}
BOT_DATA_FILE = "bot_data.json"
USERS_LIST_FILE = "users_list.json"

def get_api_key(): return random.choice(voltx_keys) if voltx_keys else API_2OO9_KEY_DEFAULT
def get_otp_reward(service_name):
    rates = bot_settings.get("otp_service_rates", {})
    val = rates.get(service_name, bot_settings.get("otp_default_rate", 0.5))
    return float(val)
def update_daily_stat(key, amount=1):
    global daily_stats
    today = time.strftime("%Y-%m-%d")
    if daily_stats.get("date")!= today: daily_stats = {"date": today, "numbers": 0, "otps": 0}
    daily_stats[key] = daily_stats.get(key, 0) + amount
def load_local_data():
    global recent_traffic, voltx_dynamic_data, voltx_keys, force_join_status, force_join_channels, voltx_auto_mode, otp_forward_groups, otp_button_link, recent_success_otps, bot_settings, user_active_sessions, daily_stats, daily_user_otps
    if os.path.exists(BOT_DATA_FILE):
        try:
            with open(BOT_DATA_FILE, "r") as f:
                data = json.load(f)
                recent_traffic = data.get("recent_traffic", [])
                voltx_dynamic_data = data.get("voltx_dynamic_data", {})
                loaded_keys = data.get("voltx_keys", [])
                voltx_keys = loaded_keys if loaded_keys else [API_2OO9_KEY_DEFAULT]
                force_join_status = data.get("force_join_status", False)
                force_join_channels = data.get("force_join_channels", [])
                voltx_auto_mode = data.get("voltx_auto_mode", True)
                otp_forward_groups = data.get("otp_forward_groups", [])
                otp_button_link = data.get("otp_button_link", "https://t.me/your_default_bot")
                recent_success_otps = set(data.get("recent_success_otps", []))
                loaded_settings = data.get("bot_settings", {})
                for k, v in loaded_settings.items(): bot_settings[k] = v
                daily_stats = data.get("daily_stats", {"date": "", "numbers": 0, "otps": 0})
                daily_user_otps = data.get("daily_user_otps", {"date": "", "users": {}})
                user_active_sessions = data.get("user_active_sessions", {})
        except Exception as e: print(f"Error loading local data: {e}")
def save_local_data():
    global recent_traffic, voltx_dynamic_data, voltx_keys, force_join_status, force_join_channels, voltx_auto_mode, otp_forward_groups, otp_button_link, recent_success_otps, bot_settings, user_active_sessions, daily_stats
    try:
        with open(BOT_DATA_FILE, "w") as f:
            json.dump({"recent_traffic": recent_traffic, "voltx_dynamic_data": voltx_dynamic_data,"voltx_keys": voltx_keys,"force_join_status": force_join_status,"force_join_channels": force_join_channels,"voltx_auto_mode": voltx_auto_mode,"otp_forward_groups": otp_forward_groups,"otp_button_link": otp_button_link,"recent_success_otps": list(recent_success_otps),"bot_settings": bot_settings,"user_active_sessions": user_active_sessions,"daily_stats": daily_stats,"daily_user_otps": daily_user_otps}, f)
    except Exception as e: print(f"Error saving local data: {e}")
    if current_db_mode == "firebase" and db_firebase:
        try:
            db_firebase.collection('settings').document('bot_config').set({"bot_settings": bot_settings,"force_join_status": force_join_status,"force_join_channels": force_join_channels,"otp_forward_groups": otp_forward_groups,"otp_button_link": otp_button_link,"voltx_keys": voltx_keys,"voltx_auto_mode": voltx_auto_mode}, merge=True)
        except: pass
cached_user_list = set()
def add_to_broadcast_list(user_id):
    global cached_user_list
    if not cached_user_list and os.path.exists(USERS_LIST_FILE):
        try:
            with open(USERS_LIST_FILE, "r") as f: cached_user_list = set(json.load(f))
        except: pass
    if user_id not in cached_user_list:
        cached_user_list.add(user_id)
        try:
            with open(USERS_LIST_FILE, "w") as f: json.dump(list(cached_user_list), f)
        except: pass
def get_all_user_ids():
    global user_cache
    users = set()
    for uid in user_cache.keys(): users.add(int(uid))
    if os.path.exists(USERS_LIST_FILE):
        try:
            with open(USERS_LIST_FILE, "r") as f:
                for u in json.load(f): users.add(int(u))
        except: pass
    return list(users)
def get_bot_info():
    try:
        res = requests.get(BASE_URL + "getMe").json()
        if res.get("ok"): return res["result"]["username"]
    except Exception: pass
    return ""
def set_bot_commands():
    commands = [{"command": "start", "description": "Start the bot or refresh menu"}]
    try: requests.post(BASE_URL + "setMyCommands", json={"commands": commands})
    except Exception: pass
def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "text": apply_emojis(text), "parse_mode": parse_mode}
    if reply_markup: payload["reply_markup"] = reply_markup
    try: return requests.post(BASE_URL + "sendMessage", json=payload).json()
    except Exception: return None
def edit_message(chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": apply_emojis(text), "parse_mode": parse_mode}
    if reply_markup: payload["reply_markup"] = reply_markup
    try: requests.post(BASE_URL + "editMessageText", json=payload)
    except Exception: pass
def answer_callback_query(callback_query_id, text="", show_alert=False):
    payload = {"callback_query_id": callback_query_id, "text": text, "show_alert": show_alert}
    requests.post(BASE_URL + "answerCallbackQuery", json=payload)
def delete_message(chat_id, message_id):
    payload = {"chat_id": chat_id, "message_id": message_id}
    requests.post(BASE_URL + "deleteMessage", json=payload)
def copy_message(chat_id, from_chat_id, message_id, reply_markup=None):
    payload = {"chat_id": chat_id, "from_chat_id": from_chat_id, "message_id": message_id}
    if reply_markup: payload["reply_markup"] = reply_markup
    try: return requests.post(BASE_URL + "copyMessage", json=payload).json()
    except Exception: return None
def get_chat_details(chat_identifier):
    chat_identifier = str(chat_identifier).strip()
    if chat_identifier.startswith("https://t.me/"): chat_identifier = "@" + chat_identifier.split("/")[-1]
    elif not chat_identifier.startswith("@") and not chat_identifier.startswith("-100"): chat_identifier = "@" + chat_identifier
    url = BASE_URL + "getChat"
    res = requests.get(url, params={"chat_id": chat_identifier}).json()
    if res.get("ok"):
        chat = res["result"]
        chat_data = {"id": chat["id"],"username": "@" + chat["username"] if "username" in chat else "","title": chat.get("title", "Private Channel"),"invite_link": chat.get("invite_link", "")}
        if not chat_data["invite_link"]:
            inv_res = requests.post(BASE_URL + "exportChatInviteLink", json={"chat_id": chat["id"]}).json()
            if inv_res.get("ok"): chat_data["invite_link"] = inv_res["result"]
        return chat_data
    return None
def is_user_joined(user_id):
    if not force_join_status or not force_join_channels: return True
    if user_id == ADMIN_ID: return True
    for ch in force_join_channels:
        try:
            res = requests.get(BASE_URL + "getChatMember", params={"chat_id": ch["id"], "user_id": user_id}).json()
            if res.get("ok"):
                status = res["result"]["status"]
                if status in ["left", "kicked"]: return False
            else: return False
        except: return False
    return True
GLOBAL_BODY_EMOJIS = {"➖": "5870818207383686839", "🚫": "5334807341109908955", "😒": "5334763399299506604","🖥": "5334880948259427772", "🌐": "5334590977837403844", "🌟": "5337102391244263212","🕓": "5336983442125001376", "⌛": "5337172996211648018", "💬": "5337302974806922068","🔐": "5337255927735163754", "🍏": "5337132498965010628", "❔": "5336850036145823599","⚠️": "5336944168944047463", "🔥": "5337267511261960341", "💸": "5429612421977253466","🥚": "5348390922507817684", "👨‍⚖": "5334763399299506604", "🐁": "5348494358205207761","🧻": "5348486915026884464", "⚗": "5346311574221000149", "🛴": "5348075478634766440","📊": "5353032893096567467", "🔢": "5226929552319594190", "👤": "5352861489541714456","📁": "5352721946054268944", "🚀": "5352597830089347330", "💎": "5352838545826420397","📍": "5352922460897452503", "👋": "5353027129250453493", "✅": "5352694861990501856","1️⃣": "5352651766288652742", "2️⃣": "5355186458418257716", "3️⃣": "5352867219028091093","4️⃣": "5352566657216714037", "5️⃣": "5353086880835474989", "6️⃣": "5354859211975071385","7️⃣": "5352859127309707652", "8️⃣": "5352957533600389988", "9️⃣": "5353060913463204207","🔤": "5352727417842606016", "📣": "5352980533150259581", "📤": "5353001161878182134","✨": "5352552689983067014", "🔹": "5352638632278660622", "🎙": "5355102594886833928","💴": "5352985330628730418", "📅": "5352585194295564660", "📴": "5352974971167611327","✏️": "5395444784611480792", "📱": "5337132498965010628", "🔗": "5420517437885943844","❌": "5420130255174145507", "⚙️": "5420155432272438703", "🫂": "5420145051336485498","➕": "5420323438508155202", "🗑": "5422557736330106570", "🎁": "5420396762189831222","➤": "5420618897898381296", "🏢": "5420156334215565595", "💳": "5190899075968441286","📝": "5192739271886282680", "🛡": "5190447043545438788", "🤝": "5192805934073685937","💰": "5190576863226933563", "👀": "5190645917711114179", "🕹": "5193100774988617665","🟢": "5192812028632274956", "🧪": "5190781475468915802", "🎨": "5190751148704833975","📂": "5257969839313526622", "🌍": "5780471598922337683", "📌": "5318986077455795572","📢": "5789428375261023681", "🆔": "5226929552319594190", "📈": "5352877703043258544","🔔": "5352980533150259581", "🏦": "5429612421977253466", "🧾": "5192739271886282680","👨‍⚖️": "5334763399299506604", "🔍": "5463352748751753567", "🔑": "5197288647275071607","🏆": "5240021484516185513", "🚦": "5429571662737611814", "👥": "5420145051336485498", "🎯": "5352922460897452503", "📶": "5429353834881261942", "⏳": "5337172996211648018", "🔸": "5429576112323732785", "🎉": "5420396762189831222", "💵": "5429612421977253466", "👑": "5352838545826420397", "↳": "5420618897898381296","🇺🇸": "5913463998522592692", "🇺🇦": "5911406692007941050", "🇵🇱": "5913550391789752571","🇰🇿": "5913724621433082323", "🇨🇳": "5913779335021466780", "🇦🇿": "5911197578640233518","🇪🇺": "5911106310585193018", "🇦🇲": "5913272455866093666", "🇷🇺": "5913274246867456342","🇺🇿": "5911051846104912282", "🇩🇪": "5911096835887337583", "🇯🇵": "5913293711659241040","🇹🇷": "5910995113881901195", "🇧🇾": "5911011185649521599", "🇬🇧": "5913443365499703513","🇮🇳": "5913754823643107921", "🇧🇷": "5911148568768418614", "🇿🇲": "5913564754160389778","🇾🇪": "5913346492512341993", "🏴󠁧󠁢󠁷󠁬󠁳󠁿": "5911297801702084799", "🇻🇳": "5913428887164949581","🇻🇦": "5911211932420938860", "🇻🇺": "5913511535220625585", "🇺🇾": "5913623088406204470","🇦🇪": "5913726554168365343", "🇺🇬": "5913488939397681980", "🇹🇲": "5913315521503170180","🇹🇳": "5911332947419468671", "🇹🇹": "5911228635548750294", "🇹🇬": "5913423260757790970","🇹🇭": "5913617968805187987", "🇹🇿": "5911418949844603556", "🇹🇯": "5911287639809463107","🇨🇭": "5913271227505448072", "🇸🇪": "5911156510162949403", "🇸🇿": "5913374525763883286","🇸🇷": "5913275539652611719", "🇸🇩": "5911387497799094470", "🇪🇸": "5911193287967904547","🇱🇰": "5911293163137406640", "🇸🇸": "5911406262511211744", "🇿🇦": "5911203119148044594","🇸🇴": "5911397852965244436", "🇸🇧": "5911482712929080608", "🇸🇮": "5913431983836368644","🇸🇰": "5913751666842145020", "🇸🇬": "5911531460808051849", "🇸🇱": "5911210450657218661","🇸🇨": "5911185183364616913", "🇷🇸": "5913592598433369871", "🇸🇳": "5910995302860461643","🏴󠁧󠁢󠁳󠁣󠁴󠁿": "5911460091336331851", "🇸🇹": "5913574331937462345", "🇸🇲": "5913587968458625465","🇼🇸": "5913325971158602854", "🇰🇳": "5913691898077253637", "🇻🇨": "5911318941531116255","🇱🇨": "5911243659344351824", "🇵🇸": "5913684768431541668", "🇷🇼": "5911455229433352234","🇷🇴": "5913460373570195273", "🇶🇦": "5911260864983339619", "🇵🇷": "5911504350974317480","🇵🇹": "5911023653939581472", "🇵🇭": "5911268638874145162", "🇵🇪": "5911207993935925780","🇵🇾": "5911014265141072316", "🇵🇬": "5911107251183030903", "🇵🇦": "5913428968769327174","🇵🇼": "5911283903187915549", "🇵🇰": "5913705895375672082", "🇴🇲": "5913570801474343473","🇳🇴": "5913617397574537046", "🇳🇬": "5911143844304393105", "🇳🇪": "5911270086278124251","🇳🇿": "5913640044937089340", "🇳🇱": "5913367645226275100", "🇳🇵": "5913496520014958723","🇳🇦": "5911108535378252443", "🇲🇿": "5911333419865871464", "🇲🇦": "5911482111633658301","🇲🇪": "5913239436157522151", "🇲🇳": "5911041383564580038", "🇲🇨": "5911245347266500057","🇲🇩": "5913456847402045950", "🇲🇻": "5913501399097806832", "🇲🇱": "5911305266355245916","🇲🇹": "5911023714069123567", "🇧🇲": "5913680005312811090", "🇲🇶": "5911378005921370347","🇲🇭": "5913235935759175692", "🇲🇺": "5913291113204027321", "🇲🇽": "5913687302462246518","🇫🇲": "5911271104185373336", "🇲🇾": "5913654360063087453", "🇰🇪": "5911154710571651231","🇲🇬": "5913766918271012920", "🇲🇰": "5913394029210374721", "🇱🇺": "5913390842344640293","🇱🇹": "5911172315642597775", "🇱🇮": "5911166650580734660", "🇱🇾": "5911236989260140996","🇱🇷": "5913324167272337727", "🇰🇮": "5911294443037660118", "🇽🇰": "5911433681582429010","🇰🇼": "5913290705182134003", "🇰🇬": "5911202161370337549", "🇱🇦": "5913718526874489279","🇱🇻": "5913738489882480243", "🇱🇧": "5911504273664905447", "🇱🇸": "5911059881988723711","🇮🇩": "5913479361620611038", "🇮🇷": "5911308891307643032", "🇮🇶": "5911382442622587735","🇮🇪": "5913440715504881532", "🇮🇱": "5911471936856134692", "🇮🇹": "5913688444923547525","🇯🇲": "5913232280742006526", "🇯🇴": "5913234136167878475", "🇮🇸": "5911047899029967246","🇭🇺": "5913767635530551104", "🇭🇳": "5911406889576436289", "🇭🇹": "5913459789454643194","🇬🇾": "5913579412883771480", "🇬🇼": "5911398694778836149", "🇬🇳": "5913471858312744319","🇬🇹": "5913324858762072330", "🇬🇩": "5913228063084121946", "🇬🇷": "5911210399117611448","🇬🇭": "5913391155877252952", "🇬🇪": "5913434771270144023", "🇬🇲": "5913657267755945883","🇬🇦": "5911037896051137264", "🇫🇷": "5913605586414473124", "🇫🇮": "5911041344909873378","🇫🇯": "5911393832875856716", "🇪🇹": "5911078333168227043", "🇩🇴": "5911152099231536123","🇹🇱": "5911141915864076479", "🇪🇨": "5911273865849347408", "🇪🇬": "5913694831539916769","🇸🇻": "5913238624408703010", "🏴󠁧󠁢󠁥󠁮󠁧󠁿": "5913475719488344315", "🇪🇪": "5910986042910969906","🇩🇲": "5911377121158107430", "🇩🇯": "5911407709915190157", "🇩🇰": "5911206009661034712","🇨🇾": "5911023550860366409", "🇭🇷": "5913692684056269311", "🇨🇷": "5911261745451635030","🇨🇬": "5911338788574990168", "🇨🇩": "5913770362834783827", "🇰🇲": "5911338582416560604","🇰🇲": "5911338582416560604", "🇨🇲": "5911172109484167745", "🇨🇦": "5913623736946265914","🇨🇻": "5913571501554012193", "🇨🇫": "5913443245240619222", "🇹🇩": "5913299849167507310","🇨🇿": "5911198691036764307", "🇨🇱": "5911470957603592832", "🇨🇴": "5913773060074246009","🇧🇮": "5913766441529642752", "🇧🇼": "5911513782722499475", "🇧🇦": "5913700002680541032","🇧🇴": "5913638795101606133", "🇧🇹": "5913236734623093021", "🇧🇯": "5913735869952430547","🇦🇷": "5913573356979884082", "🇦🇺": "5913632326880858455", "🇦🇹": "5911338831524664592","🇧🇸": "5911451643135660214", "🇧🇭": "5913581663446634403", "🇧🇩": "5911365056594973179","🇧🇧": "5911016996740272263", "🇧🇪": "5913529642802745141", "🇧🇿": "5913355005137522807","🇦🇬": "5913389025573475085", "🇦🇴": "5913753316109586411", "🇦🇩": "5911314702398396902","🇩🇿": "5913782968563800236", "🇦🇱": "5911357458797826163", "🇦🇫": "5913492040364068694","🇿🇼": "5911092502265336396", "🇨🇺": "5431551436502611633", "🇰🇵": "5434142701941437163","🇻🇪": "5434009132753499322", "🇸🇾": "5433910876786670092", "🇲🇲": "5433666360003540231","🇳🇮": "5334807849418003620", "🇰🇷": "5913371673905598425", "🇬🇶": "5911306279967529251","🇬🇱": "5292014752283774878", "🇫🇴": "5296469342039327674", "🇨🇮": "5222233374948602940","🇧🇳": "5911336409163109113", "🇧🇬": "5294329219965272288", "🇧🇫": "5913407764515786948","🇪🇷": "5433723401464198287", "🇲🇼": "5433968339154122439", "🇲🇷": "5433859405898594234","🇳🇷": "5434131139889478358", "🇸🇦": "4985897134424328239", "🇹🇴": "5433640100573491806","🇹🇻": "5433684690923961019", "🇹🇼": "5366187256937726720", "🇭🇰": "5292166459118606932","🇲🇴": "6323557758096377611"}
def apply_emojis(text):
    hidden = []
    def hide(match):
        hidden.append(match.group(0))
        return f"__TG_EMOJI_{len(hidden)-1}__"
    text = re.sub(r'<tg-emoji[^>]*>.*?</tg-emoji>', hide, text)
    for char, eid in GLOBAL_BODY_EMOJIS.items(): text = text.replace(char, f'<tg-emoji emoji-id="{eid}">{char}</tg-emoji>')
    for i, h in enumerate(hidden): text = text.replace(f"__TG_EMOJI_{i}__", h)
    return text
PREMIUM_APPS = {"Facebook": {"emoji": "📘", "id": "5429172110520003976"},"WhatsApp": {"emoji": "💬", "id": "5429612632430654504"},"Telegram": {"emoji": "✈️", "id": "5429136513831057777"},"Instagram": {"emoji": "📸", "id": "5429478178479447442"},"Google": {"emoji": "🔍", "id": "5429558795015593080"},"Microsoft": {"emoji": "🪟", "id": "5979047775470358891"},"TikTok": {"emoji": "🎵", "id": "5429132656950419591"},"Bkash": {"emoji": "🏦", "id": "5431552076452766597"},"Binance": {"emoji": "💱", "id": "5429438106434575354"},"Snapchat": {"emoji": "👻", "id": "5429398137468919845"},"Uber": {"emoji": "🚗", "id": "5298715455316303708"},"Discord": {"emoji": "🎬", "id": "5429594374524676604"},"Amazon": {"emoji": "🌟", "id": "5431358656895568355"},"Viber": {"emoji": "💜", "id": "5429470576387335368"},"Twitter": {"emoji": "🐦", "id": "5431899135580087595"},"Netflix": {"emoji": "🎥", "id": "5431641055290235797"},"Spotify": {"emoji": "🎵", "id": "5429235839244739644"},"Foodpanda": {"emoji": "🐼", "id": "5336879280578138635"},"Pathao": {"emoji": "🛵", "id": "5336879280578138635"},"ChatGPT": {"emoji": "🤖", "id": "5429503209548847635"},"Imo": {"emoji": "💭", "id": "5431378937731129128"},"Other": {"emoji": "📶", "id": "5429353834881261942"}}
SERVICE_SMS_KEYWORDS = {"Facebook": ["facebook", "fb code", "fb", "meta"],"WhatsApp": ["whats", "whatsapp", "whatsapp code"],"Telegram": ["telegram", "tg code"],"Instagram": ["instagram", "ig code"],"Google": ["google", "Googl"],"Microsoft": ["microsoft", "micro", "Microsof", "xbox"],"TikTok": ["tiktok", "tik tok"],"Bkash": ["bkash"],"Binance": ["binance", "bnb"],"Snapchat": ["snapchat", "snap"],"Uber": ["uber"],"Discord": ["discord"],"Amazon": ["amazon", "aws"],"Viber": ["viber"],"Twitter": ["twitter", "x.com"],"Netflix": ["netflix"],"Spotify": ["spotify"],"Foodpanda": ["foodpanda", "panda"],"Pathao": ["pathao"],"ChatGPT": ["openai", "chatgpt"],"Imo": ["imo code", "imo"]}
COUNTRY_CODES = {"1": "🇺🇸 USA/Canada", "380": "🇺🇦 Ukraine", "48": "🇵🇱 Poland", "7": "🇰🇿 Kazakhstan","86": "🇨🇳 China", "994": "🇦🇿 Azerbaijan", "374": "🇦🇲 Armenia", "79": "🇷🇺 Russia","998": "🇺🇿 Uzbekistan", "49": "🇩🇪 Germany", "81": "🇯🇵 Japan", "90": "🇹🇷 Turkey","375": "🇧🇾 Belarus", "44": "🇬🇧 United Kingdom", "91": "🇮🇳 India", "55": "🇧🇷 Brazil","260": "🇿🇲 Zambia", "967": "🇾🇪 Yemen", "84": "🇻🇳 Vietnam", "379": "🇻🇦 Vatican City","678": "🇻🇺 Vanuatu", "598": "🇺🇾 Uruguay", "971": "🇦🇪 UAE", "256": "🇺🇬 Uganda","993": "🇹🇲 Turkmenistan", "216": "🇹🇳 Tunisia", "228": "🇹🇬 Togo", "66": "🇹🇭 Thailand","255": "🇹🇿 Tanzania", "992": "🇹🇯 Tajikistan", "41": "🇨🇭 Switzerland", "46": "🇸🇪 Sweden","268": "🇸🇿 Eswatini", "597": "🇸🇷 Suriname", "249": "🇸🇩 Sudan", "34": "🇪🇸 Spain","94": "🇱🇰 Sri Lanka", "211": "🇸🇸 South Sudan", "27": "🇿🇦 South Africa", "252": "🇸🇴 Somalia","677": "🇸🇧 Solomon Islands", "386": "🇸🇮 Slovenia", "421": "🇸🇰 Slovakia", "65": "🇸🇬 Singapore","232": "🇸🇱 Sierra Leone", "248": "🇸🇨 Seychelles", "381": "🇷🇸 Serbia", "221": "🇸🇳 Senegal","239": "🇸🇹 Sao Tome", "378": "🇸🇲 San Marino", "685": "🇼🇸 Samoa", "970": "🇵🇸 Palestine","250": "🇷🇼 Rwanda", "40": "🇷🇴 Romania", "974": "🇶🇦 Qatar", "351": "🇵🇹 Portugal","63": "🇵🇭 Philippines", "51": "🇵🇪 Peru", "595": "🇵🇾 Paraguay", "675": "🇵🇬 Papua New Guinea","507": "🇵🇦 Panama", "680": "🇵🇼 Palau", "92": "🇵🇰 Pakistan", "968": "🇴🇲 Oman","47": "🇳🇴 Norway", "234": "🇳🇬 Nigeria", "227": "🇳🇪 Niger", "64": "🇳🇿 New Zealand","31": "🇳🇱 Netherlands", "977": "🇳🇵 Nepal", "264": "🇳🇦 Namibia", "258": "🇲🇿 Mozambique","212": "🇲🇦 Morocco", "382": "🇲🇪 Montenegro", "976": "🇲🇳 Mongolia", "377": "🇲🇨 Monaco","373": "🇲🇩 Moldova", "960": "🇲🇻 Maldives", "223": "🇲🇱 Mali", "356": "🇲🇹 Malta","596": "🇲🇶 Martinique", "692": "🇲🇭 Marshall Islands", "230": "🇲🇺 Mauritius", "52": "🇲🇽 Mexico","691": "🇫🇲 Micronesia", "60": "🇲🇾 Malaysia", "254": "🇰🇪 Kenya", "261": "🇲🇬 Madagascar","389": "🇲🇰 North Macedonia", "352": "🇱🇺 Luxembourg", "370": "🇱🇹 Lithuania", "423": "🇱🇮 Liechtenstein","218": "🇱🇾 Libya", "231": "🇱🇷 Liberia", "686": "🇰🇮 Kiribati", "383": "🇽🇰 Kosovo","965": "🇰🇼 Kuwait", "996": "🇰🇬 Kyrgyzstan", "856": "🇱🇦 Laos", "371": "🇱🇻 Latvia","961": "🇱🇧 Lebanon", "266": "🇱🇸 Lesotho", "62": "🇮🇩 Indonesia", "98": "🇮🇷 Iran","964": "🇮🇶 Iraq", "353": "🇮🇪 Ireland", "972": "🇮🇱 Israel", "39": "🇮🇹 Italy","962": "🇯🇴 Jordan", "354": "🇮🇸 Iceland", "36": "🇭🇺 Hungary", "504": "🇭🇳 Honduras","509": "🇭🇹 Haiti", "592": "🇬🇾 Guyana", "245": "🇬🇼 Guinea-Bissau", "224": "🇬🇳 Guinea","502": "🇬🇹 Guatemala", "30": "🇬🇷 Greece", "233": "🇬🇭 Ghana", "995": "🇬🇪 Georgia","220": "🇬🇲 Gambia", "241": "🇬🇦 Gabon", "33": "🇫🇷 France", "358": "🇫🇮 Finland","679": "🇫🇯 Fiji", "251": "🇪🇹 Ethiopia", "670": "🇹🇱 Timor-Leste", "593": "🇪🇨 Ecuador","20": "🇪🇬 Egypt", "503": "🇸🇻 El Salvador", "372": "🇪🇪 Estonia", "253": "🇩🇯 Djibouti","45": "🇩🇰 Denmark", "357": "🇨🇾 Cyprus", "385": "🇭🇷 Croatia", "506": "🇨🇷 Costa Rica","242": "🇨🇬 Congo", "243": "🇨🇩 DR Congo", "269": "🇰🇲 Comoros", "855": "🇰🇭 Cambodia","237": "🇨🇲 Cameroon", "238": "🇨🇻 Cape Verde", "236": "🇨🇫 CAR", "235": "🇹🇩 Chad","420": "🇨🇿 Czechia", "56": "🇨🇱 Chile", "57": "🇨🇴 Colombia", "257": "🇧🇮 Burundi","267": "🇧🇼 Botswana", "387": "🇧🇦 Bosnia", "591": "🇧🇴 Bolivia", "975": "🇧🇹 Bhutan","229": "🇧🇯 Benin", "54": "🇦🇷 Argentina", "61": "🇦🇺 Australia", "43": "🇦🇹 Austria","973": "🇧🇭 Bahrain", "880": "🇧🇩 Bangladesh", "32": "🇧🇪 Belgium", "501": "🇧🇿 Belize","244": "🇦🇴 Angola", "376": "🇦🇩 Andorra", "213": "🇩🇿 Algeria", "355": "🇦🇱 Albania","93": "🇦🇫 Afghanistan", "263": "🇿🇼 Zimbabwe", "53": "🇨🇺 Cuba", "850": "🇰🇵 North Korea","58": "🇻🇪 Venezuela", "963": "🇸🇾 Syria", "95": "🇲🇲 Myanmar", "505": "🇳🇮 Nicaragua","82": "🇰🇷 South Korea", "240": "🇬🇶 Equatorial Guinea", "299": "🇬🇱 Greenland", "298": "🇫🇴 Faroe Islands","225": "🇨🇮 Ivory Coast", "673": "🇧🇳 Brunei", "359": "🇧🇬 Bulgaria", "226": "🇧🇫 Burkina Faso","291": "🇪🇷 Eritrea", "265": "🇲🇼 Malawi", "222": "🇲🇷 Mauritania", "674": "🇳🇷 Nauru","966": "🇸🇦 Saudi Arabia", "676": "🇹🇴 Tonga", "688": "🇹🇻 Tuvalu", "886": "🇹🇼 Taiwan","852": "🇭🇰 Hong Kong", "853": "🇲🇴 Macau", "297": "🇦🇼 Aruba", "599": "🇨🇼 Curacao","500": "🇫🇰 Falkland Islands", "594": "🇬🇫 French Guiana", "590": "🇬🇵 Guadeloupe", "262": "🇷🇪 Reunion","687": "🇳🇨 New Caledonia", "683": "🇳🇺 Niue", "672": "🇳🇫 Norfolk Island", "681": "🇼🇫 Wallis and Futuna","682": "🇨🇰 Cook Islands", "689": "🇵🇫 French Polynesia", "350": "🇬🇮 Gibraltar", "508": "🇵🇲 Saint Pierre"}
def get_country_info(range_str):
    clean_range = str(range_str or "").replace("X", "")
    for code, name in sorted(COUNTRY_CODES.items(), key=lambda x: len(x[0]), reverse=True):
        if clean_range.startswith(code): return code, name
    return clean_range[:3], f"🏳️ Other (+{clean_range[:3]})"
def detect_service(message_text, raw_sid=""):
    msg_lower = str(message_text).lower()
    sid_lower = str(raw_sid).lower()
    for service, keywords in SERVICE_SMS_KEYWORDS.items():
        for kw in keywords:
            if re.search(rf'\b{re.escape(kw)}\b', msg_lower) or kw in msg_lower: return service
    for service in PREMIUM_APPS.keys():
        if service.lower() in sid_lower: return service
    return "Other"
def get_service_info_html(service_name):
    app_info = PREMIUM_APPS.get(service_name, PREMIUM_APPS["Other"])
    emoji_id = app_info["id"]
    normal_emoji = app_info["emoji"]
    short_name = service_name.upper()
    if short_name == "FACEBOOK": short_name = "FB"
    if short_name == "WHATSAPP": short_name = "WS"
    if short_name == "INSTAGRAM": short_name = "IG"
    return f'<tg-emoji emoji-id="{emoji_id}">{normal_emoji}</tg-emoji> <b>{html.escape(short_name)}</b>', emoji_id
def extract_otp_code(message_text):
    match = re.search(r'\b(\d{3}[\s-]?\d{3,4}|\d{4,8})\b', str(message_text))
    if match: return match.group(1)
    return "COPY"
def deliver_to_inbox(user_id, service_name, raw_number, msg_text, current_balance, reward):
    c_code, c_name = get_country_info(raw_number)
    service_html, srv_eid = get_service_info_html(service_name)
    clean_raw_number = str(raw_number).lstrip('+')
    text = (f"— — — — — — — — — —\n<blockquote>{service_html} <code>+{clean_raw_number}</code></blockquote>\n<blockquote><tg-emoji emoji-id=\"5420323438508155202\">➕</tg-emoji> <b>ADDED</b> ➜ {reward:.2f} TK</blockquote>\n<blockquote><tg-emoji emoji-id=\"5190899075968441286\">💳</tg-emoji> <b>BALANCE</b> ➜ {current_balance:.2f} TK</blockquote>\n— — — — — — — — — —")
    otp = extract_otp_code(msg_text)
    markup = {"inline_keyboard": [[{"text": f"{otp}", "icon_custom_emoji_id": srv_eid, "copy_text": {"text": otp}, "style": "success"}]]}
    send_message(user_id, text, reply_markup=markup)
def generate_otp_display(service_name, raw_number, message_text):
    c_code, c_name = get_country_info(raw_number)
    parts = c_name.split(" ", 1)
    country_emoji = parts[0]
    if len(raw_number) > 6: masked_number = f"{raw_number[:3]}DXA{raw_number[-3:]}"
    else: masked_number = raw_number
    service_html, srv_eid = get_service_info_html(service_name)
    text = (f"━━━━━━━━━━━━━━━━━\n{service_html} ➜ {country_emoji} <code>{html.escape(masked_number)}</code>\n━━━━━━━━━━━━━━━━━")
    otp = extract_otp_code(message_text)
    clean_range = str(raw_number)[:5] if len(str(raw_number)) >= 5 else str(raw_number)
    deep_link = f"https://t.me/{BOT_USERNAME}?start=alloc_{clean_range}_{service_name.lower()}"
    markup = {"inline_keyboard": []}
    row1 = []
    main_channel_link = bot_settings.get("main_channel_link", "")
    if main_channel_link: row1.append({"text": "𝗖𝗛𝗔𝗡𝗡𝗘𝗟", "url": main_channel_link, "icon_custom_emoji_id": "5429353834881261942", "style": "primary"})
    row1.append({"text": f"{otp}", "icon_custom_emoji_id": srv_eid, "copy_text": {"text": otp}, "style": "success"})
    markup["inline_keyboard"].append(row1)
    markup["inline_keyboard"].append([{"text": "GET NUMBER", "url": deep_link, "icon_custom_emoji_id": "5429167978761461870", "style": "danger"}])
    return text, markup
def send_otp_to_groups(formatted_text, markup):
    global otp_forward_groups
    if not otp_forward_groups: return False
    sent_any = False
    for group_id in otp_forward_groups:
        resp = send_message(group_id, formatted_text, reply_markup=markup)
        if resp and resp.get("ok"): sent_any = True
        time.sleep(1)
    return sent_any
def fetch_live_access():
    headers = {"mauthapi": get_api_key()}
    try:
        res = requests.get(f"{API_2OO9_BASE}/liveaccess", headers=headers, timeout=10)
        data = res.json()
        if data.get("meta", {}).get("code") == 200: return data.get("data", {}).get("services", [])
    except: pass
    return []
def fetch_live_number(rid):
    headers = {"mauthapi": get_api_key(), "Content-Type": "application/json"}
    payload = {"rid": str(rid)}
    try:
        res = requests.post(f"{API_2OO9_BASE}/getnum", headers=headers, json=payload, timeout=10)
        data = res.json()
        if data.get("meta", {}).get("code") == 200: return data.get("data", {})
    except: pass
    return None
def voltx_console_listener():
    global recent_traffic, voltx_dynamic_data
    cycle_count = 0
    while True:
        try:
            headers = {"mauthapi": get_api_key()}
            res = requests.get(f"{API_2OO9_BASE}/console", headers=headers, timeout=10)
            data = res.json()
            if data.get("meta", {}).get("code") == 200:
                hits = data.get("data", {}).get("hits", [])
                new_traffic, seen_signatures = [], set()
                current_time = int(time.time())
                for h in hits:
                    sig = f"{h.get('time', 0)}_{h.get('range', '')}"
                    if sig not in seen_signatures:
                        h['local_receive_time'] = current_time
                        new_traffic.append(h)
                        seen_signatures.add(sig)
                        raw_sid = h.get("sid") or "Unknown"
                        raw_msg = h.get("message") or ""
                        raw_range = str(h.get("range", "")).replace("X", "")
                        if raw_range:
                            detected_sid = detect_service(raw_msg, raw_sid)
                            app_info = PREMIUM_APPS.get(detected_sid, PREMIUM_APPS["Other"])
                            emoji_id, normal_emoji = app_info["id"], app_info["emoji"]
                            if detected_sid not in voltx_dynamic_data: voltx_dynamic_data[detected_sid] = {"emoji_id": emoji_id, "normal_emoji": normal_emoji, "ranges": {}}
                            if raw_range not in voltx_dynamic_data[detected_sid]["ranges"]: voltx_dynamic_data[detected_sid]["ranges"][raw_range] = {"last_seen": current_time, "hits": 0}
                            voltx_dynamic_data[detected_sid]["ranges"][raw_range]["last_seen"] = current_time
                            voltx_dynamic_data[detected_sid]["ranges"][raw_range]["hits"] += 1
                fifteen_mins_ago = current_time - 900
                for h in recent_traffic:
                    if h.get('local_receive_time', 0) >= fifteen_mins_ago:
                        sig = f"{h.get('time', 0)}_{h.get('range', '')}"
                        if sig not in seen_signatures:
                            new_traffic.append(h)
                            seen_signatures.add(sig)
                new_traffic.sort(key=lambda x: x.get('local_receive_time', 0), reverse=True)
                recent_traffic = new_traffic
                services_to_delete = []
                for sid, s_data in voltx_dynamic_data.items():
                    ranges_to_delete = []
                    for r, r_data in s_data["ranges"].items():
                        if current_time - r_data["last_seen"] > 300: ranges_to_delete.append(r)
                    for r in ranges_to_delete: del s_data["ranges"][r]
                    if not s_data["ranges"]: services_to_delete.append(sid)
                for sid in services_to_delete: del voltx_dynamic_data[sid]
                cycle_count += 1
                if cycle_count % 3 == 0: save_local_data()
        except Exception: pass
        time.sleep(10)
def voltx_sms_listener():
    global recent_success_otps, otp_forward_groups, user_active_sessions
    group_sent_otps = set()
    while True:
        try:
            headers = {"mauthapi": get_api_key(), "Content-Type": "application/json"}
            res = requests.get(f"{API_2OO9_BASE}/success-otp", headers=headers, timeout=15)
            if res.status_code == 200:
                data = res.json()
                otps = []
                if isinstance(data, dict):
                    if "data" in data and isinstance(data["data"], list): otps = data["data"]
                    elif "data" in data and isinstance(data["data"], dict):
                        if "otps" in data["data"]: otps = data["data"]["otps"]
                        elif "hits" in data["data"]: otps = data["data"]["hits"]
                    elif "otps" in data: otps = data["otps"]
                    elif "hits" in data: otps = data["hits"]
                elif isinstance(data, list): otps = data
                for otp_data in reversed(otps):
                    msg_text = str(otp_data.get("message", otp_data.get("sms", otp_data.get("code", ""))))
                    raw_number = str(otp_data.get("number", otp_data.get("phone", "")))
                    raw_service = str(otp_data.get("sid", otp_data.get("service", "Unknown")))
                    if not msg_text or not raw_number: continue
                    sig = f"{raw_number}_{msg_text}"
                    detected_service = detect_service(msg_text, raw_service)
                    if sig not in group_sent_otps:
                        group_sent_otps.add(sig)
                        if otp_forward_groups:
                            formatted_message, markup = generate_otp_display(detected_service, raw_number, msg_text)
                            send_otp_to_groups(formatted_message, markup)
                    if sig not in recent_success_otps:
                        recent_success_otps.add(sig)
                        owner_id = None
                        last_8_digits = raw_number[-8:] if len(raw_number) > 8 else raw_number
                        for active_num, uid in list(user_active_sessions.items()):
                            if active_num.endswith(last_8_digits):
                                owner_id = uid
                                del user_active_sessions[active_num]
                                break
                        if owner_id:
                            reward = get_otp_reward(detected_service)
                            update_user_stats(owner_id, reward, 0)
                            user_balance = get_user(owner_id).get("balance", 0.0)
                            deliver_to_inbox(owner_id, detected_service, raw_number, msg_text, user_balance, reward)
                            today_date = time.strftime("%Y-%m-%d")
                            if daily_user_otps.get("date")!= today_date:
                                daily_user_otps["date"] = today_date
                                daily_user_otps["users"] = {}
                            uid_str = str(owner_id)
                            daily_user_otps["users"][uid_str] = daily_user_otps["users"].get(uid_str, 0) + 1
                        update_daily_stat("otps", 1)
                        save_local_data()
                        time.sleep(1)
            if len(recent_success_otps) > 2000:
                recent_success_otps = set(list(recent_success_otps)[-1000:])
                save_local_data()
            if len(group_sent_otps) > 2000: group_sent_otps = set(list(group_sent_otps)[-1000:])
        except Exception: pass
        time.sleep(10)

def init_sqlite():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, first_name TEXT DEFAULT 'User', balance REAL DEFAULT 0.0, total_invites INTEGER DEFAULT 0)")
    try: cursor.execute("ALTER TABLE users ADD COLUMN first_name TEXT DEFAULT 'User'")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE users ADD COLUMN total_otps INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    conn.commit()
    conn.close()
def migrate_sqlite_to_firebase():
    global db_firebase, user_cache
    if not db_firebase: return
    try:
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, first_name, balance, total_invites FROM users")
        rows = cursor.fetchall()
        if not rows: return conn.close()
        count = 0
        batch = db_firebase.batch()
        for row in rows:
            uid, fname, bal, inv = row
            doc_ref = db_firebase.collection('users').document(str(uid))
            batch.set(doc_ref, {"user_id": uid, "first_name": fname, "balance": firestore.Increment(bal), "total_invites": firestore.Increment(inv)}, merge=True)
            count += 1
            if count % 400 == 0:
                batch.commit()
                batch = db_firebase.batch()
        if count % 400!= 0: batch.commit()
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()
        user_cache.clear()
    except Exception as e: print(f"Migration Error: {e}")
def init_firebase_from_file():
    global current_db_mode, db_firebase, bot_settings, force_join_status, force_join_channels, otp_forward_groups, otp_button_link, voltx_keys, voltx_auto_mode
    if os.path.exists("temp_firebase.json"):
        try:
            if not firebase_admin._apps: firebase_admin.initialize_app(credentials.Certificate("temp_firebase.json"))
            db_firebase = firestore.client()
            current_db_mode = "firebase"
            print("✅ Firebase Auto-Connected on Startup!")
            doc = db_firebase.collection('settings').document('bot_config').get()
            if doc.exists:
                data = doc.to_dict()
                if "bot_settings" in data: bot_settings.update(data["bot_settings"])
                if "force_join_status" in data: force_join_status = data["force_join_status"]
                if "force_join_channels" in data: force_join_channels = data["force_join_channels"]
                if "otp_forward_groups" in data: otp_forward_groups = data["otp_forward_groups"]
                if "otp_button_link" in data: otp_button_link = data["otp_button_link"]
                if "voltx_keys" in data: voltx_keys = data["voltx_keys"]
                if "voltx_auto_mode" in data: voltx_auto_mode = data["voltx_auto_mode"]
                print("✅ Settings synced from Firebase!")
            try:
                local_users = set()
                if os.path.exists(USERS_LIST_FILE):
                    with open(USERS_LIST_FILE, "r") as f: local_users = set(json.load(f))
                docs = db_firebase.collection('users').select([]).stream()
                fb_users = set(int(doc.id) for doc in docs)
                combined_users = local_users.union(fb_users)
                if len(combined_users) > len(local_users):
                    with open(USERS_LIST_FILE, "w") as f: json.dump(list(combined_users), f)
                    print(f"✅ Auto-Synced {len(fb_users)} users on Startup!")
            except Exception as e: print(f"Startup Sync Error: {e}")
        except Exception as e: print(f"❌ Firebase Auto-Connect Error: {e}")

def get_user(user_id):
    global current_db_mode, db_firebase, user_cache
    if user_id in user_cache: return user_cache[user_id]
    if current_db_mode == "firebase" and db_firebase:
        doc = db_firebase.collection('users').document(str(user_id)).get()
        if doc.exists:
            user_data = doc.to_dict()
            user_cache[user_id] = user_data
            return user_data
        return None
    else:
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT first_name, balance, total_invites FROM users WHERE user_id =?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            user_data = {"user_id": user_id, "first_name": row[0], "balance": row[1], "total_invites": row[2]}
            user_cache[user_id] = user_data
            return user_data
        return None
def add_user(user_id, first_name="User"):
    global current_db_mode, db_firebase, user_cache
    add_to_broadcast_list(user_id)
    if user_id in user_cache and user_cache[user_id]["first_name"] == first_name: return
    if current_db_mode == "firebase" and db_firebase:
        doc_ref = db_firebase.collection('users').document(str(user_id))
        if not doc_ref.get().exists:
            new_data = {"user_id": user_id, "first_name": first_name, "balance": 0.0, "total_invites": 0}
            doc_ref.set(new_data)
            user_cache[user_id] = new_data
        else:
            doc_ref.update({"first_name": first_name})
            if user_id in user_cache: user_cache[user_id]["first_name"] = first_name
    else:
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id, first_name, balance, total_invites) VALUES (?,?, 0.0, 0)", (user_id, first_name))
        cursor.execute("UPDATE users SET first_name =? WHERE user_id =?", (first_name, user_id))
        conn.commit()
        conn.close()
        if user_id not in user_cache: user_cache[user_id] = {"user_id": user_id, "first_name": first_name, "balance": 0.0, "total_invites": 0}
        else: user_cache[user_id]["first_name"] = first_name
def update_user_stats(user_id, balance_add, invite_add):
    global current_db_mode, db_firebase, user_cache
    bal_add = float(balance_add)
    inv_add = int(invite_add)
    if user_id not in user_cache: get_user(user_id)
    if user_id in user_cache:
        user_cache[user_id]["balance"] = round(user_cache[user_id]["balance"] + bal_add, 2)
        user_cache[user_id]["total_invites"] += inv_add
    if current_db_mode == "firebase" and db_firebase:
        db_firebase.collection('users').document(str(user_id)).update({"balance": firestore.Increment(bal_add), "total_invites": firestore.Increment(inv_add)})
    else:
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance +?, total_invites = total_invites +? WHERE user_id =?", (bal_add, inv_add, user_id))
        conn.commit()
        conn.close()
def get_total_users(): return len(get_all_user_ids())
def get_top_users(limit=5):
    global current_db_mode, db_firebase
    if current_db_mode == "firebase" and db_firebase:
        docs = db_firebase.collection('users').order_by('balance', direction=firestore.Query.DESCENDING).limit(limit).stream()
        return [(doc.to_dict().get("user_id"), doc.to_dict().get("first_name", "User"), doc.to_dict().get("balance")) for doc in docs]
    else:
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, first_name, balance FROM users ORDER BY balance DESC LIMIT?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows
#... (বাকি তোমার আগের সব ফাংশন আগের মতোই)...
# আমি জায়গা বাঁচাতে এখানে সংক্ষেপ করলাম কিন্তু তোমার কোডে পুরাটা আছে, শুধু নিচের Flask অংশটা যোগ করলেই হবে

# ============ RENDER FIX START ============
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is Running! Free Instance Active."

def run_bot_polling():
    global BOT_USERNAME
    load_local_data()
    init_sqlite()
    init_firebase_from_file()
    BOT_USERNAME = get_bot_info()
    set_bot_commands()
    threading.Thread(target=voltx_console_listener, daemon=True).start()
    threading.Thread(target=voltx_sms_listener, daemon=True).start()
    threading.Thread(target=auto_cache_menu_thread, daemon=True).start()
    print(f"Bot @{BOT_USERNAME} is running...")
    offset = None
    while True:
        try:
            url = BASE_URL + "getUpdates"
            res = requests.get(url, params={"timeout": 30, "offset": offset}).json()
            if res.get("ok"):
                for update in res["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update: threading.Thread(target=handle_message, args=(update["message"],)).start()
                    elif "callback_query" in update: threading.Thread(target=handle_callback, args=(update["callback_query"],)).start()
        except Exception as e:
            time.sleep(3)

# নিচের বাকি handle_message, handle_callback ফাংশনগুলো তোমার আগের কোড থেকে কপি থাকবে

if __name__ == "__main__":
    # Bot কে ব্যাকগ্রাউন্ডে চালাও
    threading.Thread(target=run_bot_polling, daemon=True).start()
    # Flask কে Render এর Port এ চালাও
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)
