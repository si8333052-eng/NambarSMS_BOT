# FINAL CLEAN - OWNER: E Noyon (6560485203)
# - TucosProfit removed permanently
# - Only your channel will show
# - No hidden backdoor
import requests
import time
import json
import random
import sqlite3
import os
import re
import html
import threading
from flask import Flask


# ===== AUTO CLEAN FOR FREE PLAN - Removes TucosProfit AND your_default =====
try:
    if os.path.exists("bot_data.json"):
        with open("bot_data.json","r",encoding="utf-8", errors="ignore") as jf:
            content = jf.read().lower()
            # If file contains any bad default links, delete it to make it empty
            if "tucosprofit" in content or "your_default" in content or "your_default_bot" in content:
                os.remove("bot_data.json")
                print("CLEANED: bot_data.json with default/banned group deleted!")
            else:
                # Also clean specific fields if file is valid json
                try:
                    import json as _js
                    with open("bot_data.json","r",encoding="utf-8") as jf2:
                        data = _js.load(jf2)
                    changed = False
                    # Clean otp_forward_groups
                    if "otp_forward_groups" in data:
                        new_groups = [g for g in data["otp_forward_groups"] if "tucos" not in g.lower() and "your_default" not in g.lower()]
                        if len(new_groups) != len(data["otp_forward_groups"]):
                            data["otp_forward_groups"] = new_groups
                            changed = True
                    # Clean force_join_channels
                    if "force_join_channels" in data:
                        new_ch = [c for c in data["force_join_channels"] if "tucos" not in str(c).lower() and "your_default" not in str(c).lower()]
                        if len(new_ch) != len(data["force_join_channels"]):
                            data["force_join_channels"] = new_ch
                            changed = True
                    # Clean bot_settings
                    if "bot_settings" in data:
                        if "tucos" in str(data["bot_settings"].get("w_group","")).lower() or "your_default" in str(data["bot_settings"].get("w_group","")).lower():
                            data["bot_settings"]["w_group"] = ""
                            changed = True
                        if "tucos" in str(data["bot_settings"].get("main_channel_link","")).lower() or "your_default" in str(data["bot_settings"].get("main_channel_link","")).lower():
                            data["bot_settings"]["main_channel_link"] = ""
                            changed = True
                        if "tucos" in str(data["bot_settings"].get("otp_button_link","")).lower() or "your_default" in str(data["bot_settings"].get("otp_button_link","")).lower():
                            data["bot_settings"]["otp_button_link"] = ""
                            changed = True
                    if changed:
                        with open("bot_data.json","w",encoding="utf-8") as out:
                            _js.dump(data, out, indent=2)
                        print("CLEANED: bad groups removed from bot_data.json")
                except:
                    pass
except Exception as e:
    print(f"Clean check: {e}")
# ============================================================


import firebase_admin
from firebase_admin import credentials, firestore
# ==========================================
# Configuration
# ==========================================
BOT_TOKEN = "8604617628:AAFKtdLBP48TyLoOE_UR3pK8D7dn4-t5iOY"
ADMIN_ID = 6560485203  # E Noyon - Main Owner
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
BOT_USERNAME = "number999sms_bot"
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
user_active_sessions = {} # format: {"number": user_id}
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
daily_stats = {"date": "", "numbers": 0, "otps": 0} # ðŸŒŸ Daily Stats Tracker
daily_user_otps = {"date": "", "users": {}}

# ðŸŒŸ Caching Variables for Rocket Speed!
cached_services_kb = None
cached_countries_kb = {}
cached_leaderboard_text = ""

def auto_cache_menu_thread():
    global cached_services_kb, cached_countries_kb, voltx_auto_mode, voltx_dynamic_data
    while True:
        try:
            if voltx_auto_mode and voltx_dynamic_data:
                service_hits = [(sid, s_data, sum(r["hits"] for r in s_data["ranges"].values())) for sid, s_data in voltx_dynamic_data.items()]
                top_services = sorted(service_hits, key=lambda x: x[2], reverse=True)[:15] # ðŸŒŸ Top 15 Services
                
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
                    
                    top_countries = sorted(country_map.items(), key=lambda x: x[1]["hits"], reverse=True)[:15] # ðŸŒŸ Top 15 Countries
                    
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
                
            # --- ðŸŒŸ Leaderboard Caching ---
            global cached_leaderboard_text, daily_user_otps
            today = time.strftime("%Y-%m-%d")
            if daily_user_otps.get("date") != today:
                daily_user_otps["date"] = today
                daily_user_otps["users"] = {}
                
            top_users = sorted(daily_user_otps["users"].items(), key=lambda x: x[1], reverse=True)[:5]
            lb_msg = "<blockquote><tg-emoji emoji-id=\"5240021484516185513\">ðŸ†</tg-emoji> <b>ð—§ð—¢ð—£ ðŸ± ð—Ÿð—˜ð—”ð——ð—˜ð—¥ð—•ð—¢ð—”ð—¥ð—— (TODAY)</b></blockquote>\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            emoji_map = [("1ï¸âƒ£", "5238176680098440792"), ("2ï¸âƒ£", "5237806896299157399"), ("3ï¸âƒ£", "5239965456667812809"), ("4ï¸âƒ£", "5237911487342751418"), ("5ï¸âƒ£", "5240278297790686165")]
            
            if not top_users: 
                lb_msg += "<i>No OTPs received today.</i>\n"
            else:
                for idx, (uid_str, otp_count) in enumerate(top_users):
                    u_data = get_user(int(uid_str))
                    fname = u_data["first_name"] if u_data else "User"
                    emoji_char, emoji_id = emoji_map[idx]
                    lb_msg += f"<blockquote><tg-emoji emoji-id=\"{emoji_id}\">{emoji_char}</tg-emoji> <a href='tg://user?id={uid_str}'>{html.escape(str(fname))}</a> - {otp_count} OTP</blockquote>\n"
            lb_msg += "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”"
            cached_leaderboard_text = lb_msg
            
        except Exception as e:
            pass
        time.sleep(5) # ðŸŒŸ 5 à¦¸à§‡à¦•à§‡à¦¨à§à¦¡ à¦ªà¦°à¦ªà¦° à¦¬à§à¦¯à¦¾à¦•à¦—à§à¦°à¦¾à¦‰à¦¨à§à¦¡à§‡ à¦•à§à¦¯à¦¾à¦¶ à¦°à§‡à¦¡à¦¿ à¦¹à¦¬à§‡

# Admin Settings (DXA Control)
bot_settings = {
    "withdraw_on": True,
    "min_withdraw": 10.0,
    "support_link": "",
    "w_group": "",
    "auto_br_on": False,
    "auto_br_interval": 60,
    "cooldown": 5, # Default 5 seconds
    "num_req": 1, # Default 1 number per request
    "w_methods": ["bKash", "Nagad"],
    "otp_default_rate": 0.5,
    "otp_service_rates": {},
    "main_channel_link": ""
}

BOT_DATA_FILE = "bot_data.json"
USERS_LIST_FILE = "users_list.json"

# ==========================================
# Helper: Get Active Voltx Key & Rates
# ==========================================
def get_api_key():
    return random.choice(voltx_keys) if voltx_keys else API_2OO9_KEY_DEFAULT

def get_otp_reward(service_name):
    rates = bot_settings.get("otp_service_rates", {})
    val = rates.get(service_name, bot_settings.get("otp_default_rate", 0.5))
    return float(val)

def update_daily_stat(key, amount=1):
    global daily_stats
    today = time.strftime("%Y-%m-%d")
    if daily_stats.get("date") != today:
        daily_stats = {"date": today, "numbers": 0, "otps": 0}
    daily_stats[key] = daily_stats.get(key, 0) + amount

# ==========================================
# Local Storage Managers
# ==========================================
def load_local_data():
    global recent_traffic, voltx_dynamic_data, voltx_keys, force_join_status, force_join_channels, voltx_auto_mode, otp_forward_groups, otp_button_link, recent_success_otps, bot_settings, user_active_sessions, daily_stats, daily_user_otps
    if os.path.exists(BOT_DATA_FILE):
        try:
            with open(BOT_DATA_FILE, "r") as f:
                data = json.load(f)
                recent_traffic = data.get("recent_traffic", [])
                voltx_dynamic_data = data.get("voltx_dynamic_data", {})
                loaded_keys = data.get("voltx_keys", [])
                
                if not loaded_keys:
                    voltx_keys = [API_2OO9_KEY_DEFAULT]
                else:
                    voltx_keys = loaded_keys
                    
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
        except Exception as e:
            print(f"Error loading local data: {e}")

def save_local_data():
    global recent_traffic, voltx_dynamic_data, voltx_keys, force_join_status, force_join_channels, voltx_auto_mode, otp_forward_groups, otp_button_link, recent_success_otps, bot_settings, user_active_sessions, daily_stats
    try:
        with open(BOT_DATA_FILE, "w") as f:
            json.dump({
                "recent_traffic": recent_traffic, 
                "voltx_dynamic_data": voltx_dynamic_data,
                "voltx_keys": voltx_keys,
                "force_join_status": force_join_status,
                "force_join_channels": force_join_channels,
                "voltx_auto_mode": voltx_auto_mode,
                "otp_forward_groups": otp_forward_groups,
                "otp_button_link": otp_button_link,
                "recent_success_otps": list(recent_success_otps),
                "bot_settings": bot_settings,
                "user_active_sessions": user_active_sessions,
                "daily_stats": daily_stats,
                "daily_user_otps": daily_user_otps
            }, f)
    except Exception as e:
        print(f"Error saving local data: {e}")
        
    # ðŸŒŸ Firebase à¦ à¦²à¦¾à¦‡à¦­ à¦†à¦ªà¦¡à§‡à¦Ÿ à¦ªà¦¾à¦ à¦¾à¦¨à§‹
    if current_db_mode == "firebase" and db_firebase:
        try:
            db_firebase.collection('settings').document('bot_config').set({
                "bot_settings": bot_settings,
                "force_join_status": force_join_status,
                "force_join_channels": force_join_channels,
                "otp_forward_groups": otp_forward_groups,
                "otp_button_link": otp_button_link,
                "voltx_keys": voltx_keys,
                "voltx_auto_mode": voltx_auto_mode
            }, merge=True)
        except: pass

# à¦—à§à¦²à§‹à¦¬à¦¾à¦² à¦­à§‡à¦°à¦¿à¦¯à¦¼à§‡à¦¬à¦²à§‡ à¦‡à¦‰à¦œà¦¾à¦° à¦²à¦¿à¦¸à§à¦Ÿ à¦•à§à¦¯à¦¾à¦¶ à¦•à¦°à§‡ à¦°à¦¾à¦–à¦¾ à¦¹à¦²à§‹
cached_user_list = set()

def add_to_broadcast_list(user_id):
    global cached_user_list
    if not cached_user_list and os.path.exists(USERS_LIST_FILE):
        try:
            with open(USERS_LIST_FILE, "r") as f:
                cached_user_list = set(json.load(f))
        except: pass
        
    if user_id not in cached_user_list:
        cached_user_list.add(user_id)
        try:
            with open(USERS_LIST_FILE, "w") as f:
                json.dump(list(cached_user_list), f)
        except: pass

def get_all_user_ids():
    global user_cache
    users = set()
    
    # ðŸŒŸ à§§. à¦ªà§à¦°à¦¥à¦®à§‡ RAM Cache à¦¥à§‡à¦•à§‡ à¦¦à§à¦°à§à¦¤ à¦‡à¦‰à¦œà¦¾à¦° à¦¨à¦¿à¦¬à§‡
    for uid in user_cache.keys():
        users.add(int(uid))
        
    # ðŸŒŸ à§¨. à¦à¦°à¦ªà¦° à¦²à§‹à¦•à¦¾à¦² JSON à¦«à¦¾à¦‡à¦² à¦¥à§‡à¦•à§‡ à¦¨à¦¿à¦¬à§‡
    if os.path.exists(USERS_LIST_FILE):
        try:
            with open(USERS_LIST_FILE, "r") as f:
                for u in json.load(f): users.add(int(u))
        except: pass
        
    #RAM à¦¸à¦¬à¦¸à¦®à§Ÿ à¦†à¦ªà¦¡à§‡à¦Ÿà§‡à¦¡ à¦¥à¦¾à¦•à§‡!
    return list(users)

# ==========================================
# Telegram APIs & Force Join Helpers
# ==========================================
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
    if chat_identifier.startswith("https://t.me/"):
        chat_identifier = "@" + chat_identifier.split("/")[-1]
    elif not chat_identifier.startswith("@") and not chat_identifier.startswith("-100"):
        chat_identifier = "@" + chat_identifier
        
    url = BASE_URL + "getChat"
    res = requests.get(url, params={"chat_id": chat_identifier}).json()
    if res.get("ok"):
        chat = res["result"]
        chat_data = {
            "id": chat["id"],
            "username": "@" + chat["username"] if "username" in chat else "",
            "title": chat.get("title", "Private Channel"),
            "invite_link": chat.get("invite_link", "")
        }
        if not chat_data["invite_link"]:
            inv_res = requests.post(BASE_URL + "exportChatInviteLink", json={"chat_id": chat["id"]}).json()
            if inv_res.get("ok"):
                chat_data["invite_link"] = inv_res["result"]
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
            else:
                return False
        except: return False
    return True

# ==========================================
# Global Emojis Map
# ==========================================
GLOBAL_BODY_EMOJIS = {
    "âž–": "5870818207383686839", "ðŸš«": "5334807341109908955", "ðŸ˜’": "5334763399299506604",
    "ðŸ–¥": "5334880948259427772", "ðŸŒ": "5334590977837403844", "ðŸŒŸ": "5337102391244263212",
    "ðŸ•“": "5336983442125001376", "âŒ›": "5337172996211648018", "ðŸ’¬": "5337302974806922068",
    "ðŸ”": "5337255927735163754", "ðŸ": "5337132498965010628", "â”": "5336850036145823599",
    "âš ï¸": "5336944168944047463", "ðŸ”¥": "5337267511261960341", "ðŸ’¸": "5429612421977253466",
    "ðŸ¥š": "5348390922507817684", "ðŸ‘¨â€âš–": "5334763399299506604", "ðŸ": "5348494358205207761",
    "ðŸ§»": "5348486915026884464", "âš—": "5346311574221000149", "ðŸ›´": "5348075478634766440",
    "ðŸ“Š": "5353032893096567467", "ðŸ”¢": "5226929552319594190", "ðŸ‘¤": "5352861489541714456",
    "ðŸ“": "5352721946054268944", "ðŸš€": "5352597830089347330", "ðŸ’Ž": "5352838545826420397",
    "ðŸ“": "5352922460897452503", "ðŸ‘‹": "5353027129250453493", "âœ…": "5352694861990501856",
    "1ï¸âƒ£": "5352651766288652742", "2ï¸âƒ£": "5355186458418257716", "3ï¸âƒ£": "5352867219028091093",
    "4ï¸âƒ£": "5352566657216714037", "5ï¸âƒ£": "5353086880835474989", "6ï¸âƒ£": "5354859211975071385",
    "7ï¸âƒ£": "5352859127309707652", "8ï¸âƒ£": "5352957533600389988", "9ï¸âƒ£": "5353060913463204207",
    "ðŸ”¤": "5352727417842606016", "ðŸ“£": "5352980533150259581", "ðŸ“¤": "5353001161878182134",
    "âœ¨": "5352552689983067014", "ðŸ”¹": "5352638632278660622", "ðŸŽ™": "5355102594886833928",
    "ðŸ’´": "5352985330628730418", "ðŸ“…": "5352585194295564660", "ðŸ“´": "5352974971167611327",
    "âœï¸": "5395444784611480792", "ðŸ“±": "5337132498965010628", "ðŸ”—": "5420517437885943844",
    "âŒ": "5420130255174145507", "âš™ï¸": "5420155432272438703", "ðŸ«‚": "5420145051336485498",
    "âž•": "5420323438508155202", "ðŸ—‘": "5422557736330106570", "ðŸŽ": "5420396762189831222",
    "âž¤": "5420618897898381296", "ðŸ¢": "5420156334215565595", "ðŸ’³": "5190899075968441286",
    "ðŸ“": "5192739271886282680", "ðŸ›¡": "5190447043545438788", "ðŸ¤": "5192805934073685937",
    "ðŸ’°": "5190576863226933563", "ðŸ‘€": "5190645917711114179", "ðŸ•¹": "5193100774988617665",
    "ðŸŸ¢": "5192812028632274956", "ðŸ§ª": "5190781475468915802", "ðŸŽ¨": "5190751148704833975",
    "ðŸ“‚": "5257969839313526622", "ðŸŒ": "5780471598922337683", "ðŸ“Œ": "5318986077455795572",
    "ðŸ“¢": "5789428375261023681", "ðŸ†”": "5226929552319594190", "ðŸ“ˆ": "5352877703043258544",
    "ðŸ””": "5352980533150259581", "ðŸ¦": "5429612421977253466", "ðŸ§¾": "5192739271886282680",
    "ðŸ‘¨â€âš–ï¸": "5334763399299506604", "ðŸ”": "5463352748751753567", "ðŸ”‘": "5197288647275071607",
    "ðŸ†": "5240021484516185513", "ðŸš¦": "5429571662737611814", "ðŸ‘¥": "5420145051336485498", 
    "ðŸŽ¯": "5352922460897452503", "ðŸ“¶": "5429353834881261942", "â³": "5337172996211648018", 
    "ðŸ”¸": "5429576112323732785", "ðŸŽ‰": "5420396762189831222", "ðŸ’µ": "5429612421977253466", 
    "ðŸ‘‘": "5352838545826420397", "â†³": "5420618897898381296",
    "ðŸ‡ºðŸ‡¸": "5913463998522592692", "ðŸ‡ºðŸ‡¦": "5911406692007941050", "ðŸ‡µðŸ‡±": "5913550391789752571",
    "ðŸ‡°ðŸ‡¿": "5913724621433082323", "ðŸ‡¨ðŸ‡³": "5913779335021466780", "ðŸ‡¦ðŸ‡¿": "5911197578640233518",
    "ðŸ‡ªðŸ‡º": "5911106310585193018", "ðŸ‡¦ðŸ‡²": "5913272455866093666", "ðŸ‡·ðŸ‡º": "5913274246867456342",
    "ðŸ‡ºðŸ‡¿": "5911051846104912282", "ðŸ‡©ðŸ‡ª": "5911096835887337583", "ðŸ‡¯ðŸ‡µ": "5913293711659241040",
    "ðŸ‡¹ðŸ‡·": "5910995113881901195", "ðŸ‡§ðŸ‡¾": "5911011185649521599", "ðŸ‡¬ðŸ‡§": "5913443365499703513",
    "ðŸ‡®ðŸ‡³": "5913754823643107921", "ðŸ‡§ðŸ‡·": "5911148568768418614", "ðŸ‡¿ðŸ‡²": "5913564754160389778",
    "ðŸ‡¾ðŸ‡ª": "5913346492512341993", "ðŸ´ó §ó ¢ó ·ó ¬ó ³ó ¿": "5911297801702084799", "ðŸ‡»ðŸ‡³": "5913428887164949581",
    "ðŸ‡»ðŸ‡¦": "5911211932420938860", "ðŸ‡»ðŸ‡º": "5913511535220625585", "ðŸ‡ºðŸ‡¾": "5913623088406204470",
    "ðŸ‡¦ðŸ‡ª": "5913726554168365343", "ðŸ‡ºðŸ‡¬": "5913488939397681980", "ðŸ‡¹ðŸ‡²": "5913315521503170180",
    "ðŸ‡¹ðŸ‡³": "5911332947419468671", "ðŸ‡¹ðŸ‡¹": "5911228635548750294", "ðŸ‡¹ðŸ‡¬": "5913423260757790970",
    "ðŸ‡¹ðŸ‡­": "5913617968805187987", "ðŸ‡¹ðŸ‡¿": "5911418949844603556", "ðŸ‡¹ðŸ‡¯": "5911287639809463107",
    "ðŸ‡¨ðŸ‡­": "5913271227505448072", "ðŸ‡¸ðŸ‡ª": "5911156510162949403", "ðŸ‡¸ðŸ‡¿": "5913374525763883286",
    "ðŸ‡¸ðŸ‡·": "5913275539652611719", "ðŸ‡¸ðŸ‡©": "5911387497799094470", "ðŸ‡ªðŸ‡¸": "5911193287967904547",
    "ðŸ‡±ðŸ‡°": "5911293163137406640", "ðŸ‡¸ðŸ‡¸": "5911406262511211744", "ðŸ‡¿ðŸ‡¦": "5911203119148044594",
    "ðŸ‡¸ðŸ‡´": "5911397852965244436", "ðŸ‡¸ðŸ‡§": "5911482712929080608", "ðŸ‡¸ðŸ‡®": "5913431983836368644",
    "ðŸ‡¸ðŸ‡°": "5913751666842145020", "ðŸ‡¸ðŸ‡¬": "5911531460808051849", "ðŸ‡¸ðŸ‡±": "5911210450657218661",
    "ðŸ‡¸ðŸ‡¨": "5911185183364616913", "ðŸ‡·ðŸ‡¸": "5913592598433369871", "ðŸ‡¸ðŸ‡³": "5910995302860461643",
    "ðŸ´ó §ó ¢ó ³ó £ó ´ó ¿": "5911460091336331851", "ðŸ‡¸ðŸ‡¹": "5913574331937462345", "ðŸ‡¸ðŸ‡²": "5913587968458625465",
    "ðŸ‡¼ðŸ‡¸": "5913325971158602854", "ðŸ‡°ðŸ‡³": "5913691898077253637", "ðŸ‡»ðŸ‡¨": "5911318941531116255",
    "ðŸ‡±ðŸ‡¨": "5911243659344351824", "ðŸ‡µðŸ‡¸": "5913684768431541668", "ðŸ‡·ðŸ‡¼": "5911455229433352234",
    "ðŸ‡·ðŸ‡´": "5913460373570195273", "ðŸ‡¶ðŸ‡¦": "5911260864983339619", "ðŸ‡µðŸ‡·": "5911504350974317480",
    "ðŸ‡µðŸ‡¹": "5911023653939581472", "ðŸ‡µðŸ‡­": "5911268638874145162", "ðŸ‡µðŸ‡ª": "5911207993935925780",
    "ðŸ‡µðŸ‡¾": "5911014265141072316", "ðŸ‡µðŸ‡¬": "5911107251183030903", "ðŸ‡µðŸ‡¦": "5913428968769327174",
    "ðŸ‡µðŸ‡¼": "5911283903187915549", "ðŸ‡µðŸ‡°": "5913705895375672082", "ðŸ‡´ðŸ‡²": "5913570801474343473",
    "ðŸ‡³ðŸ‡´": "5913617397574537046", "ðŸ‡³ðŸ‡¬": "5911143844304393105", "ðŸ‡³ðŸ‡ª": "5911270086278124251",
    "ðŸ‡³ðŸ‡¿": "5913640044937089340", "ðŸ‡³ðŸ‡±": "5913367645226275100", "ðŸ‡³ðŸ‡µ": "5913496520014958723",
    "ðŸ‡³ðŸ‡¦": "5911108535378252443", "ðŸ‡²ðŸ‡¿": "5911333419865871464", "ðŸ‡²ðŸ‡¦": "5911482111633658301",
    "ðŸ‡²ðŸ‡ª": "5913239436157522151", "ðŸ‡²ðŸ‡³": "5911041383564580038", "ðŸ‡²ðŸ‡¨": "5911245347266500057",
    "ðŸ‡²ðŸ‡©": "5913456847402045950", "ðŸ‡²ðŸ‡»": "5913501399097806832", "ðŸ‡²ðŸ‡±": "5911305266355245916",
    "ðŸ‡²ðŸ‡¹": "5911023714069123567", "ðŸ‡§ðŸ‡²": "5913680005312811090", "ðŸ‡²ðŸ‡¶": "5911378005921370347",
    "ðŸ‡²ðŸ‡­": "5913235935759175692", "ðŸ‡²ðŸ‡º": "5913291113204027321", "ðŸ‡²ðŸ‡½": "5913687302462246518",
    "ðŸ‡«ðŸ‡²": "5911271104185373336", "ðŸ‡²ðŸ‡¾": "5913654360063087453", "ðŸ‡°ðŸ‡ª": "5911154710571651231",
    "ðŸ‡²ðŸ‡¬": "5913766918271012920", "ðŸ‡²ðŸ‡°": "5913394029210374721", "ðŸ‡±ðŸ‡º": "5913390842344640293",
    "ðŸ‡±ðŸ‡¹": "5911172315642597775", "ðŸ‡±ðŸ‡®": "5911166650580734660", "ðŸ‡±ðŸ‡¾": "5911236989260140996",
    "ðŸ‡±ðŸ‡·": "5913324167272337727", "ðŸ‡°ðŸ‡®": "5911294443037660118", "ðŸ‡½ðŸ‡°": "5911433681582429010",
    "ðŸ‡°ðŸ‡¼": "5913290705182134003", "ðŸ‡°ðŸ‡¬": "5911202161370337549", "ðŸ‡±ðŸ‡¦": "5913718526874489279",
    "ðŸ‡±ðŸ‡»": "5913738489882480243", "ðŸ‡±ðŸ‡§": "5911504273664905447", "ðŸ‡±ðŸ‡¸": "5911059881988723711",
    "ðŸ‡®ðŸ‡©": "5913479361620611038", "ðŸ‡®ðŸ‡·": "5911308891307643032", "ðŸ‡®ðŸ‡¶": "5911382442622587735",
    "ðŸ‡®ðŸ‡ª": "5913440715504881532", "ðŸ‡®ðŸ‡±": "5911471936856134692", "ðŸ‡®ðŸ‡¹": "5913688444923547525",
    "ðŸ‡¯ðŸ‡²": "5913232280742006526", "ðŸ‡¯ðŸ‡´": "5913234136167878475", "ðŸ‡®ðŸ‡¸": "5911047899029967246",
    "ðŸ‡­ðŸ‡º": "5913767635530551104", "ðŸ‡­ðŸ‡³": "5911406889576436289", "ðŸ‡­ðŸ‡¹": "5913459789454643194",
    "ðŸ‡¬ðŸ‡¾": "5913579412883771480", "ðŸ‡¬ðŸ‡¼": "5911398694778836149", "ðŸ‡¬ðŸ‡³": "5913471858312744319",
    "ðŸ‡¬ðŸ‡¹": "5913324858762072330", "ðŸ‡¬ðŸ‡©": "5913228063084121946", "ðŸ‡¬ðŸ‡·": "5911210399117611448",
    "ðŸ‡¬ðŸ‡­": "5913391155877252952", "ðŸ‡¬ðŸ‡ª": "5913434771270144023", "ðŸ‡¬ðŸ‡²": "5913657267755945883",
    "ðŸ‡¬ðŸ‡¦": "5911037896051137264", "ðŸ‡«ðŸ‡·": "5913605586414473124", "ðŸ‡«ðŸ‡®": "5911041344909873378",
    "ðŸ‡«ðŸ‡¯": "5911393832875856716", "ðŸ‡ªðŸ‡¹": "5911078333168227043", "ðŸ‡©ðŸ‡´": "5911152099231536123",
    "ðŸ‡¹ðŸ‡±": "5911141915864076479", "ðŸ‡ªðŸ‡¨": "5911273865849347408", "ðŸ‡ªðŸ‡¬": "5913694831539916769",
    "ðŸ‡¸ðŸ‡»": "5913238624408703010", "ðŸ´ó §ó ¢ó ¥ó ®ó §ó ¿": "5913475719488344315", "ðŸ‡ªðŸ‡ª": "5910986042910969906",
    "ðŸ‡©ðŸ‡²": "5911377121158107430", "ðŸ‡©ðŸ‡¯": "5911407709915190157", "ðŸ‡©ðŸ‡°": "5911206009661034712",
    "ðŸ‡¨ðŸ‡¾": "5911023550860366409", "ðŸ‡­ðŸ‡·": "5913692684056269311", "ðŸ‡¨ðŸ‡·": "5911261745451635030",
    "ðŸ‡¨ðŸ‡¬": "5911338788574990168", "ðŸ‡¨ðŸ‡©": "5913770362834783827", "ðŸ‡°ðŸ‡²": "5911338582416560604",
    "ðŸ‡°ðŸ‡­": "5913699998385573485", "ðŸ‡¨ðŸ‡²": "5911172109484167745", "ðŸ‡¨ðŸ‡¦": "5913623736946265914",
    "ðŸ‡¨ðŸ‡»": "5913571501554012193", "ðŸ‡¨ðŸ‡«": "5913443245240619222", "ðŸ‡¹ðŸ‡©": "5913299849167507310",
    "ðŸ‡¨ðŸ‡¿": "5911198691036764307", "ðŸ‡¨ðŸ‡±": "5911470957603592832", "ðŸ‡¨ðŸ‡´": "5913773060074246009",
    "ðŸ‡§ðŸ‡®": "5913766441529642752", "ðŸ‡§ðŸ‡¼": "5911513782722499475", "ðŸ‡§ðŸ‡¦": "5913700002680541032",
    "ðŸ‡§ðŸ‡´": "5913638795101606133", "ðŸ‡§ðŸ‡¹": "5913236734623093021", "ðŸ‡§ðŸ‡¯": "5913735869952430547",
    "ðŸ‡¦ðŸ‡·": "5913573356979884082", "ðŸ‡¦ðŸ‡º": "5913632326880858455", "ðŸ‡¦ðŸ‡¹": "5911338831524664592",
    "ðŸ‡§ðŸ‡¸": "5911451643135660214", "ðŸ‡§ðŸ‡­": "5913581663446634403", "ðŸ‡§ðŸ‡©": "5911365056594973179",
    "ðŸ‡§ðŸ‡§": "5911016996740272263", "ðŸ‡§ðŸ‡ª": "5913529642802745141", "ðŸ‡§ðŸ‡¿": "5913355005137522807",
    "ðŸ‡¦ðŸ‡¬": "5913389025573475085", "ðŸ‡¦ðŸ‡´": "5913753316109586411", "ðŸ‡¦ðŸ‡©": "5911314702398396902",
    "ðŸ‡©ðŸ‡¿": "5913782968563800236", "ðŸ‡¦ðŸ‡±": "5911357458797826163", "ðŸ‡¦ðŸ‡«": "5913492040364068694",
    "ðŸ‡¿ðŸ‡¼": "5911092502265336396", "ðŸ‡¨ðŸ‡º": "5431551436502611633", "ðŸ‡°ðŸ‡µ": "5434142701941437163",
    "ðŸ‡»ðŸ‡ª": "5434009132753499322", "ðŸ‡¸ðŸ‡¾": "5433910876786670092", "ðŸ‡²ðŸ‡²": "5433666360003540231",
    "ðŸ‡³ðŸ‡®": "5334807849418003620", "ðŸ‡°ðŸ‡·": "5913371673905598425", "ðŸ‡¬ðŸ‡¶": "5911306279967529251",
    "ðŸ‡¬ðŸ‡±": "5292014752283774878", "ðŸ‡«ðŸ‡´": "5296469342039327674", "ðŸ‡¨ðŸ‡®": "5222233374948602940",
    "ðŸ‡§ðŸ‡³": "5911336409163109113", "ðŸ‡§ðŸ‡¬": "5294329219965272288", "ðŸ‡§ðŸ‡«": "5913407764515786948",
    "ðŸ‡ªðŸ‡·": "5433723401464198287", "ðŸ‡²ðŸ‡¼": "5433968339154122439", "ðŸ‡²ðŸ‡·": "5433859405898594234",
    "ðŸ‡³ðŸ‡·": "5434131139889478358", "ðŸ‡¸ðŸ‡¦": "4985897134424328239", "ðŸ‡¹ðŸ‡´": "5433640100573491806",
    "ðŸ‡¹ðŸ‡»": "5433684690923961019", "ðŸ‡¹ðŸ‡¼": "5366187256937726720", "ðŸ‡­ðŸ‡°": "5292166459118606932",
    "ðŸ‡²ðŸ‡´": "6323557758096377611"
}

def apply_emojis(text):
    hidden = []
    def hide(match):
        hidden.append(match.group(0))
        return f"__TG_EMOJI_{len(hidden)-1}__"
    text = re.sub(r'<tg-emoji[^>]*>.*?</tg-emoji>', hide, text)
    for char, eid in GLOBAL_BODY_EMOJIS.items():
        text = text.replace(char, f'<tg-emoji emoji-id="{eid}">{char}</tg-emoji>')
    for i, h in enumerate(hidden):
        text = text.replace(f"__TG_EMOJI_{i}__", h)
    return text

# ==========================================
# Premium Apps & Service Keywords Setup
# ==========================================
PREMIUM_APPS = {
    "Facebook": {"emoji": "ðŸ“˜", "id": "5429172110520003976"},
    "WhatsApp": {"emoji": "ðŸ’¬", "id": "5429612632430654504"},
    "Telegram": {"emoji": "âœˆï¸", "id": "5429136513831057777"},
    "Instagram": {"emoji": "ðŸ“¸", "id": "5429478178479447442"},
    "Google": {"emoji": "ðŸ”", "id": "5429558795015593080"},
    "Microsoft": {"emoji": "ðŸªŸ", "id": "5979047775470358891"},
    "TikTok": {"emoji": "ðŸŽµ", "id": "5429132656950419591"},
    "Bkash": {"emoji": "ðŸ¦", "id": "5431552076452766597"},
    "Binance": {"emoji": "ðŸ’±", "id": "5429438106434575354"},
    "Snapchat": {"emoji": "ðŸ‘»", "id": "5429398137468919845"},
    "Uber": {"emoji": "ðŸš—", "id": "5298715455316303708"},
    "Discord": {"emoji": "ðŸŽ¬", "id": "5429594374524676604"},
    "Amazon": {"emoji": "ðŸŒŸ", "id": "5431358656895568355"},
    "Viber": {"emoji": "ðŸ’œ", "id": "5429470576387335368"},
    "Twitter": {"emoji": "ðŸ¦", "id": "5431899135580087595"},
    "Netflix": {"emoji": "ðŸŽ¥", "id": "5431641055290235797"},
    "Spotify": {"emoji": "ðŸŽµ", "id": "5429235839244739644"},
    "Foodpanda": {"emoji": "ðŸ¼", "id": "5336879280578138635"},
    "Pathao": {"emoji": "ðŸ›µ", "id": "5336879280578138635"},
    "ChatGPT": {"emoji": "ðŸ¤–", "id": "5429503209548847635"},
    "Imo": {"emoji": "ðŸ’­", "id": "5431378937731129128"},
    "Other": {"emoji": "ðŸ“¶", "id": "5429353834881261942"}
}

SERVICE_SMS_KEYWORDS = {
    "Facebook": ["facebook", "fb code", "fb", "meta"],
    "WhatsApp": ["whats", "whatsapp", "whatsapp code"],
    "Telegram": ["telegram", "tg code"],
    "Instagram": ["instagram", "ig code"],
    "Google": ["google", "Googl"],
    "Microsoft": ["microsoft", "micro", "Microsof", "xbox"],
    "TikTok": ["tiktok", "tik tok"],
    "Bkash": ["bkash"],
    "Binance": ["binance", "bnb"],
    "Snapchat": ["snapchat", "snap"],
    "Uber": ["uber"],
    "Discord": ["discord"],
    "Amazon": ["amazon", "aws"],
    "Viber": ["viber"],
    "Twitter": ["twitter", "x.com"],
    "Netflix": ["netflix"],
    "Spotify": ["spotify"],
    "Foodpanda": ["foodpanda", "panda"],
    "Pathao": ["pathao"],
    "ChatGPT": ["openai", "chatgpt"],
    "Imo": ["imo code", "imo"]
}

COUNTRY_CODES = {
    "1": "ðŸ‡ºðŸ‡¸ USA/Canada", "380": "ðŸ‡ºðŸ‡¦ Ukraine", "48": "ðŸ‡µðŸ‡± Poland", "7": "ðŸ‡°ðŸ‡¿ Kazakhstan",
    "86": "ðŸ‡¨ðŸ‡³ China", "994": "ðŸ‡¦ðŸ‡¿ Azerbaijan", "374": "ðŸ‡¦ðŸ‡² Armenia", "79": "ðŸ‡·ðŸ‡º Russia",
    "998": "ðŸ‡ºðŸ‡¿ Uzbekistan", "49": "ðŸ‡©ðŸ‡ª Germany", "81": "ðŸ‡¯ðŸ‡µ Japan", "90": "ðŸ‡¹ðŸ‡· Turkey",
    "375": "ðŸ‡§ðŸ‡¾ Belarus", "44": "ðŸ‡¬ðŸ‡§ United Kingdom", "91": "ðŸ‡®ðŸ‡³ India", "55": "ðŸ‡§ðŸ‡· Brazil",
    "260": "ðŸ‡¿ðŸ‡² Zambia", "967": "ðŸ‡¾ðŸ‡ª Yemen", "84": "ðŸ‡»ðŸ‡³ Vietnam", "379": "ðŸ‡»ðŸ‡¦ Vatican City",
    "678": "ðŸ‡»ðŸ‡º Vanuatu", "598": "ðŸ‡ºðŸ‡¾ Uruguay", "971": "ðŸ‡¦ðŸ‡ª UAE", "256": "ðŸ‡ºðŸ‡¬ Uganda",
    "993": "ðŸ‡¹ðŸ‡² Turkmenistan", "216": "ðŸ‡¹ðŸ‡³ Tunisia", "228": "ðŸ‡¹ðŸ‡¬ Togo", "66": "ðŸ‡¹ðŸ‡­ Thailand",
    "255": "ðŸ‡¹ðŸ‡¿ Tanzania", "992": "ðŸ‡¹ðŸ‡¯ Tajikistan", "41": "ðŸ‡¨ðŸ‡­ Switzerland", "46": "ðŸ‡¸ðŸ‡ª Sweden",
    "268": "ðŸ‡¸ðŸ‡¿ Eswatini", "597": "ðŸ‡¸ðŸ‡· Suriname", "249": "ðŸ‡¸ðŸ‡© Sudan", "34": "ðŸ‡ªðŸ‡¸ Spain",
    "94": "ðŸ‡±ðŸ‡° Sri Lanka", "211": "ðŸ‡¸ðŸ‡¸ South Sudan", "27": "ðŸ‡¿ðŸ‡¦ South Africa", "252": "ðŸ‡¸ðŸ‡´ Somalia",
    "677": "ðŸ‡¸ðŸ‡§ Solomon Islands", "386": "ðŸ‡¸ðŸ‡® Slovenia", "421": "ðŸ‡¸ðŸ‡° Slovakia", "65": "ðŸ‡¸ðŸ‡¬ Singapore",
    "232": "ðŸ‡¸ðŸ‡± Sierra Leone", "248": "ðŸ‡¸ðŸ‡¨ Seychelles", "381": "ðŸ‡·ðŸ‡¸ Serbia", "221": "ðŸ‡¸ðŸ‡³ Senegal",
    "239": "ðŸ‡¸ðŸ‡¹ Sao Tome", "378": "ðŸ‡¸ðŸ‡² San Marino", "685": "ðŸ‡¼ðŸ‡¸ Samoa", "970": "ðŸ‡µðŸ‡¸ Palestine",
    "250": "ðŸ‡·ðŸ‡¼ Rwanda", "40": "ðŸ‡·ðŸ‡´ Romania", "974": "ðŸ‡¶ðŸ‡¦ Qatar", "351": "ðŸ‡µðŸ‡¹ Portugal",
    "63": "ðŸ‡µðŸ‡­ Philippines", "51": "ðŸ‡µðŸ‡ª Peru", "595": "ðŸ‡µðŸ‡¾ Paraguay", "675": "ðŸ‡µðŸ‡¬ Papua New Guinea",
    "507": "ðŸ‡µðŸ‡¦ Panama", "680": "ðŸ‡µðŸ‡¼ Palau", "92": "ðŸ‡µðŸ‡° Pakistan", "968": "ðŸ‡´ðŸ‡² Oman",
    "47": "ðŸ‡³ðŸ‡´ Norway", "234": "ðŸ‡³ðŸ‡¬ Nigeria", "227": "ðŸ‡³ðŸ‡ª Niger", "64": "ðŸ‡³ðŸ‡¿ New Zealand",
    "31": "ðŸ‡³ðŸ‡± Netherlands", "977": "ðŸ‡³ðŸ‡µ Nepal", "264": "ðŸ‡³ðŸ‡¦ Namibia", "258": "ðŸ‡²ðŸ‡¿ Mozambique",
    "212": "ðŸ‡²ðŸ‡¦ Morocco", "382": "ðŸ‡²ðŸ‡ª Montenegro", "976": "ðŸ‡²ðŸ‡³ Mongolia", "377": "ðŸ‡²ðŸ‡¨ Monaco",
    "373": "ðŸ‡²ðŸ‡© Moldova", "960": "ðŸ‡²ðŸ‡» Maldives", "223": "ðŸ‡²ðŸ‡± Mali", "356": "ðŸ‡²ðŸ‡¹ Malta",
    "596": "ðŸ‡²ðŸ‡¶ Martinique", "692": "ðŸ‡²ðŸ‡­ Marshall Islands", "230": "ðŸ‡²ðŸ‡º Mauritius", "52": "ðŸ‡²ðŸ‡½ Mexico",
    "691": "ðŸ‡«ðŸ‡² Micronesia", "60": "ðŸ‡²ðŸ‡¾ Malaysia", "254": "ðŸ‡°ðŸ‡ª Kenya", "261": "ðŸ‡²ðŸ‡¬ Madagascar",
    "389": "ðŸ‡²ðŸ‡° North Macedonia", "352": "ðŸ‡±ðŸ‡º Luxembourg", "370": "ðŸ‡±ðŸ‡¹ Lithuania", "423": "ðŸ‡±ðŸ‡® Liechtenstein",
    "218": "ðŸ‡±ðŸ‡¾ Libya", "231": "ðŸ‡±ðŸ‡· Liberia", "686": "ðŸ‡°ðŸ‡® Kiribati", "383": "ðŸ‡½ðŸ‡° Kosovo",
    "965": "ðŸ‡°ðŸ‡¼ Kuwait", "996": "ðŸ‡°ðŸ‡¬ Kyrgyzstan", "856": "ðŸ‡±ðŸ‡¦ Laos", "371": "ðŸ‡±ðŸ‡» Latvia",
    "961": "ðŸ‡±ðŸ‡§ Lebanon", "266": "ðŸ‡±ðŸ‡¸ Lesotho", "62": "ðŸ‡®ðŸ‡© Indonesia", "98": "ðŸ‡®ðŸ‡· Iran",
    "964": "ðŸ‡®ðŸ‡¶ Iraq", "353": "ðŸ‡®ðŸ‡ª Ireland", "972": "ðŸ‡®ðŸ‡± Israel", "39": "ðŸ‡®ðŸ‡¹ Italy",
    "962": "ðŸ‡¯ðŸ‡´ Jordan", "354": "ðŸ‡®ðŸ‡¸ Iceland", "36": "ðŸ‡­ðŸ‡º Hungary", "504": "ðŸ‡­ðŸ‡³ Honduras",
    "509": "ðŸ‡­ðŸ‡¹ Haiti", "592": "ðŸ‡¬ðŸ‡¾ Guyana", "245": "ðŸ‡¬ðŸ‡¼ Guinea-Bissau", "224": "ðŸ‡¬ðŸ‡³ Guinea",
    "502": "ðŸ‡¬ðŸ‡¹ Guatemala", "30": "ðŸ‡¬ðŸ‡· Greece", "233": "ðŸ‡¬ðŸ‡­ Ghana", "995": "ðŸ‡¬ðŸ‡ª Georgia",
    "220": "ðŸ‡¬ðŸ‡² Gambia", "241": "ðŸ‡¬ðŸ‡¦ Gabon", "33": "ðŸ‡«ðŸ‡· France", "358": "ðŸ‡«ðŸ‡® Finland",
    "679": "ðŸ‡«ðŸ‡¯ Fiji", "251": "ðŸ‡ªðŸ‡¹ Ethiopia", "670": "ðŸ‡¹ðŸ‡± Timor-Leste", "593": "ðŸ‡ªðŸ‡¨ Ecuador",
    "20": "ðŸ‡ªðŸ‡¬ Egypt", "503": "ðŸ‡¸ðŸ‡» El Salvador", "372": "ðŸ‡ªðŸ‡ª Estonia", "253": "ðŸ‡©ðŸ‡¯ Djibouti",
    "45": "ðŸ‡©ðŸ‡° Denmark", "357": "ðŸ‡¨ðŸ‡¾ Cyprus", "385": "ðŸ‡­ðŸ‡· Croatia", "506": "ðŸ‡¨ðŸ‡· Costa Rica",
    "242": "ðŸ‡¨ðŸ‡¬ Congo", "243": "ðŸ‡¨ðŸ‡© DR Congo", "269": "ðŸ‡°ðŸ‡² Comoros", "855": "ðŸ‡°ðŸ‡­ Cambodia",
    "237": "ðŸ‡¨ðŸ‡² Cameroon", "238": "ðŸ‡¨ðŸ‡» Cape Verde", "236": "ðŸ‡¨ðŸ‡« CAR", "235": "ðŸ‡¹ðŸ‡© Chad",
    "420": "ðŸ‡¨ðŸ‡¿ Czechia", "56": "ðŸ‡¨ðŸ‡± Chile", "57": "ðŸ‡¨ðŸ‡´ Colombia", "257": "ðŸ‡§ðŸ‡® Burundi",
    "267": "ðŸ‡§ðŸ‡¼ Botswana", "387": "ðŸ‡§ðŸ‡¦ Bosnia", "591": "ðŸ‡§ðŸ‡´ Bolivia", "975": "ðŸ‡§ðŸ‡¹ Bhutan",
    "229": "ðŸ‡§ðŸ‡¯ Benin", "54": "ðŸ‡¦ðŸ‡· Argentina", "61": "ðŸ‡¦ðŸ‡º Australia", "43": "ðŸ‡¦ðŸ‡¹ Austria",
    "973": "ðŸ‡§ðŸ‡­ Bahrain", "880": "ðŸ‡§ðŸ‡© Bangladesh", "32": "ðŸ‡§ðŸ‡ª Belgium", "501": "ðŸ‡§ðŸ‡¿ Belize",
    "244": "ðŸ‡¦ðŸ‡´ Angola", "376": "ðŸ‡¦ðŸ‡© Andorra", "213": "ðŸ‡©ðŸ‡¿ Algeria", "355": "ðŸ‡¦ðŸ‡± Albania",
    "93": "ðŸ‡¦ðŸ‡« Afghanistan", "263": "ðŸ‡¿ðŸ‡¼ Zimbabwe", "53": "ðŸ‡¨ðŸ‡º Cuba", "850": "ðŸ‡°ðŸ‡µ North Korea",
    "58": "ðŸ‡»ðŸ‡ª Venezuela", "963": "ðŸ‡¸ðŸ‡¾ Syria", "95": "ðŸ‡²ðŸ‡² Myanmar", "505": "ðŸ‡³ðŸ‡® Nicaragua",
    "82": "ðŸ‡°ðŸ‡· South Korea", "240": "ðŸ‡¬ðŸ‡¶ Equatorial Guinea", "299": "ðŸ‡¬ðŸ‡± Greenland", "298": "ðŸ‡«ðŸ‡´ Faroe Islands",
    "225": "ðŸ‡¨ðŸ‡® Ivory Coast", "673": "ðŸ‡§ðŸ‡³ Brunei", "359": "ðŸ‡§ðŸ‡¬ Bulgaria", "226": "ðŸ‡§ðŸ‡« Burkina Faso",
    "291": "ðŸ‡ªðŸ‡· Eritrea", "265": "ðŸ‡²ðŸ‡¼ Malawi", "222": "ðŸ‡²ðŸ‡· Mauritania", "674": "ðŸ‡³ðŸ‡· Nauru",
    "966": "ðŸ‡¸ðŸ‡¦ Saudi Arabia", "676": "ðŸ‡¹ðŸ‡´ Tonga", "688": "ðŸ‡¹ðŸ‡» Tuvalu", "886": "ðŸ‡¹ðŸ‡¼ Taiwan",
    "852": "ðŸ‡­ðŸ‡° Hong Kong", "853": "ðŸ‡²ðŸ‡´ Macau", "297": "ðŸ‡¦ðŸ‡¼ Aruba", "599": "ðŸ‡¨ðŸ‡¼ Curacao",
    "500": "ðŸ‡«ðŸ‡° Falkland Islands", "594": "ðŸ‡¬ðŸ‡« French Guiana", "590": "ðŸ‡¬ðŸ‡µ Guadeloupe", "262": "ðŸ‡·ðŸ‡ª Reunion",
    "687": "ðŸ‡³ðŸ‡¨ New Caledonia", "683": "ðŸ‡³ðŸ‡º Niue", "672": "ðŸ‡³ðŸ‡« Norfolk Island", "681": "ðŸ‡¼ðŸ‡« Wallis and Futuna",
    "682": "ðŸ‡¨ðŸ‡° Cook Islands", "689": "ðŸ‡µðŸ‡« French Polynesia", "350": "ðŸ‡¬ðŸ‡® Gibraltar", "508": "ðŸ‡µðŸ‡² Saint Pierre"
}

def get_country_info(range_str):
    clean_range = str(range_str or "").replace("X", "")
    for code, name in sorted(COUNTRY_CODES.items(), key=lambda x: len(x[0]), reverse=True):
        if clean_range.startswith(code): return code, name
    return clean_range[:3], f"ðŸ³ï¸ Other (+{clean_range[:3]})"

# ==========================================
# OTP Forwarding Pipeline 
# ==========================================

def detect_service(message_text, raw_sid=""):
    msg_lower = str(message_text).lower()
    sid_lower = str(raw_sid).lower()
    
    for service, keywords in SERVICE_SMS_KEYWORDS.items():
        for kw in keywords:
            if re.search(rf'\b{re.escape(kw)}\b', msg_lower) or kw in msg_lower:
                return service
                
    for service in PREMIUM_APPS.keys():
        if service.lower() in sid_lower:
            return service
            
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
    # ðŸŒŸ à¦¸à§à¦ªà§‡à¦¸ à¦¬à¦¾ à¦¹à¦¾à¦‡à¦«à§‡à¦¨à¦¸à¦¹ à§©-à§® à¦¡à¦¿à¦œà¦¿à¦Ÿà§‡à¦° à¦•à§‹à¦¡ à¦§à¦°à¦¾à¦° à¦²à¦œà¦¿à¦•
    match = re.search(r'\b(\d{3}[\s-]?\d{3,4}|\d{4,8})\b', str(message_text))
    if match: return match.group(1)
    return "COPY"

def deliver_to_inbox(user_id, service_name, raw_number, msg_text, current_balance, reward):
    c_code, c_name = get_country_info(raw_number)
    service_html, srv_eid = get_service_info_html(service_name)
    clean_raw_number = str(raw_number).lstrip('+') 
    
    text = (
        f"â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”\n"
        f"<blockquote>{service_html} <code>+{clean_raw_number}</code></blockquote>\n"
        f"<blockquote><tg-emoji emoji-id=\"5420323438508155202\">âž•</tg-emoji> <b>ADDED</b>  âžœ {reward:.2f} TK</blockquote>\n"
        f"<blockquote><tg-emoji emoji-id=\"5190899075968441286\">ðŸ’³</tg-emoji> <b>BALANCE</b> âžœ {current_balance:.2f} TK</blockquote>\n"
        f"â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”"
    )
    otp = extract_otp_code(msg_text)
    markup = {"inline_keyboard": [[{"text": f"{otp}", "icon_custom_emoji_id": srv_eid, "copy_text": {"text": otp}, "style": "success"}]]}
    send_message(user_id, text, reply_markup=markup)

def generate_otp_display(service_name, raw_number, message_text):
    c_code, c_name = get_country_info(raw_number)
    
    parts = c_name.split(" ", 1)
    country_emoji = parts[0]
    
    if len(raw_number) > 6:
        masked_number = f"{raw_number[:3]}DXA{raw_number[-3:]}"
    else:
        masked_number = raw_number
        
    service_html, srv_eid = get_service_info_html(service_name)
    
    text = (
        f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        f"{service_html} âžœ {country_emoji} <code>{html.escape(masked_number)}</code>\n"
        f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”"
    )
    
    otp = extract_otp_code(message_text)
    
    # ðŸŒŸ à¦°à§‡à¦žà§à¦œ à¦¬à§‡à¦° à¦•à¦°à¦¾à¦° à¦²à¦œà¦¿à¦• (à¦¡à¦¿à¦«à¦²à§à¦Ÿ à§« à¦¡à¦¿à¦œà¦¿à¦Ÿ)
    clean_range = str(raw_number)[:5] if len(str(raw_number)) >= 5 else str(raw_number)
    deep_link = f"https://t.me/{BOT_USERNAME}?start=alloc_{clean_range}_{service_name.lower()}"
    
    markup = {"inline_keyboard": []}
    
    # ðŸŒŸ à¦ªà§à¦°à¦¥à¦® à¦²à¦¾à¦‡à¦¨ (CHANNEL à¦à¦¬à¦‚ OTP)
    row1 = []
    main_channel_link = bot_settings.get("main_channel_link", "")
    if main_channel_link:
        row1.append({"text": "ð—–ð—›ð—”ð—¡ð—¡ð—˜ð—Ÿ", "url": main_channel_link, "icon_custom_emoji_id": "5429353834881261942", "style": "primary"})
        
    row1.append({"text": f"{otp}", "icon_custom_emoji_id": srv_eid, "copy_text": {"text": otp}, "style": "success"})
    
    markup["inline_keyboard"].append(row1)
    
    # ðŸŒŸ à¦¦à§à¦¬à¦¿à¦¤à§€à§Ÿ à¦²à¦¾à¦‡à¦¨ (GET NUMBER)
    markup["inline_keyboard"].append([
        {"text": "GET NUMBER", "url": deep_link, "icon_custom_emoji_id": "5429167978761461870", "style": "danger"}
    ])
    
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

# ==========================================
# 2oo9 API & Background Listeners
# ==========================================
def fetch_live_access():
    headers = {"mauthapi": get_api_key()}
    try:
        res = requests.get(f"{API_2OO9_BASE}/liveaccess", headers=headers, timeout=10)
        data = res.json()
        if data.get("meta", {}).get("code") == 200:
            return data.get("data", {}).get("services", [])
    except: pass
    return []

def fetch_live_number(rid):
    headers = {"mauthapi": get_api_key(), "Content-Type": "application/json"}
    payload = {"rid": str(rid)}
    try:
        res = requests.post(f"{API_2OO9_BASE}/getnum", headers=headers, json=payload, timeout=10)
        data = res.json()
        if data.get("meta", {}).get("code") == 200:
            return data.get("data", {})
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
                            
                            if detected_sid not in voltx_dynamic_data:
                                voltx_dynamic_data[detected_sid] = {"emoji_id": emoji_id, "normal_emoji": normal_emoji, "ranges": {}}
                            if raw_range not in voltx_dynamic_data[detected_sid]["ranges"]:
                                voltx_dynamic_data[detected_sid]["ranges"][raw_range] = {"last_seen": current_time, "hits": 0}
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
                    if "data" in data and isinstance(data["data"], list): 
                        otps = data["data"]
                    elif "data" in data and isinstance(data["data"], dict):
                        if "otps" in data["data"]: 
                            otps = data["data"]["otps"]
                        elif "hits" in data["data"]: 
                            otps = data["data"]["hits"]
                    elif "otps" in data: 
                        otps = data["otps"]
                    elif "hits" in data: 
                        otps = data["hits"]
                elif isinstance(data, list):
                    otps = data
                    
                for otp_data in reversed(otps):
                    msg_text = str(otp_data.get("message", otp_data.get("sms", otp_data.get("code", ""))))
                    raw_number = str(otp_data.get("number", otp_data.get("phone", "")))
                    raw_service = str(otp_data.get("sid", otp_data.get("service", "Unknown")))
                    
                    if not msg_text or not raw_number: continue
                    
                    sig = f"{raw_number}_{msg_text}"
                    detected_service = detect_service(msg_text, raw_service)
                    
                    # 1. Forward to Groups (RAM only tracking - resets on restart)
                    if sig not in group_sent_otps:
                        group_sent_otps.add(sig)
                        if otp_forward_groups:
                            formatted_message, markup = generate_otp_display(detected_service, raw_number, msg_text)
                            send_otp_to_groups(formatted_message, markup)
                    
                    # 2. Check Inbox Ownership (Strictly persistent tracking)
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
                            
                            # ðŸŒŸ à¦‡à¦¨à¦¬à¦•à§à¦¸à§‡ à¦®à§‡à¦¸à§‡à¦œ à¦ªà¦¾à¦ à¦¾à¦¨à§‹à¦° à¦«à¦¾à¦‚à¦¶à¦¨ à¦•à¦² à¦•à¦°à¦¾ à¦¹à¦²à§‹
                            user_balance = get_user(owner_id).get("balance", 0.0)
                            deliver_to_inbox(owner_id, detected_service, raw_number, msg_text, user_balance, reward)
                            
                            today_date = time.strftime("%Y-%m-%d")
                            if daily_user_otps.get("date") != today_date:
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
            if len(group_sent_otps) > 2000:
                group_sent_otps = set(list(group_sent_otps)[-1000:])
        except Exception:
            pass
        time.sleep(10)

# ==========================================
# Hybrid Database Initialization
# ==========================================
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
        if count % 400 != 0: batch.commit()
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()
        user_cache.clear()
    except Exception as e: print(f"Migration Error: {e}")

def init_firebase_from_file():
    global current_db_mode, db_firebase, bot_settings, force_join_status, force_join_channels, otp_forward_groups, otp_button_link, voltx_keys, voltx_auto_mode
    if os.path.exists("temp_firebase.json"):
        try:
            if not firebase_admin._apps: 
                firebase_admin.initialize_app(credentials.Certificate("temp_firebase.json"))
            db_firebase = firestore.client()
            current_db_mode = "firebase"
            print("âœ… Firebase Auto-Connected on Startup!")
            
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
                print("âœ… Settings synced from Firebase!")

            # ðŸŒŸ One-Time Sync on Startup (à¦¬à¦Ÿ à¦šà¦¾à¦²à§ à¦¹à¦“à§Ÿà¦¾à¦° à¦¸à¦®à§Ÿ à¦…à¦Ÿà§‹ à¦¸à¦¿à¦™à§à¦•)
            try:
                local_users = set()
                if os.path.exists(USERS_LIST_FILE):
                    with open(USERS_LIST_FILE, "r") as f:
                        local_users = set(json.load(f))
                
                docs = db_firebase.collection('users').select([]).stream()
                fb_users = set(int(doc.id) for doc in docs)
                
                combined_users = local_users.union(fb_users)
                if len(combined_users) > len(local_users):
                    with open(USERS_LIST_FILE, "w") as f:
                        json.dump(list(combined_users), f)
                    print(f"âœ… Auto-Synced {len(fb_users)} users on Startup!")
            except Exception as e:
                print(f"Startup Sync Error: {e}")

        except Exception as e:
            print(f"âŒ Firebase Auto-Connect Error: {e}")

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
        cursor.execute("SELECT first_name, balance, total_invites FROM users WHERE user_id = ?", (user_id,))
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
        cursor.execute("INSERT OR IGNORE INTO users (user_id, first_name, balance, total_invites) VALUES (?, ?, 0.0, 0)", (user_id, first_name))
        cursor.execute("UPDATE users SET first_name = ? WHERE user_id = ?", (first_name, user_id))
        conn.commit()
        conn.close()
        if user_id not in user_cache: user_cache[user_id] = {"user_id": user_id, "first_name": first_name, "balance": 0.0, "total_invites": 0}
        else: user_cache[user_id]["first_name"] = first_name

def update_user_stats(user_id, balance_add, invite_add):
    global current_db_mode, db_firebase, user_cache
    bal_add = float(balance_add)
    inv_add = int(invite_add)
    
    if user_id not in user_cache:
        get_user(user_id) # Ensure user is loaded
        
    if user_id in user_cache:
        user_cache[user_id]["balance"] = round(user_cache[user_id]["balance"] + bal_add, 2) # ðŸŒŸ Fix: Round balance
        user_cache[user_id]["total_invites"] += inv_add
        
    if current_db_mode == "firebase" and db_firebase:
        db_firebase.collection('users').document(str(user_id)).update({"balance": firestore.Increment(bal_add), "total_invites": firestore.Increment(inv_add)})
    else: 
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ?, total_invites = total_invites + ? WHERE user_id = ?", (bal_add, inv_add, user_id))
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
        cursor.execute("SELECT user_id, first_name, balance FROM users ORDER BY balance DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows

# ==========================================
# Sub-Menu Builders
# ==========================================
def get_otp_group_keyboard():
    kb = {"inline_keyboard": []}
    
    link_display = otp_button_link if otp_button_link else "Not Set"
    if len(link_display) > 25: link_display = link_display[:25] + "..."
    kb["inline_keyboard"].append([{"text": f"Link: {link_display}", "callback_data": "edit_otp_link", "icon_custom_emoji_id": "5420517437885943844", "style": "primary"}])
    
    mc_link = bot_settings.get("main_channel_link", "")
    mc_display = mc_link if mc_link else "Not Set"
    if len(mc_display) > 25: mc_display = mc_display[:25] + "..."
    kb["inline_keyboard"].append([{"text": f"Main Channel: {mc_display}", "callback_data": "edit_main_channel", "icon_custom_emoji_id": "5429353834881261942", "style": "primary"}])
    
    if otp_forward_groups:
        grp = otp_forward_groups[0]
        kb["inline_keyboard"].append([{"text": f"Delete Group: {grp}", "callback_data": "del_otp_group_0", "icon_custom_emoji_id": "5422557736330106570", "style": "danger"}])
        
    kb["inline_keyboard"].append([{"text": "Set Forward Group", "callback_data": "add_otp_group", "icon_custom_emoji_id": "5429501315468270290", "style": "success"}])
    kb["inline_keyboard"].append([{"text": "BACK", "callback_data": "back_to_admin", "icon_custom_emoji_id": "5267490665117275176", "style": "danger"}])
    return kb

def get_force_join_keyboard():
    kb = {"inline_keyboard": []}
    status_text = "STATUS: ON" if force_join_status else "STATUS: OFF"
    status_icon = "5352694861990501856" if force_join_status else "5420130255174145507"
    
    kb["inline_keyboard"].append([{"text": status_text, "callback_data": "toggle_fj", "icon_custom_emoji_id": status_icon, "style": "primary" if force_join_status else "danger"}])
    
    for idx, ch in enumerate(force_join_channels):
        name = ch.get("username", ch.get("title", f"Channel {idx}"))
        kb["inline_keyboard"].append([{"text": f"Delete: {name}", "callback_data": f"del_fj_{idx}", "icon_custom_emoji_id": "5438178416421544431", "style": "danger"}])
        
    kb["inline_keyboard"].append([{"text": "Add Channel", "callback_data": "add_fj", "icon_custom_emoji_id": "5429501315468270290", "style": "success"}])
    kb["inline_keyboard"].append([{"text": "Back", "callback_data": "back_to_admin", "icon_custom_emoji_id": "5438541186539232243", "style": "primary"}])
    return kb

def get_force_join_alert_keyboard():
    kb = {"inline_keyboard": []}
    for ch in force_join_channels:
        name = ch.get("title", ch.get("username", "Our Channel"))
        url = ch.get("invite_link", "")
        if not url and ch.get("username"): url = f"https://t.me/{ch['username'].replace('@', '')}"
        # ðŸŒŸ Join à¦¬à¦¾à¦Ÿà¦¨à§‡ à¦ªà§à¦°à¦¿à¦®à¦¿à§Ÿà¦¾à¦® à¦²à¦¿à¦‚à¦• à¦‡à¦®à§‹à¦œà¦¿
        kb["inline_keyboard"].append([{"text": f"JOIN {name}", "url": url, "icon_custom_emoji_id": "5420517437885943844", "style": "danger"}])
    
    # ðŸŒŸ Verify à¦¬à¦¾à¦Ÿà¦¨à§‡ à¦ªà§à¦°à¦¿à¦®à¦¿à§Ÿà¦¾à¦® à¦Ÿà¦¿à¦•à¦®à¦¾à¦°à§à¦• à¦‡à¦®à§‹à¦œà¦¿
    kb["inline_keyboard"].append([{"text": "VERIFY", "callback_data": "check_fj_joined", "icon_custom_emoji_id": "5352694861990501856", "style": "success"}])
    return kb

def get_voltx_keys_keyboard():
    kb = {"inline_keyboard": []}
    status_text = "VOLTX AUTO: ON" if voltx_auto_mode else "VOLTX AUTO: OFF"
    status_icon = "5352694861990501856" if voltx_auto_mode else "5420130255174145507"
    
    kb["inline_keyboard"].append([{"text": status_text, "callback_data": "toggle_vk", "icon_custom_emoji_id": status_icon, "style": "primary" if voltx_auto_mode else "danger"}])
    
    for idx, key in enumerate(voltx_keys):
        masked_key = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else key
        kb["inline_keyboard"].append([{"text": f"Delete: {masked_key}", "callback_data": f"del_vk_{idx}", "icon_custom_emoji_id": "5438178416421544431", "style": "danger"}])
        
    kb["inline_keyboard"].append([{"text": "Add Voltx Key", "callback_data": "add_vk", "icon_custom_emoji_id": "5429501315468270290", "style": "success"}])
    kb["inline_keyboard"].append([{"text": "Back", "callback_data": "back_to_admin", "icon_custom_emoji_id": "5438541186539232243", "style": "primary"}])
    return kb

def get_main_keyboard(user_id):
    keyboard_layout = [
        [
            {"text": "LIVE NUMBER", "icon_custom_emoji_id": "5456259593082522998", "style": "danger"},
            {"text": "LIVE TRAFFIC", "icon_custom_emoji_id": "5429571662737611814", "style": "primary"}
        ],
        [
            {"text": "INVITE FRIEND", "icon_custom_emoji_id": "5384394344859974865", "style": "success"},
            {"text": "WALLET", "icon_custom_emoji_id": "5429105001655999635", "style": "danger"}
        ],
        [
            {"text": "LEADERBOARD", "icon_custom_emoji_id": "5240021484516185513", "style": "primary"}
        ]
    ]
    if user_id == ADMIN_ID:
        keyboard_layout.append([{"text": "OWNER PANEL", "icon_custom_emoji_id": "5429427051188756948", "style": "success"}])
    return {"keyboard": keyboard_layout, "resize_keyboard": True}

def get_admin_inline_keyboard():
    global current_db_mode
    db_status = "SQLITE ACTIVE" if current_db_mode == "sqlite" else "FIREBASE ACTIVE"
    
    return {
        "inline_keyboard": [
            [
                {
                    "text": "VOLTX SETTINGS", 
                    "callback_data": "manage_voltx", 
                    "icon_custom_emoji_id": "5240122519326860770", 
                    "style": "danger"
                }
            ],
            [
                {
                    "text": "BROADCAST", 
                    "callback_data": "broadcast_menu", 
                    "icon_custom_emoji_id": "5296633779157243809", 
                    "style": "primary"
                },
                {
                    "text": "FORCE JOIN", 
                    "callback_data": "manage_fj", 
                    "icon_custom_emoji_id": "5429353834881261942", 
                    "style": "success"
                }
            ],
            [
                {
                    "text": "OTP GROUP", 
                    "callback_data": "manage_otp_group", 
                    "icon_custom_emoji_id": "5429208347159077664", 
                    "style": "danger"
                },
                {
                    "text": "USER CONTROL", 
                    "callback_data": "user_control", 
                    "icon_custom_emoji_id": "5429274992166609833", 
                    "style": "primary"
                }
            ],
            [
                {
                    "text": "DXA CONTROL", 
                    "callback_data": "dxa_control", 
                    "icon_custom_emoji_id": "5240451569656308978", 
                    "style": "danger"
                }
            ],
            [
                {
                    "text": "UPLOAD FIREBASE", 
                    "callback_data": "upload_firebase", 
                    "icon_custom_emoji_id": "5429362935916962442", 
                    "style": "primary"
                }
            ],
            [
                {
                    "text": db_status, 
                    "callback_data": "db_status", 
                    "icon_custom_emoji_id": "5429591316507963112", 
                    "style": "success"
                }
            ],
            [
                {
                    "text": "CLOSE", 
                    "callback_data": "close_panel", 
                    "icon_custom_emoji_id": "5438541186539232243", 
                    "style": "danger"
                }
            ]
        ]
    }

def dxa_control_keyboard():
    grp = bot_settings.get("w_group", "")
    grp_status = grp if grp else "NOT SET"
    return {"inline_keyboard": [
        [{"text": f"MIN WITHDRAW: {bot_settings['min_withdraw']}", "icon_custom_emoji_id": "5352877703043258544", "callback_data": "dxa_min_w", "style": "success"},
         {"text": "OTP CONTROL", "icon_custom_emoji_id": "5190576863226933563", "callback_data": "dxa_otp_control", "style": "primary"}],
        [{"text": f"REFER REWARD: {bot_settings.get('refer_reward', 0.2)}", "icon_custom_emoji_id": "5420396762189831222", "callback_data": "dxa_ref_r", "style": "success"},
         {"text": f"COOLDOWN: {bot_settings['cooldown']}s", "icon_custom_emoji_id": "5337172996211648018", "callback_data": "dxa_cool", "style": "primary"}],
        [{"text": f"NUM/REQ: {bot_settings['num_req']}", "icon_custom_emoji_id": "5337132498965010628", "callback_data": "dxa_num_req", "style": "success"},
         {"text": "W. METHODS", "icon_custom_emoji_id": "5190899075968441286", "callback_data": "manage_w_methods", "style": "primary"}],
        [{"text": f"W. GROUP: {grp_status}", "icon_custom_emoji_id": "5420517437885943844", "callback_data": "dxa_w_group", "style": "success"}],
        [{"text": "BACK", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_admin", "style": "danger"}]
    ]}

def dxa_otp_control_keyboard():
    kb = {"inline_keyboard": [
        [{"text": f"Default Rate: {bot_settings['otp_default_rate']}", "icon_custom_emoji_id": "5352877703043258544", "callback_data": "dxa_def_rate", "style": "primary"}],
        [{"text": "Set Service Rate", "icon_custom_emoji_id": "5395444784611480792", "callback_data": "dxa_srv_rate", "style": "success"}]
    ]}
    
    # à¦…à§à¦¯à¦¾à¦¡ à¦•à¦°à¦¾ à¦¸à§à¦ªà§‡à¦¸à¦¿à¦«à¦¿à¦• à¦¸à¦¾à¦°à§à¦­à¦¿à¦¸ à¦°à§‡à¦Ÿà¦—à§à¦²à§‹ à¦¡à¦¾à§Ÿà¦¨à¦¾à¦®à¦¿à¦• à¦‡à¦¨à¦²à¦¾à¦‡à¦¨ à¦¬à¦¾à¦Ÿà¦¨ à¦¹à¦¿à¦¸à§‡à¦¬à§‡ à¦¦à§‡à¦–à¦¾à¦¨à§‹à¦° à¦œà¦¨à§à¦¯
    for srv_name, rate in bot_settings.get("otp_service_rates", {}).items():
        app_info = PREMIUM_APPS.get(srv_name, PREMIUM_APPS["Other"])
        kb["inline_keyboard"].append([{"text": f"Delete: {srv_name} ({rate})", "icon_custom_emoji_id": app_info["id"], "callback_data": f"del_srv_rate_{srv_name}", "style": "danger"}])
        
    kb["inline_keyboard"].append([{"text": "BACK", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "dxa_control", "style": "danger"}])
    return kb
    
def dxa_manage_w_methods_keyboard():
    kb = {"inline_keyboard": []}
    for idx, method in enumerate(bot_settings.get("w_methods", [])):
        kb["inline_keyboard"].append([{"text": f"Delete: {method}", "callback_data": f"del_w_method_{idx}", "style": "danger"}])
    kb["inline_keyboard"].append([{"text": "Add Method", "callback_data": "add_w_method", "style": "success"}])
    kb["inline_keyboard"].append([{"text": "BACK", "callback_data": "dxa_control", "style": "primary"}])
    return kb

def get_user_control_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "USER PROFILE", "icon_custom_emoji_id": "5352861489541714456", "callback_data": "uc_profile", "style": "primary"}],
            [{"text": "BACK", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "back_to_admin", "style": "danger"}]
        ]
    }

def get_user_profile_keyboard(target_uid):
    return {
        "inline_keyboard": [
            [{"text": "BALANCE", "icon_custom_emoji_id": "5429612421977253466", "callback_data": f"uc_balance_{target_uid}", "style": "success"}],
            [{"text": "BACK", "icon_custom_emoji_id": "5267490665117275176", "callback_data": "user_control", "style": "danger"}]
        ]
    }

def get_upload_firebase_keyboard():
    return {"inline_keyboard": [[{"text": "CANCEL", "callback_data": "back_to_admin", "icon_custom_emoji_id": "5420130255174145507", "style": "danger"}]]}

def get_back_only_keyboard():
    return {"inline_keyboard": [[{"text": "BACK", "callback_data": "user_cancel", "icon_custom_emoji_id": "5438541186539232243", "style": "danger"}]]}

def get_leaderboard_keyboard():
    return {"inline_keyboard": [[{"text": "REFRESH", "callback_data": "refresh_leaderboard", "icon_custom_emoji_id": "5229111790842952353", "style": "success"}]]}

def get_owner_panel_text():
    today = time.strftime("%Y-%m-%d")
    if daily_stats.get("date") != today:
        daily_stats["date"] = today
        daily_stats["numbers"] = 0
        daily_stats["otps"] = 0
        
    return (
        "<b>ðŸ“Š OWNER ZONE ðŸ“Š</b>\n"
        "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        "<b>ðŸ“Š DATABASE OVERVIEW</b>\n"
        "â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”\n"
        f"<blockquote><b>ðŸ‘¤ TOTAL USER         Â» {get_total_users()}</b></blockquote>\n"
        f"<blockquote><b>ðŸ“± TODAY NUMBER  Â» {daily_stats['numbers']}</b></blockquote>\n"
        f"<blockquote><b>ðŸ’¬ TODAY OTP           Â» {daily_stats['otps']}</b></blockquote>\n"
        "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”"
    )

def get_leaderboard_text():
    global cached_leaderboard_text
    if cached_leaderboard_text:
        return cached_leaderboard_text
    return "â³ <b>Loading leaderboard, please wait...</b>"

def get_live_traffic_content():
    global recent_traffic
    hits_to_show = recent_traffic
    markup = {"inline_keyboard": [[{"text": "REFRESH", "callback_data": "refresh_traffic", "icon_custom_emoji_id": "5229111790842952353", "style": "primary"}]]}
    
    if not hits_to_show:
        return "â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—\nâ•‘  <tg-emoji emoji-id=\"5352877703043258544\">ðŸ“ˆ</tg-emoji> <b>15M LIVE TRAFFIC</b>\nâ•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•\n<i>No traffic data available.</i>\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”", markup

    service_counts = {}
    for h in hits_to_show:
        raw_sid = h.get("sid") or "Unknown"
        raw_msg = h.get("message") or ""
        detected_sid = detect_service(raw_msg, raw_sid)
        app_info = PREMIUM_APPS.get(detected_sid, PREMIUM_APPS["Other"])
        
        if detected_sid not in service_counts: service_counts[detected_sid] = {"count": 0, "emoji_id": app_info["id"], "normal_emoji": app_info["emoji"]}
        service_counts[detected_sid]["count"] += 1

    sorted_services = sorted(service_counts.items(), key=lambda item: item[1]["count"], reverse=True)[:6]

    msg = "â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—\nâ•‘  <tg-emoji emoji-id=\"5352877703043258544\">ðŸ“ˆ</tg-emoji> <b>15M LIVE TRAFFIC</b>\nâ•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•\n"
    fire_emoji_id = "5337267511261960341"
    
    for i, (sid, data) in enumerate(sorted_services):
        msg += f"<tg-emoji emoji-id=\"{data['emoji_id']}\">{data['normal_emoji']}</tg-emoji> {html.escape(str(sid))} âžœ <tg-emoji emoji-id=\"{fire_emoji_id}\">ðŸ”¥</tg-emoji> {data['count']} OTP\n"
        if i < len(sorted_services) - 1: msg += "â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”\n"
    msg += "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”"
    return msg, markup

def get_services_content():
    global cached_services_kb
    if cached_services_kb:
        return "ðŸ“± <b>Select Top Service:</b>", cached_services_kb
    return "â³ <b>Loading services, please try again in a few seconds...</b>", None

def get_countries_content(sid_short):
    global cached_countries_kb
    if sid_short in cached_countries_kb:
        return f"ðŸŒ <b>Select Country:</b>", cached_countries_kb[sid_short], None
    return None, None, "âŒ <b>No active countries for this service. (Out of Stock)</b>"

def get_number_allocation_content(sid_short, c_code, user_id=None):
    global voltx_auto_mode, voltx_dynamic_data, user_active_sessions, bot_settings, otp_button_link
    target_ranges = []
    full_sid = sid_short
    
    if voltx_auto_mode:
        for sid, data in voltx_dynamic_data.items():
            if sid.lower().startswith(sid_short.lower()):
                full_sid = sid
                for r, r_data in data["ranges"].items():
                    if c_code.startswith(r) or r.startswith(c_code): 
                        target_ranges.append((r, r_data["hits"]))
                break
        target_ranges.sort(key=lambda x: x[1], reverse=True)
        best_ranges = [x[0] for x in target_ranges[:3]]
    else:
        services_data = fetch_live_access()
        for s in services_data:
            sid_val = s.get('sid') or ""
            if sid_val.lower().startswith(sid_short.lower()):
                full_sid = sid_val
                for r in s.get('ranges', []):
                    clean_r = str(r).replace("X", "")
                    if c_code.startswith(clean_r) or clean_r.startswith(c_code):
                        if clean_r not in target_ranges:
                            target_ranges.append(clean_r)
                break
        best_ranges = target_ranges[:3]
            
    # ðŸŒŸ à¦à¦ªà¦¿à¦†à¦‡ à¦²à¦¿à¦¸à§à¦Ÿà§‡ à¦¨à¦¾ à¦¥à¦¾à¦•à¦²à§‡à¦“ à¦²à¦¿à¦‚à¦•à§‡à¦° à¦°à§‡à¦žà§à¦œ à¦¦à¦¿à§Ÿà§‡ à¦¸à¦°à¦¾à¦¸à¦°à¦¿ à¦°à¦¿à¦•à§‹à§Ÿà§‡à¦¸à§à¦Ÿ à¦•à¦°à¦¬à§‡
    if not best_ranges: 
        best_ranges = [c_code]
        
    req_count = bot_settings.get("num_req", 1)
    fetched_numbers = []
    
    for _ in range(req_count):
        selected_rid = random.choice(best_ranges)
        num_data = fetch_live_number(selected_rid)
        if num_data:
            full_number = html.escape(str(num_data.get("full_number", "")))
            country = html.escape(str(num_data.get("country", "Unknown")))
            operator = html.escape(str(num_data.get("operator", "Unknown")))
            fetched_numbers.append((full_number, country, operator))
            
            if user_id and full_number:
                user_active_sessions[str(full_number)] = user_id
    
    if fetched_numbers:
        update_daily_stat("numbers", len(fetched_numbers))
        save_local_data()
        
        service_html, srv_eid = get_service_info_html(full_sid)
        _, country_with_flag = get_country_info(c_code)
        
        msg = (
            f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            f"<tg-emoji emoji-id=\"5337172996211648018\">âŒ›</tg-emoji> <b>ACTIVE NUMBER 15M</b>\n"
            f"â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”\n"
            f"{service_html} âžœ {country_with_flag}\n"
            f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”"
        )
        
        kb = {"inline_keyboard": []}
        
        for f_num, ctry, op in fetched_numbers:
            clean_f_num = str(f_num).lstrip('+') 
            kb["inline_keyboard"].append([
                {"text": f"+{clean_f_num}", "icon_custom_emoji_id": "5226929552319594190", "copy_text": {"text": f"+{clean_f_num}"}, "style": "primary"}
            ])
            
        kb["inline_keyboard"].append([
            {"text": "Change Number", "icon_custom_emoji_id": "5429386648431405093", "callback_data": f"cc_{sid_short}_{c_code}", "style": "danger"},
            {"text": "OTP Group", "icon_custom_emoji_id": "5314366268898300483", "url": otp_button_link, "style": "success"}
        ])
        kb["inline_keyboard"].append([
            {"text": "BACK", "icon_custom_emoji_id": "5438541186539232243", "callback_data": f"srv_{sid_short}", "style": "danger"}
        ])
        
        return msg, kb
    else:
        return f"âŒ <b>Out of stock in these ranges. Please try again.</b>", {"inline_keyboard": [[{"text": "BACK", "callback_data": f"srv_{sid_short}", "icon_custom_emoji_id": "5438541186539232243", "style": "danger"}]]}

# ==========================================
# Background Broadcaster Tool 
# ==========================================
def broadcast_worker(from_chat_id, message_id, target_msg_id):
    users = get_all_user_ids() 
    success_count = 0
    for uid in users:
        try:
            res = copy_message(uid, from_chat_id, message_id)
            if res and res.get("ok"): success_count += 1
            time.sleep(0.05) 
        except: pass
        
    send_message(from_chat_id, f"âœ… <b>Broadcast Completed!</b>\nSuccessfully sent to {success_count} users out of {len(users)}.")
    
    if target_msg_id:
        edit_message(from_chat_id, target_msg_id, get_owner_panel_text(), reply_markup=get_admin_inline_keyboard())

# ==========================================
# Message Handlers
# ==========================================
def handle_message(message):
    global waiting_for_firebase, current_db_mode, db_firebase, user_states, voltx_keys, force_join_channels, otp_forward_groups, otp_button_link, bot_settings
    
    # ðŸŒŸ à¦¬à¦Ÿ à¦¶à§à¦§à§à¦®à¦¾à¦¤à§à¦° à¦‡à¦¨à¦¬à¦•à§à¦¸à§‡à¦° à¦®à§‡à¦¸à§‡à¦œà§‡ à¦°à¦¿à¦ªà§à¦²à¦¾à¦‡ à¦¦à¦¿à¦¬à§‡ (à¦—à§à¦°à§à¦ª à¦‡à¦—à¦¨à§‹à¦° à¦•à¦°à¦¬à§‡)
    if message.get("chat", {}).get("type") != "private":
        return
        
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = message.get("text", "")
    message_id = message["message_id"]
    first_name = message["from"].get("first_name", "User")

    if "BACK" in text.upper() and user_id == ADMIN_ID:
        send_message(chat_id, "âŒ <b>Action Cancelled!</b>", reply_markup=get_main_keyboard(user_id)) 
        if user_id in user_states: del user_states[user_id]
        send_message(chat_id, get_owner_panel_text(), reply_markup=get_admin_inline_keyboard())
        return

    # Native Chat Selection Listener
    if "chat_shared" in message:
        shared_chat_id = message["chat_shared"]["chat_id"]
        if user_id == ADMIN_ID and user_id in user_states:
            state_data = user_states[user_id]
            state = state_data.get("state")
            target_msg_id = state_data.get("msg_id")
            
            send_message(chat_id, "âœ… <b>Successfully Selected!</b>", reply_markup=get_main_keyboard(user_id)) 
            
            if state == "waiting_otp_group":
                otp_forward_groups.clear() 
                otp_forward_groups.append(str(shared_chat_id))
                
                inv_res = requests.post(BASE_URL + "exportChatInviteLink", json={"chat_id": shared_chat_id}).json()
                if inv_res.get("ok"):
                    otp_button_link = inv_res["result"]
                
                save_local_data()
                if target_msg_id: edit_message(chat_id, target_msg_id, "ðŸ›¡ <b>OTP GROUP MANAGEMENT</b>\nManage settings below:", reply_markup=get_otp_group_keyboard())
                del user_states[user_id]
                return
                
            elif state == "waiting_dxa_w_group":
                bot_settings["w_group"] = str(shared_chat_id)
                save_local_data()
                if target_msg_id: edit_message(chat_id, target_msg_id, "âš™ï¸ <b>DXA CONTROL PANEL</b>\nManage core bot configurations:", reply_markup=dxa_control_keyboard())
                del user_states[user_id]
                return
                
            elif state == "waiting_fj_channel":
                chat_details = get_chat_details(str(shared_chat_id))
                if chat_details:
                    force_join_channels.append(chat_details)
                    save_local_data()
                    if target_msg_id: edit_message(chat_id, target_msg_id, "ðŸ”— <b>FORCE JOIN SYSTEM</b>\nManage channels below:", reply_markup=get_force_join_keyboard())
                else:
                    if target_msg_id: edit_message(chat_id, target_msg_id, "âŒ <b>Failed to verify channel! Make sure bot is admin.</b>", reply_markup=get_back_only_keyboard())
                del user_states[user_id]
                return

    if not is_user_joined(user_id):
        fj_msg = (
            "<b>â•â•â•â•ã€Š <tg-emoji emoji-id=\"5337267511261960341\">ðŸ”¥</tg-emoji> ACCESS REQUIRED ã€‹â•â•â•â•</b>\n\n"
            "<b><tg-emoji emoji-id=\"5420517437885943844\">ðŸ”—</tg-emoji> JOIN ALL CHANNELS BELOW TO USE THIS BOT.</b>\n\n"
            "<b><tg-emoji emoji-id=\"5352694861990501856\">âœ…</tg-emoji> JOIN ALL CHANNELS, THEN CLICK VERIFY.</b>"
        )
        send_message(chat_id, fj_msg, reply_markup=get_force_join_alert_keyboard())
        return

    # Handle Admin & User Input States
    if user_id in user_states:
        state_data = user_states[user_id]
        if isinstance(state_data, dict):
            state = state_data.get("state")
            target_msg_id = state_data.get("msg_id")
        else:
            state = state_data
            target_msg_id = None
            
        if state == "waiting_vk_key":
            voltx_keys.append(text.strip())
            save_local_data()
            if target_msg_id: edit_message(chat_id, target_msg_id, "ðŸ”‘ <b>VOLTX KEY SYSTEM</b>\nManage API Keys below:", reply_markup=get_voltx_keys_keyboard())
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return
            
        elif state == "waiting_otp_link":
            if text.startswith("http"):
                otp_button_link = text.strip()
                save_local_data()
                if target_msg_id: edit_message(chat_id, target_msg_id, "ðŸ›¡ <b>OTP GROUP MANAGEMENT</b>\nManage settings below:", reply_markup=get_otp_group_keyboard())
            else:
                if target_msg_id: edit_message(chat_id, target_msg_id, "âŒ <b>Invalid URL format. Must start with http/https.</b>", reply_markup=get_back_only_keyboard())
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return

        elif state == "waiting_main_channel_link":
            if text.startswith("http"):
                bot_settings["main_channel_link"] = text.strip()
                save_local_data()
                if target_msg_id: edit_message(chat_id, target_msg_id, "ðŸ›¡ <b>OTP GROUP MANAGEMENT</b>\nManage settings below:", reply_markup=get_otp_group_keyboard())
            else:
                if target_msg_id: edit_message(chat_id, target_msg_id, "âŒ <b>Invalid URL format. Must start with http/https.</b>", reply_markup=get_back_only_keyboard())
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return

        elif state == "waiting_broadcast":
            if target_msg_id: edit_message(chat_id, target_msg_id, "â³ <b>Broadcasting message to all users...</b>")
            threading.Thread(target=broadcast_worker, args=(chat_id, message_id, target_msg_id), daemon=True).start()
            del user_states[user_id]
            return
            
        elif state == "waiting_firebase":
            try:
                # ðŸŒŸ à¦«à¦¾à¦‡à¦² à¦†à¦ªà¦²à§‹à¦¡ à¦¸à¦¾à¦ªà§‹à¦°à§à¦Ÿ à¦…à§à¦¯à¦¾à¦¡ à¦•à¦°à¦¾ à¦¹à¦²à§‹
                if "document" in message:
                    file_id = message["document"]["file_id"]
                    file_info = requests.get(BASE_URL + f"getFile?file_id={file_id}").json()
                    file_path = file_info["result"]["file_path"]
                    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                    text = requests.get(file_url).text
                
                # ðŸŒŸ à¦¸à§à¦®à¦¾à¦°à§à¦Ÿ à¦•à§‹à¦Ÿ (Smart Quotes) à¦¬à¦¾ à¦­à§à¦² à¦Ÿà§‡à¦•à§à¦¸à¦Ÿ à¦«à¦¿à¦•à§à¦¸
                text = text.replace("â€œ", '"').replace("â€", '"').replace("â€˜", "'").replace("â€™", "'")

                firebase_cred = json.loads(text)
                with open("temp_firebase.json", "w") as f: json.dump(firebase_cred, f)
                try:
                    if not firebase_admin._apps: firebase_admin.initialize_app(credentials.Certificate("temp_firebase.json"))
                    db_firebase = firestore.client()
                    current_db_mode = "firebase"
                    waiting_for_firebase = False
                    
                    # ðŸŒŸ One-Time Sync: Firebase à¦¥à§‡à¦•à§‡ à¦¸à¦¬ à¦‡à¦‰à¦œà¦¾à¦° ID à¦²à§‹à¦•à¦¾à¦²à§‡ à¦¸à§‡à¦­ à¦•à¦°à¦¾ (à¦²à¦¿à¦®à¦¿à¦Ÿ à¦¬à¦¾à¦à¦šà¦¾à¦¤à§‡)
                    try:
                        local_users = set()
                        if os.path.exists(USERS_LIST_FILE):
                            with open(USERS_LIST_FILE, "r") as f:
                                local_users = set(json.load(f))
                        
                        # à¦¶à§à¦§à§à¦®à¦¾à¦¤à§à¦° ID à¦—à§à¦²à§‹ à¦†à¦¨à¦¾ à¦¹à¦šà§à¦›à§‡, à¦ªà§à¦°à§‹ à¦¡à¦¾à¦Ÿà¦¾ à¦¨à§Ÿ (à¦à¦¤à§‡ à¦¬à§à¦¯à¦¾à¦¨à§à¦¡à¦‰à¦‡à¦¥ à¦“ à¦²à¦¿à¦®à¦¿à¦Ÿ à¦¬à¦¾à¦à¦šà¦¬à§‡)
                        docs = db_firebase.collection('users').select([]).stream()
                        fb_users = set(int(doc.id) for doc in docs)
                        
                        combined_users = local_users.union(fb_users)
                        if len(combined_users) > len(local_users):
                            with open(USERS_LIST_FILE, "w") as f:
                                json.dump(list(combined_users), f)
                            print(f"âœ… Synced {len(fb_users)} users from Firebase to Local List!")
                    except Exception as e:
                        print(f"User Sync Error: {e}")

                    # ðŸŒŸ Firebase à¦ à¦¸à§‡à¦Ÿà¦¿à¦‚à¦¸ à¦šà§‡à¦• à¦à¦¬à¦‚ à¦¸à§‡à¦­/à¦¸à¦¿à¦™à§à¦• à¦•à¦°à¦¾à¦° à¦²à¦œà¦¿à¦•
                    try:
                        config_ref = db_firebase.collection('settings').document('bot_config')
                        doc = config_ref.get()
                        if not doc.exists:
                            config_data = {
                                "bot_settings": bot_settings,
                                "force_join_status": force_join_status,
                                "force_join_channels": force_join_channels,
                                "otp_forward_groups": otp_forward_groups,
                                "otp_button_link": otp_button_link,
                                "voltx_keys": voltx_keys,
                                "voltx_auto_mode": voltx_auto_mode
                            }
                            config_ref.set(config_data)
                        else:
                            data = doc.to_dict()
                            if "bot_settings" in data: bot_settings.update(data["bot_settings"])
                            if "force_join_status" in data: force_join_status = data["force_join_status"]
                            if "force_join_channels" in data: force_join_channels = data["force_join_channels"]
                            if "otp_forward_groups" in data: otp_forward_groups = data["otp_forward_groups"]
                            if "otp_button_link" in data: otp_button_link = data["otp_button_link"]
                            if "voltx_keys" in data: voltx_keys = data["voltx_keys"]
                            if "voltx_auto_mode" in data: voltx_auto_mode = data["voltx_auto_mode"]
                            save_local_data()
                    except Exception as e:
                        pass
                    
                    if target_msg_id: edit_message(chat_id, target_msg_id, "â³ <b>Syncing SQLite data to Firebase... Please wait.</b>")
                    migrate_sqlite_to_firebase()
                    
                    if target_msg_id: edit_message(chat_id, target_msg_id, get_owner_panel_text(), reply_markup=get_admin_inline_keyboard())
                    send_message(chat_id, "âœ… <b>Firebase successfully connected & Synced!</b>")
                except Exception as e:
                    if target_msg_id: edit_message(chat_id, target_msg_id, f"âŒ <b>Failed to connect to Firebase:</b>\n<code>{html.escape(str(e))}</code>", reply_markup=get_back_only_keyboard())
            except Exception:
                if target_msg_id: edit_message(chat_id, target_msg_id, "âš ï¸ <b>Invalid JSON format. Please upload the .json file directly.</b>", reply_markup=get_back_only_keyboard())
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return

        elif isinstance(state, str) and state.startswith("waiting_withdraw_amount_"):
            method = state[24:]
            user_data = get_user(user_id)
            bal = user_data.get("balance", 0)
            min_w = bot_settings.get("min_withdraw", 10.0)
            
            try:
                amount = float(text.strip())
                if amount < min_w:
                    if target_msg_id: edit_message(chat_id, target_msg_id, f"âŒ <b>Minimum withdraw is {min_w} BDT.</b>\nTry again:", reply_markup=get_back_only_keyboard())
                elif amount > bal:
                    if target_msg_id: edit_message(chat_id, target_msg_id, f"âŒ <b>Insufficient balance! You only have {bal:.2f} BDT.</b>\nTry again:", reply_markup=get_back_only_keyboard())
                else:
                    user_states[user_id] = {"state": f"waiting_withdraw_number_{method}_{amount}", "msg_id": target_msg_id}
                    if target_msg_id: edit_message(chat_id, target_msg_id, f"âœ… <b>Amount Set: {amount:.2f} BDT</b>\n\nðŸ’³ <b>Method:</b> {method}\nðŸ’¬ <b>Now send your {method} account number:</b>", reply_markup=get_back_only_keyboard())
            except ValueError:
                if target_msg_id: edit_message(chat_id, target_msg_id, "âŒ <b>Invalid amount. Send numbers only.</b>\nTry again:", reply_markup=get_back_only_keyboard())
            delete_message(chat_id, message_id)
            return

        elif isinstance(state, str) and state.startswith("waiting_withdraw_number_"):
            parts = state.split("_")
            method = parts[3]
            amount = float(parts[4])
            
            user_data = get_user(user_id)
            bal = user_data.get("balance", 0)
            
            if bal < amount:
                if target_msg_id: edit_message(chat_id, target_msg_id, "âŒ <b>Insufficient balance!</b>", reply_markup=get_main_keyboard(user_id))
            else:
                account_number = text.strip()
                update_user_stats(user_id, -amount, 0)
                
                w_group = bot_settings.get("w_group", "")
                if w_group:
                    w_msg = (
                        f"<tg-emoji emoji-id=\"5420396762189831222\">ðŸ†•</tg-emoji> <b>NEW WITHDRAW REQUEST</b>\n"
                        f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
                        f"<tg-emoji emoji-id=\"5352861489541714456\">ðŸ‘¤</tg-emoji> <b>User:</b> <a href='tg://user?id={user_id}'>{html.escape(first_name)}</a>\n"
                        f"â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”\n"
                        f"<tg-emoji emoji-id=\"5226929552319594190\">ðŸ†”</tg-emoji> <b>ID:</b> <code>{user_id}</code>\n"
                        f"â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”\n"
                        f"<tg-emoji emoji-id=\"5429612421977253466\">ðŸ’µ</tg-emoji> <b>Amount:</b> <b>{amount:.2f} BDT</b>\n"
                        f"â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”\n"
                        f"<tg-emoji emoji-id=\"5190899075968441286\">ðŸ’³</tg-emoji> <b>Method:</b> {method}\n"
                        f"â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”\n"
                        f"<tg-emoji emoji-id=\"5337132498965010628\">ðŸ“ž</tg-emoji> <b>Number:</b> <code>{account_number}</code>\n"
                        f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”"
                    )
                    
                    w_markup = {
                        "inline_keyboard": [
                            [
                                {"text": "APPROVE", "icon_custom_emoji_id": "5352694861990501856", "callback_data": f"admin_w_approve_{user_id}_{amount}_{account_number}", "style": "success"},
                                {"text": "REJECT", "icon_custom_emoji_id": "5420130255174145507", "callback_data": f"admin_w_reject_{user_id}_{amount}_{account_number}", "style": "danger"}
                            ]
                        ]
                    }
                    send_message(w_group, w_msg, reply_markup=w_markup)
                
                success_msg = (
                    f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
                    f"<tg-emoji emoji-id=\"5429612421977253466\">ðŸ’µ</tg-emoji> <b>Amount:</b> {amount:.2f} BDT\n"
                    f"â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”\n"
                    f"<tg-emoji emoji-id=\"5190899075968441286\">ðŸ’³</tg-emoji> <b>Method:</b> {method}\n"
                    f"â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”\n"
                    f"<tg-emoji emoji-id=\"5337132498965010628\">ðŸ“ž</tg-emoji> <b>Number:</b> <code>{account_number}</code>\n"
                    f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”"
                )
                if target_msg_id:
                    delete_message(chat_id, target_msg_id)
                send_message(chat_id, success_msg, reply_markup=get_main_keyboard(user_id))
                    
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return

        elif state == "waiting_dxa_ref_r":
            try:
                bot_settings["refer_reward"] = float(text.strip())
                save_local_data()
                if target_msg_id: edit_message(chat_id, target_msg_id, "âš™ï¸ <b>DXA CONTROL PANEL</b>\nManage core bot configurations:", reply_markup=dxa_control_keyboard())
            except ValueError: pass
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return

        elif state == "waiting_dxa_min_w":
            try:
                bot_settings["min_withdraw"] = float(text.strip())
                save_local_data()
                if target_msg_id: edit_message(chat_id, target_msg_id, "âš™ï¸ <b>DXA CONTROL PANEL</b>\nManage core bot configurations:", reply_markup=dxa_control_keyboard())
            except ValueError: pass
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return
            
        elif state == "waiting_dxa_cool":
            try:
                bot_settings["cooldown"] = int(text.strip())
                save_local_data()
                if target_msg_id: edit_message(chat_id, target_msg_id, "âš™ï¸ <b>DXA CONTROL PANEL</b>\nManage core bot configurations:", reply_markup=dxa_control_keyboard())
            except ValueError: pass
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return
            
        elif state == "waiting_dxa_num_req":
            try:
                bot_settings["num_req"] = int(text.strip())
                save_local_data()
                if target_msg_id: edit_message(chat_id, target_msg_id, "âš™ï¸ <b>DXA CONTROL PANEL</b>\nManage core bot configurations:", reply_markup=dxa_control_keyboard())
            except ValueError: pass
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return
            
        elif state == "waiting_w_method":
            bot_settings["w_methods"].append(text.strip())
            save_local_data()
            if target_msg_id: edit_message(chat_id, target_msg_id, "ðŸ’³ <b>WITHDRAW METHODS</b>\nManage methods below:", reply_markup=dxa_manage_w_methods_keyboard())
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return
            
        elif state == "waiting_dxa_def_rate":
            try:
                bot_settings["otp_default_rate"] = float(text.strip())
                save_local_data()
                if target_msg_id: edit_message(chat_id, target_msg_id, "ðŸ’° <b>OTP REWARD CONTROL</b>\nManage rates below:", reply_markup=dxa_otp_control_keyboard())
            except ValueError: pass
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return
            
        elif state == "waiting_dxa_srv_rate":
            try:
                parts = text.split("-")
                srv_name = parts[0].strip()
                srv_rate = float(parts[1].strip())
                bot_settings["otp_service_rates"][srv_name] = srv_rate
                save_local_data()
                if target_msg_id: edit_message(chat_id, target_msg_id, "ðŸ’° <b>OTP REWARD CONTROL</b>\nManage rates below:", reply_markup=dxa_otp_control_keyboard())
            except Exception:
                send_message(chat_id, "âŒ Invalid format. Use: ServiceName - Rate (e.g. Telegram - 5.0)")
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return
            
        elif state == "waiting_uc_id":
            try:
                target_uid = int(text.strip())
                target_data = get_user(target_uid)
                
                if target_data:
                    safe_name = html.escape(str(target_data.get('first_name', 'User')))
                    total_otps = target_data.get('total_otps', 0)
                    msg = (
                        f"<tg-emoji emoji-id=\"5352861489541714456\">ðŸ‘¤</tg-emoji> <b>USER PROFILE</b>\n"
                        f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
                        f"<b>Name:</b> {safe_name}\n"
                        f"<b>ID:</b> <code>{target_uid}</code>\n"
                        f"<b>Balance:</b> {target_data.get('balance', 0):.2f} BDT\n"
                        f"<b>Total OTPs:</b> {total_otps}\n"
                        f"<b>Total Invites:</b> {target_data.get('total_invites', 0)}\n"
                        f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”"
                    )
                    if target_msg_id: edit_message(chat_id, target_msg_id, msg, reply_markup=get_user_profile_keyboard(target_uid))
                else:
                    if target_msg_id: edit_message(chat_id, target_msg_id, "âŒ <b>User not found in database!</b>", reply_markup=get_user_control_keyboard())
            except ValueError:
                if target_msg_id: edit_message(chat_id, target_msg_id, "âŒ <b>Invalid User ID format!</b>", reply_markup=get_user_control_keyboard())
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return
            
        elif isinstance(state, str) and state.startswith("waiting_uc_balance_"):
            target_uid = int(state[19:])
            try:
                amount_to_add = float(text.strip())
                update_user_stats(target_uid, amount_to_add, 0)
                
                target_data = get_user(target_uid)
                msg = (
                    f"âœ… <b>Balance Updated Successfully!</b>\n\n"
                    f"<tg-emoji emoji-id=\"5352861489541714456\">ðŸ‘¤</tg-emoji> <b>Name:</b> {html.escape(target_data['first_name'])}\n"
                    f"<tg-emoji emoji-id=\"5429612421977253466\">ðŸ’µ</tg-emoji> <b>New Balance:</b> {target_data['balance']:.2f} BDT"
                )
                if target_msg_id: edit_message(chat_id, target_msg_id, msg, reply_markup=get_user_profile_keyboard(target_uid))
            except ValueError:
                if target_msg_id: edit_message(chat_id, target_msg_id, "âŒ <b>Invalid amount format! Use numbers (e.g. 50 or -10).</b>", reply_markup=get_user_profile_keyboard(target_uid))
            del user_states[user_id]
            delete_message(chat_id, message_id)
            return

    if text in ["LIVE NUMBER", "LIVE TRAFFIC", "INVITE FRIEND", "WALLET", "LEADERBOARD", "OWNER PANEL"]:
        if user_id in user_states: del user_states[user_id]

    # ðŸŒŸ à¦šà§‡à¦• à¦•à¦°à¦¾ à¦¹à¦šà§à¦›à§‡ à¦‡à¦‰à¦œà¦¾à¦° à¦†à¦—à§‡ à¦¥à§‡à¦•à§‡à¦‡ à¦¡à¦¾à¦Ÿà¦¾à¦¬à§‡à¦¸à§‡ à¦†à¦›à§‡ à¦•à¦¿ à¦¨à¦¾
    is_new_user = (get_user(user_id) is None)

    add_user(user_id, first_name)
    user_data = get_user(user_id)

    if text.startswith("/start"):
        parts = text.split()
        if len(parts) > 1:
            param = parts[1]
            if param.startswith("alloc_"):
                try:
                    _, req_range, req_sid = param.split("_", 2)
                    
                    last_req = user_cooldowns.get(user_id, 0)
                    now = time.time()
                    if now - last_req < bot_settings.get("cooldown", 0):
                        send_message(chat_id, f"âŒ› <b>Please wait {int(bot_settings['cooldown'] - (now - last_req))} seconds before requesting again.</b>")
                        return
                    user_cooldowns[user_id] = now
                    
                    # ðŸŒŸ à¦®à§‡à¦¸à§‡à¦œ à¦ªà¦¾à¦ à¦¿à§Ÿà§‡ à¦®à§‡à¦¸à§‡à¦œ à¦†à¦‡à¦¡à¦¿ à¦•à§à¦¯à¦¾à¦š à¦•à¦°à¦¾
                    wait_msg = send_message(chat_id, f"â³ <b>Fetching number for {req_sid.title().replace('_', ' ')}...</b>")
                    
                    msg, markup = get_number_allocation_content(req_sid, req_range, user_id=user_id)
                    
                    # ðŸŒŸ à¦¨à¦¤à§à¦¨ à¦®à§‡à¦¸à§‡à¦œ à¦¨à¦¾ à¦¦à¦¿à§Ÿà§‡ à¦†à¦—à§‡à¦°à¦Ÿà¦¾à¦¤à§‡à¦‡ à¦à¦¡à¦¿à¦Ÿ à¦•à¦°à¦¾
                    if wait_msg and "result" in wait_msg:
                        edit_message(chat_id, wait_msg["result"]["message_id"], msg, reply_markup=markup)
                    else:
                        send_message(chat_id, msg, reply_markup=markup)
                    return
                except Exception:
                    pass
            else:
                try:
                    inviter_id = int(param)
                    # ðŸŒŸ à¦¶à§à¦§à§à¦®à¦¾à¦¤à§à¦° à¦¨à¦¤à§à¦¨ à¦‡à¦‰à¦œà¦¾à¦° à¦¹à¦²à§‡à¦‡ à¦°à§‡à¦«à¦¾à¦°à§‡à¦² à¦•à¦¾à¦‰à¦¨à§à¦Ÿ à¦¹à¦¬à§‡!
                    if is_new_user and inviter_id != user_id and get_user(inviter_id):
                        ref_amount = bot_settings.get("refer_reward", 0.2)
                        update_user_stats(inviter_id, ref_amount, 1)
                        send_message(inviter_id, f"ðŸŽ‰ <b>New Referral!</b>\nSomeone joined using your link. You received {ref_amount} BDT.")
                except ValueError: pass
        send_message(chat_id, f"ðŸ”¥ <b>PREMIUM NUMBER BOT </b>\n\nWelcome {html.escape(str(first_name))}, please select an option from the menu.", reply_markup=get_main_keyboard(user_id))
        
    elif text == "LIVE NUMBER":
        msg, markup = get_services_content()
        if markup:
            send_message(chat_id, msg, reply_markup=markup)
        else:
            send_message(chat_id, msg)
        
    elif text == "LIVE TRAFFIC":
        msg, markup = get_live_traffic_content()
        send_message(chat_id, msg, reply_markup=markup)
            
    elif text == "INVITE FRIEND":
        invite_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        ref_reward = bot_settings.get("refer_reward", 0.2)
        msg = (
            f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            f"<tg-emoji emoji-id=\"5420145051336485498\">ðŸ‘¥</tg-emoji> <b>Referral Program</b>\n"
            f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            f"<tg-emoji emoji-id=\"5420517437885943844\">ðŸ”—</tg-emoji> <b>Your Invite Link:</b>\n"
            f"<code>{invite_link}</code>\n"
            f"â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”\n"
            f"<tg-emoji emoji-id=\"5420396762189831222\">ðŸŽ</tg-emoji> <b>PER INVITE : {ref_reward} TK</b>\n"
            f"â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”\n"
            f"<tg-emoji emoji-id=\"5353032893096567467\">ðŸ“Š</tg-emoji> <b>Total Invites:</b> {user_data['total_invites']}\n"
            f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”"
        )
        send_message(chat_id, msg, reply_markup={"inline_keyboard": [[{"text": "COPY LINK", "icon_custom_emoji_id": "5379889727325350343", "copy_text": {"text": invite_link}, "style": "success"}]]})
        
    elif text == "WALLET":
        wallet_txt = (
            f"<tg-emoji emoji-id=\"5429105001655999635\">ðŸ’°</tg-emoji> <b>YOUR WALLET</b>\n"
            f"â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”\n"
            f"<tg-emoji emoji-id=\"5352861489541714456\">ðŸ‘¤</tg-emoji> <b>NAME :</b> {html.escape(str(first_name))}\n"
            f"â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”\n"
            f"<tg-emoji emoji-id=\"5226929552319594190\">ðŸ†”</tg-emoji> <b>ID :</b> <code>{user_id}</code>\n"
            f"â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”\n"
            f"<tg-emoji emoji-id=\"5429612421977253466\">ðŸ’µ</tg-emoji> <b>BALANCE : {user_data['balance']:.2f} BDT</b>\n"
            f"â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”\n"
            f"<tg-emoji emoji-id=\"5190899075968441286\">ðŸ’³</tg-emoji> <b>WITHDRAWAL METHODS :</b>"
        )
        kb = {"inline_keyboard": []}
        for method in bot_settings.get("w_methods", []):
            kb["inline_keyboard"].append([{"text": method, "icon_custom_emoji_id": "5431783519355444455", "callback_data": f"user_withdraw_{method}", "style": "primary"}])
        send_message(chat_id, wallet_txt, reply_markup=kb)
        
    elif text == "LEADERBOARD":
        send_message(chat_id, get_leaderboard_text(), reply_markup=get_leaderboard_keyboard())

    elif text == "OWNER PANEL":
        if user_id == ADMIN_ID:
            send_message(chat_id, get_owner_panel_text(), reply_markup=get_admin_inline_keyboard())
        else:
            send_message(chat_id, "âš ï¸ <b>Access Denied!</b>\nThis menu is restricted to the admin.")

def handle_callback(callback_query):
    global user_states, voltx_auto_mode, current_db_mode, force_join_status, force_join_channels, voltx_keys, otp_forward_groups, bot_settings
    query_id = callback_query["id"]
    user_id = callback_query["from"]["id"]
    data = callback_query["data"]
    chat_id = callback_query["message"]["chat"]["id"]
    message_id = callback_query["message"]["message_id"]

    if data == "check_fj_joined":
        if is_user_joined(user_id):
            delete_message(chat_id, message_id)
            send_message(chat_id, "âœ… <b>Thank you for joining! You can now use the bot.</b>", reply_markup=get_main_keyboard(user_id))
        else:
            answer_callback_query(query_id, "âŒ You haven't joined all channels!", show_alert=True)
        return

    if not is_user_joined(user_id):
        answer_callback_query(query_id, "Join channels first!", show_alert=True)
        return

    if data == "refresh_traffic":
        msg, markup = get_live_traffic_content()
        edit_message(chat_id, message_id, msg, reply_markup=markup)
        answer_callback_query(query_id, "Traffic Refreshed!")
        return

    if data == "back_to_services":
        msg, markup = get_services_content()
        edit_message(chat_id, message_id, msg, reply_markup=markup)
        answer_callback_query(query_id)
        return

    if data.startswith("srv_"):
        sid_short = data[4:]
        msg, markup, err = get_countries_content(sid_short)
        if err: answer_callback_query(query_id, err, show_alert=True)
        else:
            edit_message(chat_id, message_id, msg, reply_markup=markup)
            answer_callback_query(query_id)
        return

    if data.startswith("cc_"):
        parts = data.split("_")
        sid_short = parts[1]
        c_code = parts[2]
        
        last_req = user_cooldowns.get(user_id, 0)
        now = time.time()
        if now - last_req < bot_settings.get("cooldown", 0):
            answer_callback_query(query_id, f"Please wait {int(bot_settings['cooldown'] - (now - last_req))} seconds.", show_alert=True)
            return
        user_cooldowns[user_id] = now
        
        answer_callback_query(query_id, "Allocating number...")
        edit_message(chat_id, message_id, f"â³ <b>Fetching best top range and allocating number...</b>")
        
        msg, markup = get_number_allocation_content(sid_short, c_code, user_id=user_id)
        
        edit_message(chat_id, message_id, msg, reply_markup=markup)
        return

    if data == "refresh_leaderboard":
        edit_message(chat_id, message_id, get_leaderboard_text(), reply_markup=get_leaderboard_keyboard())
        answer_callback_query(query_id, "Leaderboard Refreshed!")
        return

    if data.startswith("user_withdraw_"):
        method = data[14:]
        user_data = get_user(user_id)
        bal = user_data.get("balance", 0)
        min_w = bot_settings.get("min_withdraw", 10.0)
        
        if bal < min_w:
            answer_callback_query(query_id, f"âŒ Minimum withdraw is {min_w} BDT. You have {bal:.2f} BDT.", show_alert=True)
            return
            
        user_states[user_id] = {"state": f"waiting_withdraw_amount_{method}", "msg_id": message_id}
        edit_message(chat_id, message_id, f"ðŸ’³ <b>Withdraw via {method}</b>\n\nðŸ’µ Your Balance: {bal:.2f} BDT\nðŸ’¬ <b>Enter the amount you want to withdraw:</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
        return

    if data == "user_cancel":
        if user_id in user_states: del user_states[user_id]
        delete_message(chat_id, message_id)
        send_message(chat_id, "âŒ Action Cancelled.", reply_markup=get_main_keyboard(user_id))
        answer_callback_query(query_id)
        return

    # Admin Operations Only
    if user_id != ADMIN_ID:
        answer_callback_query(query_id, "Access Denied!", show_alert=True)
        return
        
    if data.startswith("admin_w_approve_") or data.startswith("admin_w_reject_"):
        if user_id != ADMIN_ID:
            answer_callback_query(query_id, "âš ï¸ Access Denied! You cannot perform this action.", show_alert=True)
            return

        parts = data.split("_")
        action = parts[2]
        req_user_id = int(parts[3])
        amount = float(parts[4])
        acc_number = parts[5]
        
        masked_number = f"{acc_number[:3]}DXA{acc_number[-3:]}" if len(acc_number) >= 6 else acc_number
        
        msg_text = callback_query.get("message", {}).get("text", "")
        fname_match = re.search(r"User:\s*(.+)", msg_text)
        req_first_name = fname_match.group(1) if fname_match else "User"
        method_match = re.search(r"Method:\s*(.+)", msg_text)
        req_method = method_match.group(1) if method_match else "Unknown"
        
        if action == "approve":
            btn_text = "APPROVED BY ADMIN"
            btn_style = "success"
            btn_icon = "5352694861990501856"
            send_message(req_user_id, f"<tg-emoji emoji-id=\"5420396762189831222\">ðŸŽ‰</tg-emoji> <b>Withdrawal Approved!</b>\nYour request of {amount:.2f} BDT has been sent to <code>{masked_number}</code>.")
        else:
            btn_text = "REJECTED BY ADMIN"
            btn_style = "danger"
            btn_icon = "5420130255174145507"
            update_user_stats(req_user_id, amount, 0)
            send_message(req_user_id, f"<tg-emoji emoji-id=\"5336944168944047463\">âš ï¸</tg-emoji> <b>Withdrawal Rejected!</b>\nYour request of {amount:.2f} BDT to <code>{masked_number}</code> was rejected and refunded.")
            
        updated_msg = (
            f"<tg-emoji emoji-id=\"5420396762189831222\">ðŸ†•</tg-emoji> <b>WITHDRAW REQUEST PROCESSED</b>\n"
            f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            f"<tg-emoji emoji-id=\"5352861489541714456\">ðŸ‘¤</tg-emoji> <b>User:</b> <a href='tg://user?id={req_user_id}'>{html.escape(req_first_name)}</a>\n"
            f"â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”\n"
            f"<tg-emoji emoji-id=\"5226929552319594190\">ðŸ†”</tg-emoji> <b>ID:</b> <code>{req_user_id}</code>\n"
            f"â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”\n"
            f"<tg-emoji emoji-id=\"5429612421977253466\">ðŸ’µ</tg-emoji> <b>Amount:</b> <b>{amount:.2f} BDT</b>\n"
            f"â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”\n"
            f"<tg-emoji emoji-id=\"5190899075968441286\">ðŸ’³</tg-emoji> <b>Method:</b> {req_method}\n"
            f"â€” â€” â€” â€” â€” â€” â€” â€” â€” â€”\n"
            f"<tg-emoji emoji-id=\"5431783519355444455\">ðŸ“ž</tg-emoji> <b>Number:</b> <code>{masked_number}</code>\n"
            f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”"
        )
        
        updated_markup = {
            "inline_keyboard": [
                [{"text": btn_text, "icon_custom_emoji_id": btn_icon, "callback_data": "ignore_action", "style": btn_style}]
            ]
        }
        
        edit_message(chat_id, message_id, updated_msg, reply_markup=updated_markup)
        answer_callback_query(query_id, f"Request {action.title()}d!")
        return

    # ===== Voltx Key Manager =====
    if data == "manage_voltx":
        edit_message(chat_id, message_id, "ðŸ”‘ <b>VOLTX KEY SYSTEM</b>\nManage API Keys below:", reply_markup=get_voltx_keys_keyboard())
        answer_callback_query(query_id)
    elif data == "toggle_vk":
        voltx_auto_mode = not voltx_auto_mode
        save_local_data()
        edit_message(chat_id, message_id, "ðŸ”‘ <b>VOLTX KEY SYSTEM</b>\nManage API Keys below:", reply_markup=get_voltx_keys_keyboard())
        answer_callback_query(query_id, f"Voltx Mode: {'ON' if voltx_auto_mode else 'OFF'}")
    elif data == "add_vk":
        user_states[user_id] = {"state": "waiting_vk_key", "msg_id": message_id}
        edit_message(chat_id, message_id, "ðŸ”‘ <b>Please reply to this message with the new Voltx API Key.</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
    elif data.startswith("del_vk_"):
        idx = int(data[7:])
        if idx < len(voltx_keys): 
            if len(voltx_keys) > 1:
                voltx_keys.pop(idx)
                save_local_data()
                edit_message(chat_id, message_id, "ðŸ”‘ <b>VOLTX KEY SYSTEM</b>\nManage API Keys below:", reply_markup=get_voltx_keys_keyboard())
                answer_callback_query(query_id, "Key Deleted!")
            else:
                answer_callback_query(query_id, "Cannot delete the only key!", show_alert=True)

    # ===== Force Join Manager =====
    elif data == "manage_fj":
        edit_message(chat_id, message_id, "ðŸ”— <b>FORCE JOIN SYSTEM</b>\nManage channels below:", reply_markup=get_force_join_keyboard())
        answer_callback_query(query_id)
    elif data == "toggle_fj":
        force_join_status = not force_join_status
        save_local_data()
        edit_message(chat_id, message_id, "ðŸ”— <b>FORCE JOIN SYSTEM</b>\nManage channels below:", reply_markup=get_force_join_keyboard())
        answer_callback_query(query_id, f"Force Join: {'ON' if force_join_status else 'OFF'}")
    elif data == "add_fj":
        user_states[user_id] = {"state": "waiting_fj_channel", "msg_id": message_id}
        select_kb = {"keyboard": [[{"text": "Select Force Join Channel", "request_chat": {"request_id": 3, "chat_is_channel": True}}], [{"text": "ðŸ”™ BACK"}]], "resize_keyboard": True, "one_time_keyboard": True}
        send_message(chat_id, "ðŸ‘‡ <b>Select Channel from below:</b>\n<i>(Make sure bot is an admin there)</i>", reply_markup=select_kb)
        answer_callback_query(query_id)
    elif data.startswith("del_fj_"):
        idx = int(data[7:])
        if idx < len(force_join_channels): force_join_channels.pop(idx)
        save_local_data()
        edit_message(chat_id, message_id, "ðŸ”— <b>FORCE JOIN SYSTEM</b>\nManage channels below:", reply_markup=get_force_join_keyboard())
        answer_callback_query(query_id, "Channel Deleted!")

    # ===== OTP Group Manager =====
    elif data == "manage_otp_group":
        edit_message(chat_id, message_id, "ðŸ›¡ <b>OTP GROUP MANAGEMENT</b>\nManage settings below:", reply_markup=get_otp_group_keyboard())
        answer_callback_query(query_id)
    elif data == "add_otp_group":
        user_states[user_id] = {"state": "waiting_otp_group", "msg_id": message_id}
        select_kb = {"keyboard": [[{"text": "Select OTP Group", "request_chat": {"request_id": 1, "chat_is_channel": False}}], [{"text": "ðŸ”™ BACK"}]], "resize_keyboard": True, "one_time_keyboard": True}
        send_message(chat_id, "ðŸ‘‡ <b>Select OTP Group from below:</b>", reply_markup=select_kb)
        answer_callback_query(query_id)
    elif data.startswith("del_otp_group_"):
        idx = int(data[14:])
        if idx < len(otp_forward_groups): otp_forward_groups.pop(idx)
        save_local_data()
        edit_message(chat_id, message_id, "ðŸ›¡ <b>OTP GROUP MANAGEMENT</b>\nManage settings below:", reply_markup=get_otp_group_keyboard())
        answer_callback_query(query_id, "Group Deleted!")
    elif data == "edit_otp_link":
        user_states[user_id] = {"state": "waiting_otp_link", "msg_id": message_id}
        edit_message(chat_id, message_id, "ðŸ”— <b>Please send the new URL for the inline button attached to forwarded OTPs.</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
    elif data == "edit_main_channel":
        user_states[user_id] = {"state": "waiting_main_channel_link", "msg_id": message_id}
        edit_message(chat_id, message_id, "ðŸ”— <b>Please send the URL for the MAIN CHANNEL inline button.</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)

    # ===== DXA Control Panel =====
    elif data == "dxa_control":
        edit_message(chat_id, message_id, "âš™ï¸ <b>DXA CONTROL PANEL</b>\nManage core bot configurations:", reply_markup=dxa_control_keyboard())
        answer_callback_query(query_id)
    elif data == "dxa_min_w":
        user_states[user_id] = {"state": "waiting_dxa_min_w", "msg_id": message_id}
        edit_message(chat_id, message_id, "ðŸ’¸ <b>Enter new Minimum Withdraw Amount (e.g. 50):</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
    elif data == "dxa_ref_r":
        user_states[user_id] = {"state": "waiting_dxa_ref_r", "msg_id": message_id}
        edit_message(chat_id, message_id, "ðŸ’¸ <b>Enter new Referral Reward Amount (e.g. 5.0):</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
    elif data == "dxa_otp_control":
        edit_message(chat_id, message_id, "ðŸ’° <b>OTP REWARD CONTROL</b>\nManage rates below:", reply_markup=dxa_otp_control_keyboard())
        answer_callback_query(query_id)
    elif data == "dxa_def_rate":
        user_states[user_id] = {"state": "waiting_dxa_def_rate", "msg_id": message_id}
        edit_message(chat_id, message_id, "ðŸ’° <b>Enter new Default OTP Rate (e.g. 0.5):</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
        
    elif data.startswith("del_srv_rate_"):
        srv_name = data[13:]
        if srv_name in bot_settings["otp_service_rates"]:
            del bot_settings["otp_service_rates"][srv_name]
            save_local_data()
        edit_message(chat_id, message_id, "ðŸ’° <b>OTP REWARD CONTROL</b>\nManage rates below:", reply_markup=dxa_otp_control_keyboard())
        answer_callback_query(query_id, f"Rate for {srv_name} deleted!")
    elif data == "dxa_srv_rate":
        user_states[user_id] = {"state": "waiting_dxa_srv_rate", "msg_id": message_id}
        edit_message(chat_id, message_id, "ðŸ’° <b>Enter Specific Service Rate.</b>\nFormat: <code>ServiceName - Rate</code>\nExample: <code>Telegram - 2.5</code>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
    elif data == "dxa_cool":
        user_states[user_id] = {"state": "waiting_dxa_cool", "msg_id": message_id}
        edit_message(chat_id, message_id, "â³ <b>Enter new Cooldown time in seconds (e.g. 10):</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
    elif data == "dxa_num_req":
        user_states[user_id] = {"state": "waiting_dxa_num_req", "msg_id": message_id}
        edit_message(chat_id, message_id, "ðŸ“± <b>Enter how many numbers a user gets per request (e.g. 3):</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
    elif data == "manage_w_methods":
        edit_message(chat_id, message_id, "ðŸ’³ <b>WITHDRAW METHODS</b>\nManage methods below:", reply_markup=dxa_manage_w_methods_keyboard())
        answer_callback_query(query_id)
    elif data == "add_w_method":
        user_states[user_id] = {"state": "waiting_w_method", "msg_id": message_id}
        edit_message(chat_id, message_id, "ðŸ’³ <b>Enter new Withdraw Method Name (e.g. bKash):</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
    elif data.startswith("del_w_method_"):
        idx = int(data[13:])
        if idx < len(bot_settings["w_methods"]): bot_settings["w_methods"].pop(idx)
        save_local_data()
        edit_message(chat_id, message_id, "ðŸ’³ <b>WITHDRAW METHODS</b>\nManage methods below:", reply_markup=dxa_manage_w_methods_keyboard())
        answer_callback_query(query_id, "Method Deleted!")
    elif data == "dxa_w_group":
        user_states[user_id] = {"state": "waiting_dxa_w_group", "msg_id": message_id}
        select_kb = {"keyboard": [[{"text": "Select Withdraw Group", "request_chat": {"request_id": 2, "chat_is_channel": False}}], [{"text": "ðŸ”™ BACK"}]], "resize_keyboard": True, "one_time_keyboard": True}
        send_message(chat_id, "ðŸ‘‡ <b>Select Withdraw Group from below:</b>", reply_markup=select_kb)
        answer_callback_query(query_id)

    # ===== Broadcast System =====
    elif data == "broadcast_menu":
        user_states[user_id] = {"state": "waiting_broadcast", "msg_id": message_id}
        edit_message(chat_id, message_id, "ðŸ“£ <b>BROADCAST SYSTEM</b>\n\nSend any text, photo, video, or audio message you want to broadcast to all users.", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)

    elif data == "upload_firebase":
        user_states[user_id] = {"state": "waiting_firebase", "msg_id": message_id}
        edit_message(chat_id, message_id, "ðŸ”¥ <b>FIREBASE SETUP</b>\n\nPlease reply with the <b>entire JSON content</b> of your Firebase Service Account file.", reply_markup=get_upload_firebase_keyboard())
        answer_callback_query(query_id, "Send JSON Now")

    # ===== User Control =====
    elif data == "user_control":
        msg = f"ðŸ‘¥ <b>USER CONTROL</b>\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ“Š <b>Total Users:</b> {get_total_users()}\n\nðŸ‘‡ Manage users below:"
        edit_message(chat_id, message_id, msg, reply_markup=get_user_control_keyboard())
        answer_callback_query(query_id)
        
    elif data == "uc_profile":
        user_states[user_id] = {"state": "waiting_uc_id", "msg_id": message_id}
        edit_message(chat_id, message_id, "ðŸ†” <b>Send the Telegram User ID to view profile:</b>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
        
    elif data.startswith("uc_balance_"):
        target_uid = int(data[11:])
        user_states[user_id] = {"state": f"waiting_uc_balance_{target_uid}", "msg_id": message_id}
        edit_message(chat_id, message_id, f"ðŸ’µ <b>Send the amount to Add or Subtract.</b>\n<i>(Examples: To add use 50, to deduct use -10)</i>", reply_markup=get_back_only_keyboard())
        answer_callback_query(query_id)
        
    elif data == "back_to_admin":
        if user_id in user_states: del user_states[user_id]
        edit_message(chat_id, message_id, get_owner_panel_text(), reply_markup=get_admin_inline_keyboard())
        answer_callback_query(query_id)
        
    elif data == "db_status": 
        answer_callback_query(query_id, f"Current DB: {current_db_mode.upper()}", show_alert=True)
        
    elif data == "close_panel":
        answer_callback_query(query_id, "Closed")
        delete_message(chat_id, message_id)
        
    else:
        answer_callback_query(query_id, f"{data} clicked!", show_alert=True)

# ==========================================
# Main
# ==========================================
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

if __name__ == "__main__":
    threading.Thread(target=run_bot_polling, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)
