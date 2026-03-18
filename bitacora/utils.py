import json
import re

from django.utils import timezone


def extract_structured_content(html_content):
    if not html_content:
        return None

    structured_blocks = []
    cleaned_html = html_content

    pattern = (
        r'<div[^>]*class="[^"]*content-block[^"]*"[^>]*'
        r'data-block-id="([^"]*)"[^>]*data-block-type="([^"]*)"[^>]*>.*?</div>'
    )
    matches = re.findall(pattern, cleaned_html, re.DOTALL | re.IGNORECASE)

    for block_id, block_type in matches:
        block_pattern = f'<div[^>]*data-block-id="{re.escape(block_id)}"[^>]*>(.*?)</div>'
        block_match = re.search(block_pattern, cleaned_html, re.DOTALL | re.IGNORECASE)

        if block_match:
            block_html = block_match.group(0)
            title_match = re.search(
                r'<h[1-6][^>]*>(.*?)</h[1-6]>', block_html,
                re.DOTALL | re.IGNORECASE,
            )
            title = title_match.group(1).strip() if title_match else f'Bloque {block_type}'
            content_start = block_html.find('</h5>')
            if content_start == -1:
                content_start = block_html.find('</h6>')
            content_html = (
                block_html[content_start + len('</h5>'):].strip()
                if content_start != -1 else block_html
            )
            structured_blocks.append({
                'id':           block_id,
                'type':         block_type,
                'title':        title,
                'content':      content_html,
                'content_type': block_type,
                'inserted_at':  timezone.now().isoformat(),
            })
            cleaned_html = cleaned_html.replace(block_html, '')

    json_pattern = r'\[{.*?}\]'
    for json_str in re.findall(json_pattern, cleaned_html, re.DOTALL):
        try:
            data = json.loads(json_str)
            if isinstance(data, list):
                structured_blocks.extend(data)
                cleaned_html = cleaned_html.replace(json_str, '')
        except json.JSONDecodeError:
            pass

    return structured_blocks if structured_blocks else None
