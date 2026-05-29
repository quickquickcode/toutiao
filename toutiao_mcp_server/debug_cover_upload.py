#!/usr/bin/env python3
"""
调试封面图片上传功能的专用脚本
"""

import sys
import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_cover_upload():
    """调试封面上传区域"""
    try:
        from toutiao_mcp_server.auth import TouTiaoAuth
        from toutiao_mcp_server.publisher import TouTiaoPublisher
        
        # 初始化
        auth = TouTiaoAuth()
        if not auth.check_login_status():
            logger.error("未登录")
            return
        
        publisher = TouTiaoPublisher(auth)
        driver = publisher._setup_driver()
        publisher._transfer_cookies_to_driver(driver)
        
        # 打开发布页面
        logger.info("打开发布页面...")
        driver.get("https://mp.toutiao.com/profile_v4/graphic/publish")
        time.sleep(5)
        
        # 输入标题和内容，让页面进入完整状态
        logger.info("输入基本内容...")
        
        # 标题
        title_textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[placeholder*='请输入文章标题']"))
        )
        driver.execute_script("arguments[0].value = '调试测试标题';", title_textarea)
        
        # 内容
        content_editor = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ProseMirror"))
        )
        driver.execute_script("arguments[0].innerHTML = '<p>调试测试内容</p>';", content_editor)
        
        time.sleep(3)
        
        # 开始调试封面上传区域
        logger.info("开始调试封面上传区域...")
        
        # 查找所有可能的上传相关元素
        print("\n=== 查找所有可能的上传元素 ===")
        
        # 1. 查找所有包含"upload"的元素
        upload_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'upload')]")
        print(f"找到 {len(upload_elements)} 个包含'upload'的元素")
        for i, elem in enumerate(upload_elements[:5]):
            try:
                print(f"  {i+1}. 类名: {elem.get_attribute('class')}, 标签: {elem.tag_name}, 可见: {elem.is_displayed()}")
            except:
                print(f"  {i+1}. 无法获取信息")
        
        # 2. 查找所有文件输入框
        file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        print(f"\n找到 {len(file_inputs)} 个文件输入框")
        for i, inp in enumerate(file_inputs):
            try:
                accept = inp.get_attribute('accept') or '无accept属性'
                print(f"  {i+1}. accept: {accept}, 可见: {inp.is_displayed()}")
            except:
                print(f"  {i+1}. 无法获取信息")
        
        # 3. 查找包含"+"的元素
        plus_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '+')]")
        print(f"\n找到 {len(plus_elements)} 个包含'+'的元素")
        for i, elem in enumerate(plus_elements[:5]):
            try:
                print(f"  {i+1}. 文本: '{elem.text}', 标签: {elem.tag_name}, 可见: {elem.is_displayed()}")
            except:
                print(f"  {i+1}. 无法获取信息")
        
        # 4. 查找包含"预览"的元素
        preview_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '预览')]")
        print(f"\n找到 {len(preview_elements)} 个包含'预览'的元素")
        for i, elem in enumerate(preview_elements):
            try:
                print(f"  {i+1}. 文本: '{elem.text}', 标签: {elem.tag_name}, 可见: {elem.is_displayed()}")
                # 尝试找到父级容器
                parent = elem.find_element(By.XPATH, "./..")
                print(f"     父级: {parent.tag_name}, 类名: {parent.get_attribute('class')}")
            except:
                print(f"  {i+1}. 无法获取信息")
        
        print("\n=== 调试完成，浏览器将保持开启30秒供手动检查 ===")
        time.sleep(30)
        
    except Exception as e:
        logger.error(f"调试失败: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    debug_cover_upload()