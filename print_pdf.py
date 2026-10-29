"""웹 교안(index.html) → 인쇄용 PDF. 토글은 모두 펼치고, 탭은 모두 보이게, 화면용 버튼은 숨깁니다."""
import asyncio, sys, pathlib
from playwright.async_api import async_playwright

SRC, OUT = sys.argv[1], sys.argv[2]
CSS = """
header.bar, .back, .help, .toc, .dock, .copy, .show, .teachbtn, .tabbar, .dl { display: none !important; }
.mark.here::before { display: none !important; }
body { background: #fff !important; }
#lesson { max-width: none !important; }
#lesson pre { padding-top: 1em !important; }
#lesson h1 { break-before: page; }
#lesson h1:first-of-type { break-before: auto; }
table, pre, .callout, blockquote, img { break-inside: avoid; }
h1, h2, h3 { break-after: avoid; }
.tabpane { display: block !important; }
.tablabel { font-weight: 700; margin: .8em 0 .2em; }
"""
JS = """() => {
  document.querySelectorAll('details').forEach(d => d.open = true);
  document.querySelectorAll('.tabs').forEach(box => {
    const btns = [...box.querySelectorAll('.tabbar button')];
    box.querySelectorAll('.tabpane').forEach((p, i) => {
      p.hidden = false;
      const h = document.createElement('div'); h.className = 'tablabel'; h.textContent = '▸ ' + (btns[i]?.textContent || '');
      p.prepend(h);
    });
  });
}"""

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(color_scheme='light')
        await pg.goto(pathlib.Path(SRC).resolve().as_uri(), wait_until='load')
        await pg.wait_for_timeout(4000)
        await pg.add_style_tag(content=CSS)
        await pg.evaluate(JS)
        await pg.evaluate('document.fonts.ready')
        await pg.pdf(path=OUT, format='A4', print_background=True,
                     margin={'top': '16mm', 'bottom': '18mm', 'left': '15mm', 'right': '15mm'},
                     display_header_footer=True, header_template='<span></span>',
                     footer_template='<div style="width:100%;font-size:9px;color:#777;text-align:center;">같은 AI로 다른 결과 만들기 · <span class="pageNumber"></span> / <span class="totalPages"></span></div>')
        await b.close()

asyncio.run(main())
