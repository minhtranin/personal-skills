#!/usr/bin/env python3
"""
Convert Markdown text to Atlassian Document Format (ADF).
Supports: headings, tables, bullet lists, bold text, code blocks.

Usage:
  As module: from jira_adf import text_to_adf
  As script: echo "## Hello" | python3 jira_adf.py
"""

import json
import re
import sys


def parse_inline(text):
    """Parse bold (**text**) and code (`text`) into ADF inline nodes with marks."""
    nodes = []
    # Split on **bold** and `code` patterns
    parts = re.split(r'(\*\*.*?\*\*|`[^`]+`)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            nodes.append({
                'type': 'text',
                'text': part[2:-2],
                'marks': [{'type': 'strong'}]
            })
        elif part.startswith('`') and part.endswith('`'):
            nodes.append({
                'type': 'text',
                'text': part[1:-1],
                'marks': [{'type': 'code'}]
            })
        elif part:
            nodes.append({'type': 'text', 'text': part})
    return nodes or [{'type': 'text', 'text': ''}]


def _parse_table(lines, start):
    """Parse a markdown table starting at `start`. Returns (adf_node, next_index)."""
    header_line = lines[start].strip()
    separator = lines[start + 1].strip() if start + 1 < len(lines) else ''

    # Validate separator row
    if not re.match(r'^\|[\s|:\-]+\|$', separator):
        # Not a valid table, treat first line as paragraph
        return None, start + 1

    headers = [c.strip() for c in header_line.strip('|').split('|')]
    num_cols = len(headers)

    # Header row
    header_row = {
        'type': 'tableRow',
        'content': [
            {
                'type': 'tableHeader',
                'attrs': {'colspan': 1, 'rowspan': 1},
                'content': [{'type': 'paragraph', 'content': parse_inline(h)}]
            }
            for h in headers
        ]
    }

    # Data rows (skip header + separator)
    i = start + 2
    data_rows = []
    while i < len(lines) and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
        raw_cells = lines[i].strip().strip('|').split('|')
        cells = [c.strip() for c in raw_cells]
        while len(cells) < num_cols:
            cells.append('')
        cells = cells[:num_cols]

        row = {
            'type': 'tableRow',
            'content': [
                {
                    'type': 'tableCell',
                    'attrs': {'colspan': 1, 'rowspan': 1},
                    'content': [{'type': 'paragraph', 'content': parse_inline(c)}]
                }
                for c in cells
            ]
        }
        data_rows.append(row)
        i += 1

    table = {
        'type': 'table',
        'attrs': {'isNumberColumnEnabled': False, 'layout': 'default'},
        'content': [header_row] + data_rows
    }
    return table, i


def text_to_adf(text):
    """Convert markdown text to an ADF document."""
    if not text or not text.strip():
        return {'type': 'doc', 'version': 1, 'content': [
            {'type': 'paragraph', 'content': [{'type': 'text', 'text': ''}]}
        ]}

    content = []
    lines = text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip empty lines
        if not line.strip():
            i += 1
            continue

        # Heading: ## Heading
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            level = min(len(heading_match.group(1)), 6)
            heading_text = heading_match.group(2).strip()
            content.append({
                'type': 'heading',
                'attrs': {'level': level},
                'content': parse_inline(heading_text)
            })
            i += 1
            continue

        # Table: | header | header |
        if line.strip().startswith('|') and line.strip().endswith('|'):
            table_node, next_i = _parse_table(lines, i)
            if table_node:
                content.append(table_node)
                i = next_i
                continue

        # Bullet list: - item or * item
        if re.match(r'^[\-\*]\s+', line):
            items = []
            while i < len(lines) and re.match(r'^[\-\*]\s+', lines[i]):
                item_text = re.sub(r'^[\-\*]\s+', '', lines[i]).strip()
                items.append({
                    'type': 'listItem',
                    'content': [{'type': 'paragraph', 'content': parse_inline(item_text)}]
                })
                i += 1
            content.append({
                'type': 'bulletList',
                'content': items
            })
            continue

        # Ordered list: 1. item
        if re.match(r'^\d+\.\s+', line):
            items = []
            while i < len(lines) and re.match(r'^\d+\.\s+', lines[i]):
                item_text = re.sub(r'^\d+\.\s+', '', lines[i]).strip()
                items.append({
                    'type': 'listItem',
                    'content': [{'type': 'paragraph', 'content': parse_inline(item_text)}]
                })
                i += 1
            content.append({
                'type': 'orderedList',
                'content': items
            })
            continue

        # Horizontal rule: ---
        if re.match(r'^-{3,}$', line.strip()):
            content.append({'type': 'rule'})
            i += 1
            continue

        # Code block: ```lang ... ```
        if line.strip().startswith('```'):
            lang = line.strip()[3:].strip() or 'plain'
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1  # skip closing ```
            content.append({
                'type': 'codeBlock',
                'attrs': {'language': lang},
                'content': [{'type': 'text', 'text': '\n'.join(code_lines)}]
            })
            continue

        # Plain paragraph — collect consecutive non-special lines
        para_lines = []
        while i < len(lines):
            l = lines[i]
            if not l.strip():
                break
            if re.match(r'^#{1,6}\s', l):
                break
            if re.match(r'^[\-\*]\s+', l):
                break
            if re.match(r'^\d+\.\s+', l):
                break
            if l.strip().startswith('|') and l.strip().endswith('|'):
                break
            if l.strip().startswith('```'):
                break
            if re.match(r'^-{3,}$', l.strip()):
                break
            para_lines.append(l)
            i += 1

        if para_lines:
            para_text = ' '.join(para_lines)
            content.append({
                'type': 'paragraph',
                'content': parse_inline(para_text)
            })

    return {
        'type': 'doc',
        'version': 1,
        'content': content or [{'type': 'paragraph', 'content': [{'type': 'text', 'text': ''}]}]
    }


if __name__ == '__main__':
    md_text = sys.stdin.read()
    adf = text_to_adf(md_text)
    print(json.dumps(adf, ensure_ascii=False))
