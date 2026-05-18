# -*- coding: utf-8 -*-
"""
成都继续教育后台挂机脚本
通过模拟心跳请求实现后台学习
"""
import time
import requests

# ==================== 配置区 ====================
username = "qhliutingting"
password = "Zxc12345."
DEVICE_ID = "dcd9b57cb4f855cdaad6d10e6710e3e5"

TOKEN = "12fa1b83-0ca6-4e47-900e-21243fad5da1"
COOKIE = "UM_distinctid=19d3df98d8acd3-0a5220ad99373b8-26061b51-168000-19d3df98d8be22; CNZZDATA1779201=cnzz_eid%3D343077129-1774861258-%26ntime%3D1779099133"

# 心跳间隔（秒）
HEARTBEAT_INTERVAL = 30

# API 基础地址
BASE_URL = "https://www.cdsjxjy.cn/prod/stu/student/course"
# https://www.cdsjxjy.cn/cdcte/#/user/center

# ==================== 辅助函数 ====================
def format_duration(seconds):
    """格式化时长，显示秒和小时"""
    if not seconds:
        return "0 秒 (0.00 小时)"
    hours = seconds / 3600
    return f"{seconds} 秒 ({hours:.2f} 小时)"


import base64

from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

PUBLIC_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAjzJLqfPgAhr49ZNA4IqWdYIVE8riZsivkApdWJrSumXoytM7DlKIoifUZcT8+gE249kg2Pkgzfb19nVXtB8005JF8idXtADMqI5Cq9jQlwTxHxL1PRdkRFOULFdIvXOa70IRq70RQ6mKWTKQKm3SAOTK5vKAfV1edYEERCpHHiZGWDAb+6MXOFstL7Vx7a7CbSAffRQ8sPMNbxgvYZuaUqF4PuQlGwv8ziiQgZ1kf1LdG0FL1HRWZycOOKAtJH9TNR8f9eR6wtR+VuXz3u8iuAT0BwEwWJy8Ndf7J2yznhH5WFK8ETihGkp8HGZxJGqxAfvpCosvm0PYlrEiHo6ZtwIDAQAB"


def rsa_encrypt(text):
    key = RSA.import_key(base64.b64decode(PUBLIC_KEY))
    cipher = PKCS1_v1_5.new(key)
    encrypted = cipher.encrypt(text.encode())
    return base64.b64encode(encrypted).decode()


# ==================== 登录 ====================
def login():
    """登录获取 token 和 cookie"""
    global TOKEN, COOKIE

    print("[登录] 正在登录...")

    # 加密用户名和密码
    encrypted_username = rsa_encrypt(username)
    encrypted_password = rsa_encrypt(password)

    # 登录请求
    url = "https://www.cdsjxjy.cn/prod/stu/student/login"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    data = {
        "username": encrypted_username,
        "password": encrypted_password,
        "captcha": "",
        "validityPeriod": 7,
        "deviceId": DEVICE_ID
    }

    try:
        resp = requests.post(url, headers=headers, json=data)
        result = resp.json()

        if result.get("code") == 200:
            token = result.get("data", {}).get("token")
            if token:
                TOKEN = token
                # 从响应头获取 cookie
                set_cookie = resp.headers.get("Set-Cookie", "")
                if set_cookie:
                    COOKIE = set_cookie.split(";")[0]
                print(f"[登录] 成功! Token: {token[:20]}...")
                return True
        else:
            print(f"[登录] 失败: {result}")
    except Exception as e:
        print(f"[登录] 异常: {e}")

    return False


# ==================== 验证码处理 ====================
def send_captcha(sessionId, retry_count=0, max_retries=5):
    """处理验证码：先调用 heartbeat 获取 verifyCode，再调用 /verify"""
    if retry_count >= max_retries:
        print(f"[验证码] 重试次数过多 ({max_retries} 次)，返回")
        return None

    # 再次调用 heartbeat 获取 verifyCode
    result = api_request("POST", "/study/heartbeat", {"sessionId": sessionId})

    if result and result.get("code") == 200:
        study_data = result.get("data", {})
        verifyCode = study_data.get("verifyCode")

        if verifyCode:
            print(f"[验证码] 获取到验证码: {verifyCode}")
            # 调用 /verify 接口
            verify_result = api_request("POST", "/study/verify", data={
                "verifyCode": verifyCode,
                "sessionId": sessionId
            })

            # 如果验证失败，递归重试
            if verify_result and verify_result.get("code") == 500:
                print(f"[验证码] 验证失败，重试 {retry_count + 1}/{max_retries}...")
                return send_captcha(sessionId, retry_count + 1, max_retries)

            return verify_result

    return None


# ==================== API 请求 ====================
def get_headers():
    """获取请求头"""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    if TOKEN:
        headers["token"] = TOKEN
    return headers


def get_cookies():
    """获取 Cookies"""
    if COOKIE:
        return {"Cookie": COOKIE}
    return {}


def api_request(method, endpoint, data=None, silent=False):
    """发送 API 请求"""
    url = f"{BASE_URL}{endpoint}"
    headers = get_headers()

    try:
        if method.upper() == "GET":
            resp = requests.get(url, headers=headers, cookies=get_cookies())
        else:
            resp = requests.post(url, headers=headers, cookies=get_cookies(), json=data)

        if not silent:
            print(f"[请求] {method} {endpoint}")
            if data:
                print(f"[请求体] {data}")
            print(f"[响应] {resp.status_code}: {resp.text[:200]}")

        return resp.json()
    except Exception as e:
        print(f"[错误] 请求失败: {e}")
        return None


# ==================== 学习笔记 ====================
NOTE_CONTENT = "老师课堂逻辑清晰，知识点讲解细致，还会用案例互动，能带动学生思考，氛围活跃，学生参与度高 老师课堂逻辑清晰，知识点讲解细致，还会用案例互动，能带动学生思考，氛围活跃，学生参与度高"


def check_learning_record(selectId):
    """检查学习笔记是否存在"""
    url = f"https://www.cdsjxjy.cn/prod/stu/learning/record/get?id={selectId}"
    headers = get_headers()
    try:
        resp = requests.get(url, headers=headers, cookies=get_cookies())
        result = resp.json()
        return result.get("data") is not None
    except:
        return False


def submit_learning_record(selectId):
    """提交学习笔记"""
    url = "https://www.cdsjxjy.cn/prod/stu/learning/record"
    headers = get_headers()
    data = {
        "courseContent": NOTE_CONTENT,
        "feeling": NOTE_CONTENT,
        "selectId": selectId
    }
    try:
        resp = requests.post(url, headers=headers, cookies=get_cookies(), json=data)
        print(f"[学习笔记] 已提交")
    except Exception as e:
        print(f"[学习笔记] 提交失败: {e}")


# ==================== 课程接口 ====================
def get_course_list():
    """获取课程列表"""
    result = api_request("POST", "/page/selected", {"pageNum": 1, "pageSize": 50}, silent=True)
    if result and result.get("code") == 200:
        return result.get("data", {}).get("content", [])
    return []


def is_course_completed(course):
    """判断课程是否已完成：duration >= requiredTime 且 endStatus == 1"""
    duration = course.get("duration", 0) or 0
    required_time = course.get("requiredTime", 0) or 0
    end_status = course.get("endStatus", 0)
    return duration >= required_time and end_status == 1


def get_course_progress(course):
    """获取课程进度百分比"""
    duration = course.get("duration", 0) or 0
    required_time = course.get("requiredTime", 0) or 0
    if required_time == 0:
        return 0
    return duration * 100 / required_time


def sort_courses_by_progress(courses):
    """排序课程：排除已完成的，按进度降序（进度高的优先）"""
    # 排除已完成的课程
    incomplete = [c for c in courses if not is_course_completed(c)]
    # 按进度降序排序
    incomplete.sort(key=get_course_progress, reverse=True)
    return incomplete


def print_course_progress(courses):
    """打印课程进度概览"""
    print("\n=== 课程进度概览（按进度排序，优先学习接近完成的）===")
    
    completed_count = 0
    incomplete_count = 0
    
    for i, course in enumerate(courses):
        course_name = course.get("courseName", "未知课程")
        duration = course.get("duration", 0) or 0
        required_time = course.get("requiredTime", 0) or 0
        end_status = course.get("endStatus", 0)
        
        # 判断是否完成
        is_completed = duration >= required_time and end_status == 1
        
        if is_completed:
            completed_count += 1
        else:
            incomplete_count += 1
            progress = get_course_progress(course)
            # 截断课程名称，保持对齐
            display_name = course_name[:30].ljust(32) if len(course_name) > 30 else course_name.ljust(32)
            print(f"{incomplete_count}. {display_name} {duration:>5}/{required_time:<5} ({progress:>5.1f}%)")
    
    print(f"\n已完成: {completed_count} 门，未完成: {incomplete_count} 门")


def end_study(sessionId):
    """结束学习"""
    api_request("POST", "/study/end", {"sessionId": sessionId}, silent=True)


def start_study(selectId):
    """开始学习"""
    retry_count = 0
    max_retries = 5

    while retry_count < max_retries:
        result = api_request("POST", "/study/start", {"selectId": selectId})

        if result and result.get("code") == 200:
            study_data = result.get("data", {})

            # 如果有其他会话，先结束再重试
            if study_data.get("hasOther"):
                print(f"[开始学习] 检测到其他会话，先结束... (重试 {retry_count + 1}/{max_retries})")
                end_study(study_data["sessionId"])
                time.sleep(2)
                retry_count += 1
                continue

            print(f"[开始学习] 要求时长: {format_duration(study_data.get('requiredTime', 0))}")
            print(f"[开始学习] 已学时长: {format_duration(study_data.get('duration', 0))}")
            return study_data
        else:
            print(f"[开始学习] 失败: {result}")
            retry_count += 1
            time.sleep(1)

    # 超过重试次数，重新登录
    print("[开始学习] 重试次数过多，重新登录...")
    if login():
        # 重新登录成功，再尝试一次
        result = api_request("POST", "/study/start", {"selectId": selectId})
        if result and result.get("code") == 200:
            study_data = result.get("data", {})
            if not study_data.get("hasOther"):
                print(f"[开始学习] 要求时长: {format_duration(study_data.get('requiredTime', 0))}")
                print(f"[开始学习] 已学时长: {format_duration(study_data.get('duration', 0))}")
                return study_data

    print("[开始学习] 重新登录后仍然失败，跳过此课程")
    return None


def heartbeat(sessionId, required_time):
    """发送心跳"""
    data = {
        "sessionId": sessionId,
    }
    result = api_request("POST", "/study/heartbeat", data, silent=True)

    if result and result.get("code") == 200:
        study_data = result.get("data", {})
        duration = study_data.get("duration") or 0
        percent = duration * 100 // required_time if required_time else 0

        # 进度条显示（浮点数计算，避免低进度时为空）
        bar_len = 20
        filled = int(bar_len * duration / required_time) if required_time else 0
        bar = '█' * filled + '░' * (bar_len - filled)
        print(f"\r[进度条] {bar} {duration}/{required_time} ({percent}%)", end="", flush=True)

        # 检查是否需要验证码
        verifyCode = study_data.get("verifyCode")
        if verifyCode:
            print()  # 换行
            print("[心跳] 需要验证码验证")
            send_captcha(sessionId)

        return study_data
    else:
        print()  # 换行
        print(f"[心跳] 失败: {result}")
        return None


# ==================== 统计信息 ====================
def get_study_statistics():
    """获取学习统计信息"""
    # 课程统计
    stats = api_request("POST", "/page/datasts", {}, silent=True)
    # 学分
    credit = api_request("GET", "/getCredit", None, silent=True)

    if stats and stats.get("code") == 200:
        data = stats.get("data", {})
        data["credit"] = credit.get("data", {}).get("value", 0) if credit else 0
        return data
    return None


def print_statistics():
    """打印学习统计"""
    stats = get_study_statistics()
    if stats:
        total = stats.get("TotalCount", 0)
        finished = stats.get("EndCount", 0)
        unfinished = stats.get("NotEndCount", 0)
        credit = stats.get("credit", 0)

        print(f"正在学习 {total} 门 | 已完成 {finished} 门 | 未完成 {unfinished} 门")
        print(f"提醒: 视频学习最多获得20个学分, 当前已获得: {credit} 个学分")


# ==================== 主程序 ====================
def main():
    print("=" * 50)
    print("成都继续教育后台挂机脚本")
    print("=" * 50)

    # 登录
    if not login():
        print("[错误] 登录失败，使用默认值")


    # 获取课程列表
    courses = get_course_list()
    print(f"共 {len(courses)} 门课程")

    # 打印课程进度概览
    print_course_progress(courses)

    # 排序课程：排除已完成的，按进度降序
    sorted_courses = sort_courses_by_progress(courses)
    print(f"\n将学习 {len(sorted_courses)} 门未完成的课程")

    # 遍历每门课程
    for i, course in enumerate(sorted_courses):
        selectId = course["selectId"]
        print(f"\n=== 课程 {i + 1}/{len(sorted_courses)}: {course['courseName']} ===")

        # 检查学习笔记
        if check_learning_record(selectId):
            print("[学习笔记] 已存在")
        else:
            submit_learning_record(selectId)

        # 开始学习
        study_info = start_study(selectId)
        if not study_info:
            continue

        # 已完成则跳过
        if study_info.get("watchingFinished") and study_info.get("duration") == study_info.get("requiredTime"):
            print("已完成，跳过")
            continue

        sessionId = study_info["sessionId"]
        required_time = study_info.get("requiredTime", 0)

        # 心跳循环
        last_stats_time = time.time()
        # 打印统计
        print_statistics()
        while True:
            time.sleep(HEARTBEAT_INTERVAL)
            result = heartbeat(sessionId, required_time)
            if not result:
                print("[警告] 心跳失败，先结束当前会话...")
                end_study(sessionId)
                study_info = start_study(selectId)
                if not study_info:
                    break
                sessionId = study_info["sessionId"]
                required_time = study_info.get("requiredTime", 0)
                continue

            # 检查是否完成
            if result.get("watchingFinished") or result.get("creditObtained"):
                verify_info = start_study(selectId)
                if (verify_info and
                        verify_info.get("watchingFinished") == True and
                        verify_info.get("duration") == verify_info.get("requiredTime")):
                    print()  # 换行
                    print("[完成] 课程学习完成!")
                    break

            duration = result.get("duration") or 0
            if duration >= required_time:
                print()  # 换行
                print(f"[完成] 已达到要求时长: {duration}/{required_time}")
                break

    print("=" * 50)
    print("全部课程学习结束")


if __name__ == "__main__":
    main()
