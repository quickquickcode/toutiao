"""
Markdown 解析器 - 将 Markdown 转换为今日头条支持的 HTML
"""

import re
from typing import Dict


def parse_markdown(md_content: str) -> Dict[str, str]:
    """
    解析 Markdown 文本，返回 title 和 html_content

    支持的格式：
    - # 标题 → <h1>
    - ## 副标题 → <h2>
    - **粗体** → <strong>
    - *斜体* → <em>
    - ![图片](url) → <img>
    - [链接](url) → <a>
    - 段落和换行
    """

    lines = md_content.split('\n')
    title = ""
    html_parts = []

    for line in lines:
        line = line.strip()

        # 空行
        if not line:
            html_parts.append('<p><br></p>')
            continue

        # 图片（行内，不能有其他内容）
        img_match = re.match(r'^!\[(.+?)\]\((.+?)\)$', line)
        if img_match:
            alt, url = img_match.groups()
            html_parts.append(f'<img src="{url}" alt="{alt}"/>')
            continue

        # 一级标题
        if line.startswith('# '):
            content = line[2:]
            title = title or content
            html_parts.append(f'<h1>{content}</h1>')
            continue

        # 二级标题
        if line.startswith('## '):
            html_parts.append(f'<h2>{line[3:]}</h2>')
            continue

        # 三级标题
        if line.startswith('### '):
            html_parts.append(f'<h3>{line[4:]}</h3>')
            continue

        # 无序列表
        if line.startswith('- ') or line.startswith('* '):
            html_parts.append(f'<li>{process_inline(line[2:])}</li>')
            continue

        # 有序列表
        ol_match = re.match(r'^\d+\.\s+(.+)$', line)
        if ol_match:
            html_parts.append(f'<li>{process_inline(ol_match.group(1))}</li>')
            continue

        # 引用
        if line.startswith('> '):
            html_parts.append(f'<blockquote>{process_inline(line[2:])}</blockquote>')
            continue

        # 代码块
        if line.startswith('```'):
            continue

        # 普通段落 - 处理行内样式
        html_parts.append(f'<p>{process_inline(line)}</p>')

    return {
        'title': title or '无标题',
        'html': ''.join(html_parts)
    }


def process_inline(text: str) -> str:
    """处理行内样式"""

    # 图片 ![alt](url) - 独立处理，不嵌套
    # 先处理粗体
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # 斜体
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # 删除线
    text = re.sub(r'~~(.+?)~~', r'<del>\1</del>', text)
    # 行内代码
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # 链接 [文字](url)
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)

    return text


def read_markdown_file(file_path: str) -> str:
    """读取 Markdown 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()
