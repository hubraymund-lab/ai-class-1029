"""노션 페이지 → 웹 교안 본문(lesson.html).

GitHub Actions에서 돌립니다. 환경변수:
  NOTION_TOKEN    노션 연동(인티그레이션) 비밀 키
  NOTION_PAGE_ID  교안 페이지 ID (주소 끝 32자리)
노션 이미지 주소는 한 시간쯤 뒤 만료되므로, 이미지는 내려받아 site/assets/ 에 넣습니다.
"""
import html, json, os, re, sys, hashlib, urllib.request

TOKEN = os.environ['NOTION_TOKEN']
PAGE = re.sub(r'[^0-9a-f]', '', os.environ['NOTION_PAGE_ID'].lower())[-32:]
OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else 'site'
os.makedirs(f'{OUT_DIR}/assets', exist_ok=True)


def api(path):
    req = urllib.request.Request('https://api.notion.com/v1/' + path,
                                 headers={'Authorization': f'Bearer {TOKEN}', 'Notion-Version': '2022-06-28'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def children(block_id):
    out, cursor = [], None
    while True:
        q = f'blocks/{block_id}/children?page_size=100' + (f'&start_cursor={cursor}' if cursor else '')
        d = api(q)
        out += d['results']
        if not d.get('has_more'):
            return out
        cursor = d['next_cursor']


COLORS = {'gray', 'brown', 'orange', 'yellow', 'green', 'blue', 'purple', 'pink', 'red'}


def color_class(c):
    base = (c or 'default').replace('_background', '')
    return base if base in COLORS else ''


def rich(rts):
    s = ''
    for rt in rts or []:
        t = html.escape(rt.get('plain_text', '')).replace('\n', '<br>')
        a = rt.get('annotations', {})
        if a.get('code'): t = f'<code>{t}</code>'
        if a.get('bold'): t = f'<b>{t}</b>'
        if a.get('italic'): t = f'<i>{t}</i>'
        if a.get('strikethrough'): t = f'<s>{t}</s>'
        if a.get('underline'): t = f'<u>{t}</u>'
        cc = a.get('color', 'default')
        if cc and cc != 'default':
            t = f'<span class="{"bg-" if cc.endswith("_background") else ""}{color_class(cc)}">{t}</span>'
        href = rt.get('href')
        if href and href.startswith(('http://', 'https://')):
            t = f'<a href="{html.escape(href)}">{t}</a>'
        s += t
    return s


def save_image(url):
    name = hashlib.sha1(url.split('?')[0].encode()).hexdigest()[:16]
    ext = os.path.splitext(url.split('?')[0])[1][:5] or '.png'
    path = f'{OUT_DIR}/assets/{name}{ext}'
    if not os.path.exists(path):
        with urllib.request.urlopen(url, timeout=60) as r, open(path, 'wb') as f:
            f.write(r.read())
    return f'assets/{name}{ext}'


def render(blocks):
    out, i = [], 0
    while i < len(blocks):
        b = blocks[i]; t = b['type']
        # 이어지는 목록 항목은 하나의 목록으로 묶기
        if t in ('bulleted_list_item', 'numbered_list_item', 'to_do'):
            tag = 'ol' if t == 'numbered_list_item' else 'ul'
            items = []
            while i < len(blocks) and blocks[i]['type'] == t:
                x = blocks[i]; v = x[t]
                box = ('☑ ' if v.get('checked') else '☐ ') if t == 'to_do' else ''
                sub = render(children(x['id'])) if x.get('has_children') else ''
                items.append(f'<li>{box}{rich(v["rich_text"])}{sub}</li>')
                i += 1
            out.append(f'<{tag}>' + ''.join(items) + f'</{tag}>')
            continue
        out.append(block(b))
        i += 1
    return '\n'.join(x for x in out if x)


def block(b):
    t = b['type']; v = b.get(t, {})
    kids = lambda: render(children(b['id'])) if b.get('has_children') else ''
    if t == 'paragraph':
        txt = rich(v['rich_text'])
        return f'<p>{txt}</p>' + kids() if txt else ''
    if t in ('heading_1', 'heading_2', 'heading_3'):
        n = t[-1]; inner = rich(v['rich_text'])
        if v.get('is_toggleable'):
            return f'<h{n}>{inner}</h{n}>' + kids()
        return f'<h{n}>{inner}</h{n}>'
    if t == 'callout':
        return f'<div class="callout {color_class(v.get("color"))}"><p>{rich(v["rich_text"])}</p>{kids()}</div>'
    if t == 'quote':
        cls = color_class(v.get('color'))
        if cls:  # 색이 있는 인용 블록은 노션에서 회색 상자로 보임
            return f'<div class="quote"><p>{rich(v["rich_text"])}</p>{kids()}</div>'
        return f'<blockquote><p>{rich(v["rich_text"])}</p>{kids()}</blockquote>'
    if t == 'toggle':
        return f'<details class="toggle"><summary>{rich(v["rich_text"])}</summary>{kids()}</details>'
    if t == 'code':
        code = html.escape(''.join(r.get('plain_text', '') for r in v['rich_text']))
        return f'<pre><code>{code}</code></pre>'
    if t == 'divider':
        return '<hr>'
    if t == 'table':
        rows = children(b['id']); head = v.get('has_column_header')
        h = []
        for ri, r in enumerate(rows):
            cells = r['table_row']['cells']; tag = 'th' if (head and ri == 0) else 'td'
            h.append('<tr>' + ''.join(f'<{tag}>{rich(c)}</{tag}>' for c in cells) + '</tr>')
        return '<table>' + ''.join(h) + '</table>'
    if t == 'column_list':
        cols = children(b['id'])
        return '<div class="cols">' + ''.join(f'<div class="col">{render(children(c["id"]))}</div>' for c in cols) + '</div>'
    if t == 'image':
        src = v.get('file', {}).get('url') or v.get('external', {}).get('url')
        if not src: return ''
        if v.get('type') == 'file':
            src = save_image(src)
        cap = rich(v.get('caption'))
        return f'<figure><img src="{html.escape(src)}" alt="">' + (f'<figcaption class="gray">{cap}</figcaption>' if cap else '') + '</figure>'
    if t == 'bookmark' or t == 'embed' or t == 'link_preview':
        u = v.get('url', '')
        return f'<p><a href="{html.escape(u)}">{html.escape(u)}</a></p>' if u else ''
    if t in ('file', 'pdf'):
        # 첨부 파일은 내려받기 주소가 만료되므로 config.json 의 downloadUrl(구글 드라이브 등)로 안내
        return ''
    if t in ('table_of_contents', 'child_page', 'child_database', 'breadcrumb'):
        return ''
    if t == 'synced_block':
        return kids()
    return ''


if __name__ == '__main__':
    body = render(children(PAGE))
    open(f'{OUT_DIR}/lesson.html', 'w', encoding='utf-8').write(body)
    print('lesson.html', len(body), 'bytes')
