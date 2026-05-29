#!/usr/bin/env python3
"""
今日头条发布功能一键测试脚本
"""

import sys
import os
import subprocess

def main():
    print("=" * 60)
    print("🚀 今日头条自动发布功能测试")
    print("=" * 60)
    print()
    
    print("请选择测试类型:")
    print("1. 简化测试 (推荐)")
    print("2. 完整测试")
    print("3. 退出")
    print()
    
    choice = input("请输入选择 (1-3): ").strip()
    
    if choice == "1":
        print("\n🚀 启动简化测试...")
        subprocess.run([sys.executable, "test_simple_publish_final.py"])
    elif choice == "2":
        print("\n🚀 启动完整测试...")
        subprocess.run([sys.executable, "test_optimized_publish.py"])
    elif choice == "3":
        print("\n👋 退出测试")
        return
    else:
        print("\n❌ 无效选择，退出")
        return

if __name__ == "__main__":
    main()