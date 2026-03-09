#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import requests
from seleniumbase import SB

LOGIN_URL = "https://justrunmy.app/id/Account/Login"
DOMAIN    = "justrunmy.app"

# ============================================================
#  环境变量对接（仅修改此处名称，逻辑与原版一致）
# ============================================================
EMAIL        = os.environ.get("JUSTRUNMY_EMAIL")
PASSWORD     = os.environ.get("JUSTRUNMY_PASSWORD")
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID   = os.environ.get("TG_CHAT_ID")

if not EMAIL or not PASSWORD:
    print("❌ 致命错误：未找到 JUSTRUNMY_EMAIL 或 JUSTRUNMY_PASSWORD 环境变量！")
    sys.exit(1)

DYNAMIC_APP_NAME = "未知应用"

# ============================================================
#  Telegram 推送模块 (完全保留原版逻辑)
# ============================================================
def send_tg_message(status_icon, status_text, time_left):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("ℹ️ 未配置 TG 变量，跳过推送。")
        return

    local_time = time.gmtime(time.time() + 8 * 3600)
    current_time_str = time.strftime("%Y-%m-%d %H:%M:%S", local_time)

    message = (
        f"{status_icon} *JustRunMy 自动续期*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📧 *账号*: `{EMAIL[:3]}***`\n"
        f"📝 *状态*: {status_text}\n"
        f"⏱️ *剩余*: {time_left}\n"
        f"📅 *时间*: {current_time_str}\n"
        f"━━━━━━━━━━━━━━━"
    )
    
    payload = {"chat_id": TG_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage", json=payload, timeout=10)
    except Exception as e:
        print(f"❌ TG 发送失败: {e}")

# ============================================================
#  核心逻辑 (复刻自原版 justrunmy_renew.py)
# ============================================================
def handle_login(sb):
    print(f"🚀 访问登录页面: {LOGIN_URL}")
    sb.uc_open_with_reconnect(LOGIN_URL, reconnect_time=5)
    sb.sleep(5)
    
    # 处理 Cloudflare 验证 (关键一步)
    sb.uc_gui_handle_cf() 
    
    print("📧 填写登录凭据...")
    # 这里的选择器根据你提供的 error.png 修正为 Email 和 Password
    sb.wait_for_element('input[name="Email"]', timeout=15)
    sb.type('input[name="Email"]', EMAIL)
    sb.type('input[name="Password"]', PASSWORD)
    
    print("🖱️ 点击提交...")
    sb.click('button[type="submit"]')
    sb.sleep(8)
    
    # 再次尝试处理可能出现的二次 CF 验证
    sb.uc_gui_handle_cf()

def reset_timer_logic(sb):
    global DYNAMIC_APP_NAME
    print("🌐 正在进入控制面板...")
    sb.open("https://justrunmy.app/panel")
    sb.sleep(5)
    
    # 定位应用卡片
    print("🔍 查找应用卡片...")
    sb.wait_for_element('h3.font-semibold', timeout=20)
    DYNAMIC_APP_NAME = sb.get_text('h3.font-semibold')
    print(f"📦 发现应用: {DYNAMIC_APP_NAME}")
    
    sb.click('h3.font-semibold')
    sb.sleep(3)
    
    # 点击续期按钮
    print("⏱️ 点击 Reset Timer 按钮...")
    sb.wait_for_element('button:contains("Reset Timer")', timeout=10)
    sb.click('button:contains("Reset Timer")')
    sb.sleep(2)
    
    print("确认重置...")
    sb.click('button:contains("Just Reset")')
    sb.sleep(5)
    
    # 刷新验证结果
    sb.refresh()
    sb.sleep(5)
    timer_text = sb.get_text('span.font-mono.text-xl')
    return timer_text

def main():
    print(f"开始执行任务: {EMAIL[:3]}***")
    
    # 保持原版的 SB 配置
    with SB(uc=True, test=True, headless=False) as sb:
        try:
            handle_login(sb)
            
            # 简单判断是否登录成功
            if "Login" in sb.get_current_url():
                print("⚠️ 登录后仍停留页面，尝试直接跳转 Panel...")
                sb.open("https://justrunmy.app/panel")
                sb.sleep(5)

            timer_left = reset_timer_logic(sb)
            print(f"✅ 续期完成！剩余时间: {timer_left}")
            
            sb.save_screenshot("renew_success.png")
            send_tg_message("✅", "续期完成", timer_left)
            
        except Exception as e:
            print(f"💥 运行异常: {e}")
            sb.save_screenshot("error.png")
            send_tg_message("❌", "运行失败", "请查看 GitHub Actions 截图")

if __name__ == "__main__":
    main()
