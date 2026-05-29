"""
今日头条 MCP 服务器安装配置文件
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="toutiao-mcp-server",
    version="1.0.0",
    author="TouTiao MCP Developer",
    author_email="developer@example.com",
    description="今日头条 MCP 服务器 - 支持内容发布和管理的 Model Context Protocol 服务器",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/toutiao-mcp-server",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastmcp>=2.3.0",
        "selenium>=4.0.0",
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.0",
        "Pillow>=8.0.0",
        "python-dateutil>=2.8.0",
        "pydantic>=1.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "black>=21.0.0",
            "flake8>=3.8.0",
            "mypy>=0.812",
        ],
    },
    entry_points={
        "console_scripts": [
            "toutiao-mcp-server=toutiao_mcp_server.__main__:main",
        ],
    },
)