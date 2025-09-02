#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏监控系统 Streamlit Dashboard 启动脚本

使用方法:
1. 安装依赖: pip install -r requirements_streamlit.txt
2. 运行脚本: python run_dashboard.py
3. 或直接运行: streamlit run streamlit_dashboard.py
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """检查必要的依赖是否已安装"""
    required_packages = ['streamlit', 'asyncio']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少以下依赖包: {', '.join(missing_packages)}")
        print("请运行以下命令安装依赖:")
        print("pip install -r requirements_streamlit.txt")
        return False
    
    return True

def main():
    """主函数"""
    print("🎮 游戏监控系统 Streamlit Dashboard 启动器")
    print("=" * 50)
    
    # 检查当前工作目录
    current_dir = Path.cwd()
    dashboard_file = current_dir / "streamlit_dashboard.py"
    
    if not dashboard_file.exists():
        print(f"❌ 找不到 streamlit_dashboard.py 文件")
        print(f"请确保在项目根目录 ({current_dir}) 下运行此脚本")
        return
    
    # 检查依赖
    print("🔍 检查依赖包...")
    if not check_dependencies():
        return
    
    print("✅ 依赖检查通过")
    print("🚀 启动 Streamlit Dashboard...")
    print("-" * 50)
    
    # 启动 Streamlit
    try:
        cmd = [sys.executable, "-m", "streamlit", "run", "streamlit_dashboard.py", "--server.port=8501"]
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
    except KeyboardInterrupt:
        print("\n👋 用户中断，正在退出...")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    main()