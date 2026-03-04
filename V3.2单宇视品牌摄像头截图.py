import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

# -------- 配置区域 --------
USERNAME = "admin"
PASSWORD = "摄像机密码"
INPUT_FILE = "UNVIPC.txt"
SAVE_DIR = "snapshots"
MAX_THREADS = 32
TIMEOUT = 30  # FFmpeg 单个摄像头截图超时时间（秒）
FFMPEG_PATH = "ffmpeg"  # 如果 ffmpeg.exe 不在 PATH 中，请写成 "C:/xxx/ffmpeg.exe"

# 海康默认主码流
RTSP_TEMPLATE = (
    "rtsp://{user}:{pwd}@{ip}/media/video0"
)
# --------------------------

os.makedirs(SAVE_DIR, exist_ok=True)

success_list = []
fail_list = []


# 读取 IP 列表
def load_ip_list(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


# FFmpeg 截图函数
def save_snapshot(ip):
    rtsp_url = RTSP_TEMPLATE.format(user=USERNAME, pwd=PASSWORD, ip=ip)
    output_path = f"{SAVE_DIR}/{ip}.jpg"

    cmd = [
        FFMPEG_PATH,
        "-rtsp_transport", "tcp",   # 强制 TCP，更稳定
        "-y",                       # 覆盖文件
        "-i", rtsp_url,             # 输入流
        "-frames:v", "1",           # 截取 1 帧
        "-q:v", "2",                # 图片质量（1-31，越小越清晰）
        output_path
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=TIMEOUT
        )
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True, ip
        else:
            return False, ip
    except subprocess.TimeoutExpired:
        return False, ip
    except Exception:
        return False, ip


def main():
    ip_list = load_ip_list(INPUT_FILE)
    print(f"共加载 {len(ip_list)} 个摄像头")

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_list = {executor.submit(save_snapshot, ip): ip for ip in ip_list}

        for future in as_completed(future_list):
            success, ip = future.result()

            if success:
                print(f"[√] {ip} 保存成功")
                success_list.append(ip)
            else:
                print(f"[×] {ip} 保存失败")
                fail_list.append(ip)

    # 输出结果文件
    with open("KEDAsuccessSecond.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(success_list))

    with open("KEDAfailSecond.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(fail_list))

    print("\n======== 执行完成 ========")
    print(f"成功: {len(success_list)} 台")
    print(f"失败: {len(fail_list)} 台")
    print(f"截图保存在: {SAVE_DIR}/")


if __name__ == "__main__":
    main()
