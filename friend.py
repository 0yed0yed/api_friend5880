# fast_spammer.py
import requests
import json
import threading
import time
import base64
import tempfile
import os
import sys
import importlib.util
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from flask import Flask, request, jsonify
import urllib3
import gc
from concurrent.futures import ThreadPoolExecutor

try:
    from byte import Encrypt_ID, encrypt_api
except ImportError:
    def Encrypt_ID(uid: str) -> str:
        return uid.encode().hex()
    def encrypt_api(payload: str) -> str:
        return payload.encode().hex()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

REGION_MAP = {
    "ind": "https://client.ind.freefiremobile.com",
    "me": "https://clientbp.ggpolarbear.com",
    "vn": "https://clientbp.ggpolarbear.com",
    "bd": "https://clientbp.ggpolarbear.com",
    "pk": "https://clientbp.ggpolarbear.com",
    "sg": "https://clientbp.ggpolarbear.com",
    "br": "https://client.us.freefiremobile.com",
    "na": "https://client.us.freefiremobile.com",
    "id": "https://clientbp.ggpolarbear.com",
    "ru": "https://clientbp.ggpolarbear.com",
    "th": "https://clientbp.ggpolarbear.com",
}

ALL_REGIONS = list(REGION_MAP.items())

OAUTH_URL = "https://100067.connect.garena.com/oauth/guest/token/grant"
MAJOR_LOGIN_URL = "https://loginbp.ggpolarbear.com/MajorLogin"
CLIENT_ID = "100067"
CLIENT_SECRET = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
PROTO_KEY = b'Yg&tc%DEuh6%Zc^8'
PROTO_IV = b'6oyZDr22E3ychjM%'

BASE_HEADERS = {
    'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 11; ASUS_Z01QD Build/PI)",
    'Connection': "Keep-Alive",
    'Accept-Encoding': "gzip",
    'Content-Type': "application/x-www-form-urlencoded",
    'Expect': "100-continue",
    'X-Unity-Version': "2018.4.11f1",
    'X-GA': "v1 1",
    'ReleaseVersion': "OB53"
}

MAJOR_LOGIN_REQ_B64 = "ChNNYWpvckxvZ2luUmVxLnByb3RvIvoKCgpNYWpvckxvZ2luEhIKCmV2ZW50X3RpbWUYAyABKAkSEQoJZ2FtZV9uYW1lGAQgASgJEhMKC3BsYXRmb3JtX2lkGAUgASgFEhYKDmNsaWVudF92ZXJzaW9uGAcgASgJEhcKD3N5c3RlbV9zb2Z0d2FyZRgIIAEoCRIXCg9zeXN0ZW1faGFyZHdhcmUYCSABKAkSGAoQdGVsZWNvbV9vcGVyYXRvchgKIAEoCRIUCgxuZXR3b3JrX3R5cGUYCyABKAkSFAoMc2NyZWVuX3dpZHRoGAwgASgNEhUKDXNjcmVlbl9oZWlnaHQYDSABKA0SEgoKc2NyZWVuX2RwaRgOIAEoCRIZChFwcm9jZXNzb3JfZGV0YWlscxgPIAEoCRIOCgZtZW1vcnkYECABKA0SFAoMZ3B1X3JlbmRlcmVyGBEgASgJEhMKC2dwdV92ZXJzaW9uGBIgASgJEhgKEHVuaXF1ZV9kZXZpY2VfaWQYEyABKAkSEQoJY2xpZW50X2lwGBQgASgJEhAKCGxhbmd1YWdlGBUgASgJEg8KB29wZW5faWQYFiABKAkSFAoMb3Blbl9pZF90eXBlGBcgASgJEhMKC2RldmljZV90eXBlGBggASgJEicKEG1lbW9yeV9hdmFpbGFibGUYGSABKAsyDS5HYW1lU2VjdXJpdHkSFAoMYWNjZXNzX3Rva2VuGB0gASgJEhcKD3BsYXRmb3JtX3Nka19pZBgeIAEoBRIaChJuZXR3b3JrX29wZXJhdG9yX2EYKSABKAkSFgoObmV0d29ya190eXBlX2EYKiABKAkSHAoUY2xpZW50X3VzaW5nX3ZlcnNpb24YOSABKAkSHgoWZXh0ZXJuYWxfc3RvcmFnZV90b3RhbBg8IAEoBRIiChpleHRlcm5hbF9zdG9yYWdlX2F2YWlsYWJsZRg9IAEoBRIeChZpbnRlcm5hbF9zdG9yYWdlX3RvdGFsGD4gASgFEiIKGmludGVybmFsX3N0b3JhZ2VfYXZhaWxhYmxlGD8gASgFEiMKG2dhbWVfZGlza19zdG9yYWdlX2F2YWlsYWJsZRhAIAEoBRIfChdnYW1lX2Rpc2tfc3RvcmFnZV90b3RhbBhBIAEoBRIlCh1leHRlcm5hbF9zZGNhcmRfYXZhaWxfc3RvcmFnZRhCIAEoBRIlCh1leHRlcm5hbF9zZGNhcmRfdG90YWxfc3RvcmFnZRhDIAEoBRIQCghsb2dpbl9ieRhJIAEoBRIUCgxsaWJyYXJ5X3BhdGgYSiABKAkSEgoKcmVnX2F2YXRhchhMIAEoBRIVCg1saWJyYXJ5X3Rva2VuGE0gASgJEhQKDGNoYW5uZWxfdHlwZRhOIAEoBRIQCghjcHVfdHlwZRhPIAEoBRIYChBjcHVfYXJjaGl0ZWN0dXJlGFEgASgJEhsKE2NsaWVudF92ZXJzaW9uX2NvZGUYUyABKAkSFAoMZ3JhcGhpY3NfYXBpGFYgASgJEh0KFXN1cHBvcnRlZF9hc3RjX2JpdHNldBhXIAEoDRIaChJsb2dpbl9vcGVuX2lkX3R5cGUYWCABKAUSGAoQYW5hbHl0aWNzX2RldGFpbBhZIAEoDBIUCgxsb2FkaW5nX3RpbWUYXCABKA0SFwoPcmVsZWFzZV9jaGFubmVsGF0gASgJEhIKCmV4dHJhX2luZm8YXiABKAkSIAoYYW5kcm9pZF9lbmdpbmVfaW5pdF9mbGFnGF8gASgNEg8KB2lmX3B1c2gYYSABKAUSDgoGaXNfdnBuGGIgASgFEhwKFG9yaWdpbl9wbGF0Zm9ybV90eXBlGGMgASgJEh0KFXByaW1hcnlfcGxhdGZvcm1fdHlwZRhkIAEoCSI1CgxHYW1lU2VjdXJpdHkSDwoHdmVyc2lvbhgGIAEoBRIUCgxoaWRkZW5fdmFsdWUYCCABKARiBnByb3RvMw=="
MAJOR_LOGIN_RES_B64 = "ChNNYWpvckxvZ2luUmVzLnByb3RvInwKDU1ham9yTG9naW5SZXMSEwoLYWNjb3VudF91aWQYASABKAQSDgoGcmVnaW9uGAIgASgJEg0KBXRva2VuGAggASgJEgsKA3VybBgKIAEoCRIRCgl0aW1lc3RhbXAYFSABKAMSCwoDa2V5GBYgASgMEgoKAml2GBcgASgMYgZwcm90bzM="
GET_LOGIN_DATA_B64 = "ChVHZXRMb2dpbkRhdGFSZXMucHJvdG8ipAEKDEdldExvZ2luRGF0YRISCgpBY2NvdW50VUlEGAEgASgEEg4KBlJlZ2lvbhgDIAEoCRITCgtBY2NvdW50TmFtZRgEIAEoCRIWCg5PbmxpbmVfSVBfUG9ydBgOIAEoCRIPCgdDbGFuX0lEGBQgASgDEhYKDkFjY291bnRJUF9Qb3J0GCAgASgJEhoKEkNsYW5fQ29tcGlsZWRfRGF0YRg3IAEoCWIGcHJvdG8z"

active_sessions = {}
sessions_lock = threading.Lock()

# إعدادات السرعة
DEFAULT_THREADS = 100
DEFAULT_DELAY = 0  # بدون تأخير لأقصى سرعة

def load_protobuf_classes():
    classes = {}
    temp_dir = tempfile.mkdtemp()
    
    req_code = f'''
# -*- coding: utf-8 -*-
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
import base64
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(base64.b64decode("{MAJOR_LOGIN_REQ_B64}"))
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'MajorLoginReq_pb2', _globals)
'''
    res_code = f'''
# -*- coding: utf-8 -*-
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
import base64
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(base64.b64decode("{MAJOR_LOGIN_RES_B64}"))
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'MajorLoginRes_pb2', _globals)
'''
    data_code = f'''
# -*- coding: utf-8 -*-
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
import base64
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(base64.b64decode("{GET_LOGIN_DATA_B64}"))
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'GetLoginDataRes_pb2', _globals)
'''
    req_path = os.path.join(temp_dir, 'MajorLoginReq_pb2.py')
    with open(req_path, 'w') as f:
        f.write(req_code)
    spec = importlib.util.spec_from_file_location("MajorLoginReq_pb2", req_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["MajorLoginReq_pb2"] = module
    spec.loader.exec_module(module)
    classes['MajorLogin'] = module.MajorLogin
    classes['GameSecurity'] = module.GameSecurity
    
    res_path = os.path.join(temp_dir, 'MajorLoginRes_pb2.py')
    with open(res_path, 'w') as f:
        f.write(res_code)
    spec = importlib.util.spec_from_file_location("MajorLoginRes_pb2", res_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["MajorLoginRes_pb2"] = module
    spec.loader.exec_module(module)
    classes['MajorLoginRes'] = module.MajorLoginRes
    
    data_path = os.path.join(temp_dir, 'GetLoginDataRes_pb2.py')
    with open(data_path, 'w') as f:
        f.write(data_code)
    spec = importlib.util.spec_from_file_location("GetLoginDataRes_pb2", data_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["GetLoginDataRes_pb2"] = module
    spec.loader.exec_module(module)
    classes['GetLoginData'] = module.GetLoginData
    
    return classes

PB = load_protobuf_classes()
MajorLogin = PB['MajorLogin']
GameSecurity = PB['GameSecurity']
MajorLoginRes = PB['MajorLoginRes']
GetLoginData = PB['GetLoginData']

def encrypt_proto(payload_bytes):
    cipher = AES.new(PROTO_KEY, AES.MODE_CBC, PROTO_IV)
    padded = pad(payload_bytes, AES.block_size)
    return cipher.encrypt(padded)

def decrypt_proto(encrypted_bytes):
    cipher = AES.new(PROTO_KEY, AES.MODE_CBC, PROTO_IV)
    decrypted = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
    return decrypted

def generate_access_token(uid, password):
    headers = {
        "Host": "100067.connect.garena.com",
        "User-Agent": "GarenaMSDK/5.5.2P3",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "close"
    }
    data = {
        "uid": uid, "password": password, "response_type": "token",
        "client_type": "2", "client_secret": CLIENT_SECRET, "client_id": CLIENT_ID
    }
    try:
        response = requests.post(OAUTH_URL, headers=headers, data=data, timeout=5, verify=False)
        if response.status_code == 200:
            resp_data = response.json()
            return resp_data.get("open_id"), resp_data.get("access_token"), None
        else:
            return None, None, None
    except:
        return None, None, None

def build_major_login_message(open_id, access_token):
    major_login = MajorLogin()
    major_login.event_time = str(datetime.now())[:-7]
    major_login.game_name = "free fire"
    major_login.platform_id = 1
    major_login.client_version = "1.123.1"
    major_login.system_software = "Android OS 9"
    major_login.system_hardware = "Handheld"
    major_login.telecom_operator = "Verizon"
    major_login.network_type = "WIFI"
    major_login.screen_width = 1920
    major_login.screen_height = 1080
    major_login.screen_dpi = "280"
    major_login.processor_details = "ARM64"
    major_login.memory = 3003
    major_login.gpu_renderer = "Adreno"
    major_login.gpu_version = "OpenGL ES 3.1"
    major_login.unique_device_id = "Google|test"
    major_login.client_ip = "223.191.51.89"
    major_login.language = "en"
    major_login.open_id = open_id
    major_login.open_id_type = "4"
    major_login.device_type = "Handheld"
    major_login.memory_available.version = 55
    major_login.memory_available.hidden_value = 81
    major_login.access_token = access_token
    major_login.platform_sdk_id = 1
    major_login.network_operator_a = "Verizon"
    major_login.network_type_a = "WIFI"
    major_login.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    major_login.external_storage_total = 36235
    major_login.external_storage_available = 31335
    major_login.internal_storage_total = 2519
    major_login.internal_storage_available = 703
    major_login.game_disk_storage_available = 25010
    major_login.game_disk_storage_total = 26628
    major_login.external_sdcard_avail_storage = 32992
    major_login.external_sdcard_total_storage = 36235
    major_login.login_by = 3
    major_login.library_path = "/data/app/lib/arm64"
    major_login.reg_avatar = 1
    major_login.library_token = "test"
    major_login.channel_type = 3
    major_login.cpu_type = 2
    major_login.cpu_architecture = "64"
    major_login.client_version_code = "2019118695"
    major_login.graphics_api = "OpenGLES2"
    major_login.supported_astc_bitset = 16383
    major_login.login_open_id_type = 4
    major_login.analytics_detail = b"test"
    major_login.loading_time = 13564
    major_login.release_channel = "android"
    major_login.extra_info = "test"
    major_login.android_engine_init_flag = 110009
    major_login.if_push = 1
    major_login.is_vpn = 1
    major_login.origin_platform_type = "4"
    major_login.primary_platform_type = "4"
    return major_login.SerializeToString()

def major_login(open_id, access_token):
    proto_payload = build_major_login_message(open_id, access_token)
    encrypted_payload = encrypt_proto(proto_payload)
    try:
        response = requests.post(MAJOR_LOGIN_URL, data=encrypted_payload, headers=BASE_HEADERS, timeout=5, verify=False)
        if response.status_code == 200:
            res = MajorLoginRes()
            res.ParseFromString(response.content)
            if res.token:
                return True, res.token
            return False, None
        else:
            return False, None
    except:
        return False, None

def get_jwt_token(uid, password):
    open_id, access_token, _ = generate_access_token(uid, password)
    if not open_id:
        return None
    success, token = major_login(open_id, access_token)
    if not success:
        return None
    return token

def send_friend_request(target_uid, token, region_server_url):
    try:
        encrypted_id = Encrypt_ID(target_uid)
        payload = f"08a7c4839f1e10{encrypted_id}1801"
        encrypted_payload = encrypt_api(payload)
        url = f"{region_server_url}/RequestAddingFriend"
        headers = {
            "Expect": "100-continue",
            "Authorization": f"Bearer {token}",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB53",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9)",
            "Connection": "close",
            "Accept-Encoding": "gzip, deflate, br"
        }
        response = requests.post(url, headers=headers, data=bytes.fromhex(encrypted_payload), timeout=3)
        return response.status_code == 200
    except:
        return False

def load_accounts():
    accounts = []
    try:
        with open("accounts.txt", "r") as f:
            for line in f:
                line = line.strip()
                if not line or ':' not in line:
                    continue
                uid, pwd = line.split(':', 1)
                accounts.append({"uid": uid, "password": pwd})
        return accounts
    except:
        return []

# ============ وضع السرعة الفائقة ============
def ultra_fast_spammer(target_uid, region=None, num_threads=100, delay=0):
    """أقصى سرعة ممكنة - آلاف الطلبات في الدقيقة"""
    accounts = load_accounts()
    if not accounts:
        return
    
    if region and region.lower() in REGION_MAP:
        regions_to_try = [(region.lower(), REGION_MAP[region.lower()])]
    else:
        regions_to_try = ALL_REGIONS
    
    with sessions_lock:
        if target_uid not in active_sessions:
            return
        stop_event = active_sessions[target_uid]["stop_event"]
        stats = active_sessions[target_uid]["stats"]
    
    # إنشاء طابور ضخم من المهام
    task_list = []
    for _ in range(1000):  # تكرار كل حساب 1000 مرة
        for acc in accounts:
            task_list.append(acc)
    
    task_index = 0
    task_lock = threading.Lock()
    
    request_session = requests.Session()
    request_session.verify = False
    
    def get_next_task():
        nonlocal task_index
        with task_lock:
            if task_index >= len(task_list):
                task_index = 0  # إعادة تعيين الطابور
            task = task_list[task_index]
            task_index += 1
            return task
    
    def worker():
        consecutive_failures = 0
        
        while not stop_event.is_set():
            account = get_next_task()
            
            token = get_jwt_token(account['uid'], account['password'])
            if token:
                for region_name, server_url in regions_to_try:
                    if stop_event.is_set():
                        return
                    if send_friend_request(target_uid, token, server_url):
                        with sessions_lock:
                            if target_uid in active_sessions:
                                stats["success"] += 1
                                stats["total"] += 1
                        consecutive_failures = 0
                        break
                    else:
                        with sessions_lock:
                            if target_uid in active_sessions:
                                stats["failed"] += 1
                                stats["total"] += 1
                        consecutive_failures += 1
            else:
                with sessions_lock:
                    if target_uid in active_sessions:
                        stats["failed"] += 1
                        stats["total"] += 1
                consecutive_failures += 1
            
            if consecutive_failures > 20:
                time.sleep(2)
                consecutive_failures = 0
            
            if delay > 0:
                time.sleep(delay)
    
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()
        threads.append(t)
    
    # مراقبة الإحصائيات
    last_total = 0
    while not stop_event.is_set():
        time.sleep(5)
        with sessions_lock:
            if target_uid in active_sessions:
                current_total = stats["total"]
                rpm = (current_total - last_total) * 12  # *12 لأن 5 ثواني = 12 فترة في الدقيقة
                last_total = current_total
                stats["current_rpm"] = rpm

@app.route('/start/fast', methods=['GET'])
def start_fast():
    """بدء سبام بأقصى سرعة"""
    target_uid = request.args.get('uid')
    if not target_uid:
        return jsonify({"error": "Missing 'uid' parameter"}), 400
    
    threads = request.args.get('threads', DEFAULT_THREADS, type=int)
    delay = request.args.get('delay', DEFAULT_DELAY, type=float)
    region = request.args.get('region')
    
    # تحديد الحد الأقصى للخيوط
    if threads > 500:
        return jsonify({"error": "Maximum threads is 500"}), 400
    
    with sessions_lock:
        if target_uid in active_sessions:
            return jsonify({"error": f"Target {target_uid} is already being spammed"}), 409
    
    accounts = load_accounts()
    if not accounts:
        return jsonify({"error": "No accounts found in accounts.txt"}), 404
    
    stop_event = threading.Event()
    stats = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "start_time": datetime.now().isoformat(),
        "mode": "ULTRA_FAST",
        "current_rpm": 0
    }
    
    with sessions_lock:
        active_sessions[target_uid] = {
            "active": True,
            "stop_event": stop_event,
            "stats": stats,
            "region": region,
            "threads": threads,
            "delay": delay
        }
    
    thread = threading.Thread(target=ultra_fast_spammer, args=(target_uid, region, threads, delay))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "status": "started",
        "target_uid": target_uid,
        "threads": threads,
        "delay": f"{delay}s" if delay > 0 else "0s (MAX SPEED)",
        "total_accounts": len(accounts),
        "mode": "⚡ ULTRA FAST ⚡",
        "warning": "هذا الوضع يستهلك موارد عالية!",
        "estimated_speed": f"~{threads * 60} to {threads * 120} requests/minute",
        "infinite": "YES - use /stop to stop"
    })

@app.route('/start/balanced', methods=['GET'])
def start_balanced():
    """بدء سبام متوازن - أقل استهلاك للموارد"""
    target_uid = request.args.get('uid')
    if not target_uid:
        return jsonify({"error": "Missing 'uid' parameter"}), 400
    
    threads = request.args.get('threads', 10, type=int)
    delay = request.args.get('delay', 0.5, type=float)
    
    if threads > 50:
        threads = 50
    
    with sessions_lock:
        if target_uid in active_sessions:
            return jsonify({"error": f"Target {target_uid} is already being spammed"}), 409
    
    accounts = load_accounts()
    if not accounts:
        return jsonify({"error": "No accounts found in accounts.txt"}), 404
    
    stop_event = threading.Event()
    stats = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "start_time": datetime.now().isoformat(),
        "mode": "BALANCED"
    }
    
    with sessions_lock:
        active_sessions[target_uid] = {
            "active": True,
            "stop_event": stop_event,
            "stats": stats,
            "threads": threads,
            "delay": delay
        }
    
    thread = threading.Thread(target=ultra_fast_spammer, args=(target_uid, None, threads, delay))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "status": "started",
        "target_uid": target_uid,
        "threads": threads,
        "delay": f"{delay}s",
        "total_accounts": len(accounts),
        "mode": "⚖️ BALANCED ⚖️",
        "estimated_speed": f"~{int(threads * 60 / delay)} requests/minute" if delay > 0 else "MAX",
        "infinite": "YES - use /stop to stop"
    })

@app.route('/stop', methods=['GET', 'POST'])
def stop_spamming():
    target_uid = request.args.get('uid')
    if not target_uid:
        return jsonify({"error": "Missing 'uid' parameter"}), 400
    
    with sessions_lock:
        if target_uid not in active_sessions:
            return jsonify({"error": f"No active session found for UID: {target_uid}"}), 404
        
        stop_event = active_sessions[target_uid]["stop_event"]
        stats = active_sessions[target_uid]["stats"].copy()
        stop_event.set()
        del active_sessions[target_uid]
    
    time.sleep(0.5)
    
    return jsonify({
        "status": "stopped",
        "target_uid": target_uid,
        "final_stats": stats
    })

@app.route('/stop/all', methods=['GET', 'POST'])
def stop_all():
    with sessions_lock:
        if not active_sessions:
            return jsonify({"message": "No active sessions"}), 200
        
        for uid, data in list(active_sessions.items()):
            data["stop_event"].set()
        active_sessions.clear()
    
    return jsonify({"status": "stopped", "message": "All sessions stopped"})

@app.route('/status', methods=['GET'])
def get_status():
    with sessions_lock:
        sessions_info = []
        for uid, data in active_sessions.items():
            elapsed = (datetime.now() - datetime.fromisoformat(data["stats"]["start_time"])).total_seconds()
            rpm = round((data["stats"]["total"] / elapsed) * 60, 1) if elapsed > 0 else 0
            
            sessions_info.append({
                "target_uid": uid,
                "stats": data["stats"].copy(),
                "running_for_seconds": round(elapsed, 1),
                "current_rpm": rpm,
                "threads": data.get("threads", 1),
                "delay": data.get("delay", 0),
                "mode": data["stats"].get("mode", "UNKNOWN")
            })
    
    return jsonify({
        "active_sessions": sessions_info,
        "total_active": len(sessions_info)
    })

@app.route('/health', methods=['GET'])
def health():
    with sessions_lock:
        active_count = len(active_sessions)
    return jsonify({
        "status": "ok",
        "active_sessions": active_count,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/spam/single', methods=['GET'])
def spam_single():
    """طلب واحد من حساب محدد"""
    account_id = request.args.get('id')
    account_pass = request.args.get('pass')
    target_uid = request.args.get('target')
    
    if not account_id or not account_pass or not target_uid:
        return jsonify({"error": "Missing parameters. Required: id, pass, target"}), 400
    
    token = get_jwt_token(account_id, account_pass)
    if not token:
        return jsonify({"error": "Failed to get token for this account"}), 401
    
    for region_name, server_url in ALL_REGIONS:
        if send_friend_request(target_uid, token, server_url):
            return jsonify({
                "status": "success",
                "account_id": account_id,
                "target_uid": target_uid,
                "region_used": region_name
            })
    
    return jsonify({
        "status": "failed",
        "account_id": account_id,
        "target_uid": target_uid
    })

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║         ⚡ ULTRA FAST FREE FIRE SPAMMER ⚡                          ║
    ║                                                                      ║
    ║  ┌─────────────────────────────────────────────────────────────┐   ║
    ║  │  الوضع السريع (أقصى سرعة):                                   │   ║
    ║  │  /start/fast?uid=1879625250&threads=100                      │   ║
    ║  │  /start/fast?uid=1879625250&threads=200&delay=0              │   ║
    ║  └─────────────────────────────────────────────────────────────┘   ║
    ║                                                                      ║
    ║  ┌─────────────────────────────────────────────────────────────┐   ║
    ║  │  الوضع المتوازن (أقل ضغط):                                   │   ║
    ║  │  /start/balanced?uid=1879625250&threads=10&delay=0.5         │   ║
    ║  └─────────────────────────────────────────────────────────────┘   ║
    ║                                                                      ║
    ║  🛑 /stop?uid=1879625250     - إيقاف هدف                          ║
    ║  🔥 /stop/all                - إيقاف الكل                         ║
    ║  📊 /status                  - مراقبة السرعة                      ║
    ║                                                                      ║
    ║  ⚡ مع زيادة عدد الخيوط تزداد السرعة:                             ║
    ║     - 100 خيط → ~6000 طلب/دقيقة                                   ║
    ║     - 200 خيط → ~12000 طلب/دقيقة                                  ║
    ║     - 500 خيط → ~30000 طلب/دقيقة (يحتاج موارد قوية)               ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)
    app.run(host="0.0.0.0", port=20030, debug=False, threaded=True)