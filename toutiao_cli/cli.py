#!/usr/bin/env python3
"""
今日头条 CLI 工具
"""

import sys
from pathlib import Path

import typer
from typing import Optional, List

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from toutiao_cli import TouTiaoAuth, TouTiaoPublisher, parse_markdown, read_markdown_file

app = typer.Typer(help="今日头条 CLI 工具")

# 子命令组
auth_group = typer.Typer(help="认证管理")
article_group = typer.Typer(help="文章管理")
micro_group = typer.Typer(help="微头条")

app.add_typer(auth_group, name="auth")
app.add_typer(article_group, name="article")
app.add_typer(micro_group, name="micro")


# ==================== Auth 命令 ====================

@auth_group.command("login")
def auth_login():
    """扫码登录"""
    auth = TouTiaoAuth()
    if auth.login():
        typer.secho("登录成功！", fg=typer.colors.GREEN)
    else:
        typer.secho("登录失败", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)


@auth_group.command("status")
def auth_status():
    """检查登录状态"""
    auth = TouTiaoAuth()
    if auth.check_status():
        typer.secho("已登录", fg=typer.colors.GREEN)
    else:
        typer.secho("未登录", fg=typer.colors.YELLOW)
        raise typer.Exit(1)


# ==================== Article 命令 ====================

@article_group.command("publish")
def article_publish(
    file: str = typer.Argument(..., help="Markdown 文件路径"),
):
    """
    发布文章（从 Markdown 文件）

    示例: python3 cli.py article publish articles/example.md
    """
    # 读取并解析 Markdown
    try:
        md_content = read_markdown_file(file)
    except FileNotFoundError:
        typer.secho(f"文件不存在: {file}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"读取文件失败: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    parsed = parse_markdown(md_content)

    typer.echo(f"标题: {parsed['title']}")
    typer.echo("正在打开发布页面...")

    # 发布
    auth = TouTiaoAuth()
    if not auth.check_status():
        typer.secho("请先登录: python3 cli.py auth login", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    publisher = TouTiaoPublisher(auth)
    result = publisher.publish_article(
        title=parsed['title'],
        html_content=parsed['html'],
    )

    if result.get('success'):
        typer.secho("发布准备完成，请在浏览器中手动点击发布按钮", fg=typer.colors.GREEN)
    else:
        typer.secho(f"发布失败: {result.get('message')}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)


@article_group.command("preview")
def article_preview(
    file: str = typer.Argument(..., help="Markdown 文件路径"),
):
    """
    预览 Markdown 解析结果

    示例: python3 cli.py article preview articles/example.md
    """
    try:
        md_content = read_markdown_file(file)
    except FileNotFoundError:
        typer.secho(f"文件不存在: {file}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    parsed = parse_markdown(md_content)

    typer.echo(f"\n{'='*50}")
    typer.secho(f"标题: {parsed['title']}", fg=typer.colors.CYAN)
    typer.echo(f"{'='*50}\n")
    typer.echo("HTML 内容:")
    typer.echo(parsed['html'])


# ==================== Micro 命令 ====================

@micro_group.command("publish")
def micro_publish(
    content: str = typer.Argument(None, help="微头条内容（可使用 Markdown）"),
    file: Optional[str] = typer.Option(None, "-f", "--file", help="从 Markdown 文件读取内容"),
    images: Optional[str] = typer.Option(None, "-i", "--images", help="图片路径（逗号分隔，最多9张）"),
    topic: Optional[str] = typer.Option(None, "-t", "--topic", help="话题标签"),
):
    """
    发布微头条

    示例: python3 cli.py micro publish "这是微头条内容"
    示例: python3 cli.py micro publish "内容" --topic "科技" -i "a.jpg,b.jpg"
    示例: python3 cli.py micro publish -f articles/example.md
    """
    # 检查登录
    auth = TouTiaoAuth()
    if not auth.check_status():
        typer.secho("请先登录: python3 cli.py auth login", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # 如果提供了文件，从文件读取
    html_content = None
    if file:
        try:
            md_content = read_markdown_file(file)
            parsed = parse_markdown(md_content)
            # 标题作为第一行，保留 Markdown 格式
            html_content = parsed['html']
            typer.echo(f"标题: {parsed['title']}")
            # 如果没有提供 content 且有标题，用标题作为话题
            if not content and parsed['title']:
                content = parsed['title']
        except FileNotFoundError:
            typer.secho(f"文件不存在: {file}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)
        except Exception as e:
            typer.secho(f"读取文件失败: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)
    elif not content:
        typer.secho("请提供内容或使用 -f 指定文件", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # 解析图片列表
    image_list = None
    if images:
        image_list = [img.strip() for img in images.split(',') if img.strip()]

    typer.echo("正在打开发布页面...")

    publisher = TouTiaoPublisher(auth)
    result = publisher.publish_micro(
        content=content or "",
        html_content=html_content,
        images=image_list,
        topic=topic,
    )

    if result.get('success'):
        typer.secho("发布准备完成，请在浏览器中手动点击发布按钮", fg=typer.colors.GREEN)
    else:
        typer.secho(f"发布失败: {result.get('message')}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)


@micro_group.command("debug-page")
def micro_debug_page():
    """打开微头条发布页，输出 Playwright 看到的发布按钮诊断信息。"""
    auth = TouTiaoAuth()
    publisher = TouTiaoPublisher(auth)
    result = publisher.debug_micro_page()
    typer.echo(result)
    if not result.get("ok") or not result.get("hasPublishText"):
        raise typer.Exit(1)


# ==================== 主入口 ====================

@app.command()
def main():
    """今日头条 CLI 工具"""
    pass


if __name__ == "__main__":
    app()
