import requests
import time
import random
import string
import base64
import json
from datetime import datetime
import threading
import urllib3
import concurrent.futures

# ================= 全局配置 =================
CHANNEL = "02"
APP_VER_NO = "3.1.6"
RUN_TIME = datetime(2025, 9, 9, 17, 00, 0, 300000)
RUN_COUNT = 1
TIME_SLEEP = 1
MAX_WORKERS = 1
REQUEST_TIMEOUT = 10
config_file = "./accounts.json"
STOP_FLAG = False  # 【核心】全局停止标志

# API端点
BASE_URL = 'https://app.hzgh.org.cn'
ENDPOINTS = {
    'login': '/unionApp/interf/front/U/U042',
    'signin': '/unionApp/interf/front/U/U042',
    'comment': '/unionApp/interf/front/AC/AC08',
    'query': '/unionApp/interf/front/U/U005',
    'exchange': '/unionApp/interf/front/OL/OL41'
}

# 密钥配置
ENCRYPTION_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC7yWoQaojBBqKI2H0j4e8ZeX/n1yip6hxrxSVth5F5n1JJ/B3liPMdz6K1chNLFTAcbI7hTL9KkphP9yQ+bPYD68Ajrt/DFrW679Zi1CoeetHVrM4sF68lYarGXwnSlKloaPWnI4Ch9cSqIvIOInlpeJqYPlJ8ZJvGCmbQoM6bewIDAQAB
-----END PUBLIC KEY-----"""

SIGNING_PRIVATE_KEY_PEM = """-----BEGIN PRIVATE KEY-----
MIICeAIBADANBgkqhkiG9w0BAQEFAASCAmIwggJeAgEAAoGBAJ+C8Z9awsGU8DeB
pq47p+pVBgIxWr9epYE5lTrVwoTvOv7dOBTsNgYPgDqFLbU8eZsV26DOvgd4TC5t
ZUWF7WbAleOcxvwA143XTBpZEeDx6who8KiW1WBKUwkeEfXZvOWhN2d+8GlCjvJu
2J4yNGEXScQEIWb+ofE4Pd4yPkkzAgMBAAECgYB0Tzu18a0vEFX0c1JBm3g98w81
jB1aiz3tMzqwMuvqmLIQ4uegwfhGhQkAItoIW/dj8RU7dWS096+87sG4ZwaKCv/S
mT1CibqmSATrX6YNIFU4uXsZzMREJxmZi+V5AllT9DWBG5YjKgrGfWjL0Rq10Zvx
YMTdjO+SbqDIjVoc+QJBAOrMXRO6G349NpLvo1QPevxIykKNKhr5Qkjv4oVydoVo
HW6iMU30PhrBqBYla+K8W+xyeqrjd9ucDQFW/Z2+hD8CQQCt6jz4o7qadQM0giko
BsgWwp7teyZI/8ZH5htrKZwDJzUe6LuM9xjDeXAqqjNjQrDL7M+6T7ZwMmK3UN3b
oe4NAkEA6ioGabYh1TSXSNNVwG/v58twbA78/wm34aXb89rD+Shssflv0p7TkTuxt
uR7RBU2WAmT7PoOfyaSkdN/++IVYQJBAJ/klCvQc/YfkFPNO0N2gK0UP4N8zmUc
6tIdh6XNeocXm+oP9KaUYusMkghXtKkUnnDOBul28fdTC5kYOvD7fl0CQQDLIYfo
8MSMgcFkBH1wRUbhjVv31bk8+4G9a+h7UkLdLtch5qPsS7bsFCyszqEYjhYtQ278
Q20lSzaIsom0Q3ai
-----END PRIVATE KEY-----"""

SIGN_KEY_NEW = "zSw3MLRV7VuwT!*G"
ENCRYPT_KEYS = ["login_name", "user_id"]
NO_SIGN_KEYS = ["answerContent", "surveyId", "content", "preContent", "img", "img1", "img2", "package", "codeUrl", "belong", "verCode"]

# 解密密钥
PRIVATE_KEY_PEM = """-----BEGIN RSA PRIVATE KEY-----
MIICdQIBADANBgkqhkiG9w0BAQEFAASCAl8wggJbAgEAAoGBAIOBMtf2AIYQlrNy
/lVPHx4R/LKI+Vtk3bKmzID8vdVnh/4WA3lczqfejM10Xfy3sNe4l5EeQTvnDgUH
bIFK8FyJRpvypAmS9oyW6uwGTjZEu5Y6hsSxiGAOG5ZOlH8vOSfuaAkZ+iUlqifP
E3ZOmHkqGzmukg4wCRaPLx5ioq8zAgMBAAECgYAgLOVmx677HmXxBCrMbq57agU9
HZx9SyGfS4Zv7Ob5pvo0Jei1sgpyMlabEmTIp50iOu0CubdWU8MvYdCfldlXQLW7
cjk8N1NyGQLFd2fJ03a7gGWnwwEdPoNTpSHnB+mDL9l7MVjion5fLojzq9Pz1gMK
L01I2TfZBDL4m6EbgQJBAMfgrMKtj7f40GA3qp/y/9/eBCAu8PbtFmtATLMQRf4t
Ghjvn349x1b6FZj8RiaRBSrq0Owjrdo5TUxgfS7dz3MCQQCobdWk2SQhRlqEHfFE
ro/8ab6gn3GhBDzzKvNjhKr2MO6JWqs+Vr+/P9uYpA+G+rv74uVIGWhjuNtI5+/6
9DFBAkAJOQS/tuJ6yrBSwD7PQpcr7UKjeYcE3cu7ByyC1q1kHRCnNedWG+Omz8NP
W9Sg0vA6GrupKbxL5Xj7nTgpgXKhAkBIVlvioAvfaqrngUClAd//RZ9EtxYDVKGk
wnaj8E/Iyr04KsPPU0ypJBD5XsT4cOmZxho5PAhUhAlSJ6MvAf/BAkA64ieVhtQA
1KV0pSSEJMnbPlZe+yBYGTWLMaG2zL0kKEhIs2fIHbVhLFQ8TkO5oH+mhxuuXI5+
nVU2G0dqUl6D
-----END RSA PRIVATE KEY-----"""

# ================= 超级兼容导入模块 =================
def import_crypto_modules():
    modules = {}
    try:
        from Crypto.PublicKey import RSA
        from Crypto.Signature import pkcs1_15
        from Crypto.Hash import SHA256
        from Crypto.Cipher import DES3, PKCS1_v1_5
        from Crypto.Util.Padding import pad, unpad
        modules['RSA'] = RSA
        modules['pkcs1_15'] = pkcs1_15
        modules['SHA256'] = SHA256
        modules['DES3'] = DES3
        modules['PKCS1_v1_5'] = PKCS1_v1_5
        modules['pad'] = pad
        modules['unpad'] = unpad
        return modules
    except ImportError:
        pass

    try:
        from Cryptodome.PublicKey import RSA
        from Cryptodome.Signature import pkcs1_15
        from Cryptodome.Hash import SHA256
        from Cryptodome.Cipher import DES3, PKCS1_v1_5
        from Cryptodome.Util.Padding import pad, unpad
        modules['RSA'] = RSA
        modules['pkcs1_15'] = pkcs1_15
        modules['SHA256'] = SHA256
        modules['DES3'] = DES3
        modules['PKCS1_v1_5'] = PKCS1_v1_5
        modules['pad'] = pad
        modules['unpad'] = unpad
        return modules
    except ImportError:
        pass

    print("❌ 错误：找不到加密库！")
    print("请安装：python -m pip install pycryptodome")
    input("按回车退出...")
    exit()

crypto = import_crypto_modules()
RSA = crypto['RSA']
pkcs1_15 = crypto['pkcs1_15']
SHA256 = crypto['SHA256']
DES3 = crypto['DES3']
PKCS1_v1_5 = crypto['PKCS1_v1_5']
pad = crypto['pad']
unpad = crypto['unpad']
_DES3 = DES3

# 清除警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================= 工具函数 =================
def rand_str(n):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(n))

def rsa_encrypt(pub_pem, s):
    try:
        rsakey = RSA.importKey(pub_pem)
        cipher = PKCS1_v1_5.new(rsakey)
        return base64.b64encode(cipher.encrypt(s.encode('utf-8'))).decode('utf-8')
    except Exception as e:
        raise Exception(f"RSA加密失败: {e}")

def des3_ecb_pkcs7_encrypt(key24, plaintext):
    try:
        key_bytes = key24.encode('utf-8')
        cipher = DES3.new(key_bytes, DES3.MODE_ECB)
        padded_data = pad(plaintext.encode('utf-8'), DES3.block_size, style='pkcs7')
        encrypted = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted).decode('utf-8')
    except Exception as e:
        raise Exception(f"3DES加密失败: {e}")

def rsa_sha256_sign(private_key_pem, data_string):
    try:
        key = RSA.import_key(private_key_pem)
        h = SHA256.new(data_string.encode('utf-8'))
        signature = pkcs1_15.new(key).sign(h)
        return base64.b64encode(signature).decode('utf-8')
    except Exception as e:
        raise Exception(f"RSA签名失败: {e}")

def decrypt_data2(data2):
    try:
        rsa_enc = data2[:172]
        des_enc = data2[172:]
        rsa_enc_bytes = base64.b64decode(rsa_enc)
        des_enc_bytes = base64.b64decode(des_enc)

        rsakey = RSA.importKey(PRIVATE_KEY_PEM)
        cipher_rsa = PKCS1_v1_5.new(rsakey)
        a_bytes = cipher_rsa.decrypt(rsa_enc_bytes, None)
        a = a_bytes.decode()

        key = ("HTt0Hzsu" + a).encode()
        iv = a[:8].encode()

        cipher_des3 = DES3.new(key, DES3.MODE_CBC, iv)
        decrypted = cipher_des3.decrypt(des_enc_bytes)
        decrypted = unpad(decrypted, DES3.block_size, style='pkcs7')
        return decrypted.decode()
    except Exception as e:
        raise Exception(f"解密失败: {e}")

def build_payload(account, custom_params=None):
    try:
        payload = {
            "channel": CHANNEL,
            "app_ver_no": APP_VER_NO,
            "timestamp": int(time.time() * 1000),
            "login_name": account["login_name"],
            "user_id": account["user_id"],
            "ses_id": account["ses_id"],
            "exchange_id": account["exchange_id"]
        }

        if custom_params:
            payload.update(custom_params)

        filtered_payload = {}
        for key, value in payload.items():
            if value is not None and value != "":
                filtered_payload[key] = value
            elif isinstance(value, (int, float)) and value == 0:
                filtered_payload[key] = value
        payload = filtered_payload

        m = rand_str(24).upper()
        dec_key = rsa_encrypt(ENCRYPTION_PUBLIC_KEY_PEM, m)
        payload["dec_key"] = dec_key

        for key in ENCRYPT_KEYS:
            if key in payload:
                payload[key] = des3_ecb_pkcs7_encrypt(m, str(payload[key]))

        payload_for_signing = payload.copy()
        for key in NO_SIGN_KEYS:
            if key in payload_for_signing:
                del payload_for_signing[key]

        keys_for_sign = list(payload_for_signing.keys())
        values_for_sign = [str(v) for v in payload_for_signing.values()]
        values_concat = "".join(values_for_sign)
        string_to_sign = values_concat + SIGN_KEY_NEW
        sign = rsa_sha256_sign(SIGNING_PRIVATE_KEY_PEM, string_to_sign)

        payload["key"] = ",".join(keys_for_sign)
        payload["sign"] = sign
        return payload
    except Exception as e:
        raise Exception(f"构建请求体失败: {e}")

def create_account_session():
    session = requests.Session()
    headers = {
        "Host": "app.hzgh.org.cn",
        "Connection": "keep-alive",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Linux; Android 9; SKW-A0 Build/PQ3A.190705.08061357; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36;unionApp;HZGH",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://app.hzgh.org.cn:8123",
        "X-Requested-With": "com.zjte.hanggongefamily",
        "Referer": "https://app.hzgh.org.cn:8123/",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    session.headers.update(headers)
    session.verify = False
    return session

# ================= 单账号任务 =================
def run_exchange(account):
    global STOP_FLAG
    session = create_account_session()
    account_id = account["login_name"][:8]
    try:
        for i in range(RUN_COUNT):
            if STOP_FLAG:
                print(f"[{account_id}] 收到停止信号")
                break
            try:
                payload = build_payload(account)
                resp = session.post(
                    BASE_URL + ENDPOINTS['exchange'],
                    json=payload,
                    timeout=REQUEST_TIMEOUT
                )
                resp_json = resp.json()
                if "data2" in resp_json:
                    decrypted = decrypt_data2(resp_json["data2"])
                    print(f"[{account_id}] 第{i+1}次兑换: {decrypted}")
                else:
                    print(f"[{account_id}] 第{i+1}次兑换: {resp_json}")
                time.sleep(TIME_SLEEP)
            except Exception as e:
                print(f"[{account_id}] 第{i+1}次兑换失败: {e}")
                continue
    except Exception as e:
        print(f"[{account_id}] 兑换任务异常: {e}")
    finally:
        session.close()

def daily_task_workflow(account):
    session = create_account_session()
    account_id = account["login_name"][:8]
    print(f"\n🎯 [{account_id}] 开始执行每日任务")
    try:
        print(f"[{account_id}] 执行登录...")
        payload = build_payload(account, {"type": "1"})
        resp = session.post(BASE_URL + ENDPOINTS['login'], json=payload, timeout=REQUEST_TIMEOUT)
        resp_json = resp.json()
        decrypted = decrypt_data2(resp_json["data2"]) if "data2" in resp_json else str(resp_json)
        print(f"[{account_id}] 登录结果: {decrypted}")
        time.sleep(1)

        for i in range(1, 4):
            try:
                print(f"[{account_id}] 第{i}次签到...")
                payload = build_payload(account, {"type": "5"})
                resp = session.post(BASE_URL + ENDPOINTS['signin'], json=payload, timeout=REQUEST_TIMEOUT)
                resp_json = resp.json()
                decrypted = decrypt_data2(resp_json["data2"]) if "data2" in resp_json else str(resp_json)
                print(f"[{account_id}] 第{i}次签到结果: {decrypted}")
                time.sleep(1)
            except Exception as e:
                print(f"[{account_id}] 第{i}次签到失败: {e}")
                continue

        print(f"[{account_id}] 执行评论...")
        payload = build_payload(account, {
            "related_id": "1232",
            "content_type": "1",
            "oper_type": "0",
            "suffix": "png",
            "content": "好"
        })
        resp = session.post(BASE_URL + ENDPOINTS['comment'], json=payload, timeout=REQUEST_TIMEOUT)
        resp_json = resp.json()
        decrypted = decrypt_data2(resp_json["data2"]) if "data2" in resp_json else str(resp_json)
        print(f"[{account_id}] 评论结果: {decrypted}")
        time.sleep(1)

        print(f"[{account_id}] 查询积分...")
        payload = build_payload(account)
        resp = session.post(BASE_URL + ENDPOINTS['query'], json=payload, timeout=REQUEST_TIMEOUT)
        resp_json = resp.json()
        decrypted = decrypt_data2(resp_json["data2"]) if "data2" in resp_json else str(resp_json)
        print(f"[{account_id}] 积分查询结果: {decrypted}")

        print(f"🎉 [{account_id}] 每日任务完成\n")
    except Exception as e:
        print(f"❌ [{account_id}] 每日任务失败: {e}")
    finally:
        session.close()

# ================= 多账号调度 =================
def load_accounts():
    global config_file
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            accounts = json.load(f)
        print(f"✅ 成功加载 {len(accounts)} 个账号")
        return accounts
    except FileNotFoundError:
        print(f"❌ 未找到账号文件: {config_file}")
        return []
    except json.JSONDecodeError:
        print("❌ 账号文件格式错误")
        return []

def wait_until_target():
    global STOP_FLAG
    print(f"⏳ 等待到目标时间: {RUN_TIME}")
    while True:
        if STOP_FLAG:
            print("⏹️ 取消等待")
            return
            
        now = datetime.now()
        if now >= RUN_TIME:
            break
        diff = (RUN_TIME - now).total_seconds()
        
        if diff > 3600:
            sleep_time = 300
        elif diff > 600:
            sleep_time = 60
        elif diff > 60:
            sleep_time = 30
        elif diff > 1:
            sleep_time = 0.5
        else:
            sleep_time = 0.05
            
        # 分段睡眠，频繁检查停止
        check_interval = 0.5
        slept = 0
        while slept < sleep_time and not STOP_FLAG:
            time.sleep(min(check_interval, sleep_time - slept))
            slept += check_interval
            
        if STOP_FLAG:
            return
            
        print(f"⏳ 剩余 {diff:.2f} 秒")

def run_multi_account_exchange():
    global STOP_FLAG
    STOP_FLAG = False
    
    accounts = load_accounts()
    if not accounts:
        return
        
    wait_until_target()
    
    if STOP_FLAG:
        print("⏹️ 任务已取消")
        return

    print("\n🚀 开始多账号兑换任务")
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(run_exchange, account) for account in accounts]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"❌ 某个账号异常: {e}")
    print("\n🏁 所有账号兑换任务完成")

def run_multi_account_daily_task():
    global STOP_FLAG
    STOP_FLAG = False
    
    accounts = load_accounts()
    if not accounts:
        return
        
    print("\n🚀 开始多账号每日任务")
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(daily_task_workflow, account) for account in accounts]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"❌ 某个账号每日任务异常: {e}")
    print("\n🏁 所有账号每日任务完成")

# ================= 主函数 =================
if __name__ == "__main__":
    task_choice = input("请选择任务类型（1=每日任务 2=兑换任务）：")
    if task_choice == "1":
        run_multi_account_daily_task()
    elif task_choice == "2":
        run_multi_account_exchange()
    else:
        print("❌ 无效选择")
