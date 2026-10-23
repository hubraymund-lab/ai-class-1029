"""본문 조각 + 설정 → 페이지. --artifact 는 미리보기(문서 뼈대 없이), 기본은 GitHub Pages용 완성 문서."""
import json, sys, argparse
ap = argparse.ArgumentParser(); ap.add_argument('lesson'); ap.add_argument('out'); ap.add_argument('--config', default=None); ap.add_argument('--artifact', action='store_true')
a = ap.parse_args()
here = __file__.rsplit('/', 1)[0]
tpl = open(f'{here}/template.html', encoding='utf-8').read()
cfg = json.load(open(a.config, encoding='utf-8')) if a.config else {}
body = tpl.replace('<!--LESSON-->', open(a.lesson, encoding='utf-8').read()) \
          .replace('<!--CONFIG-->', json.dumps(cfg, ensure_ascii=False).replace('</', '<\\/'))
sb = '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js"></script>' if cfg.get('supabaseUrl') else ''
body = body.replace('<!--SUPABASE-->', sb)
if not a.artifact:
    body = '<!doctype html>\n<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<style>[hidden]{display:none!important}img{max-width:100%}:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}</style>\n</head><body>\n' + body + '\n</body></html>\n'
open(a.out, 'w', encoding='utf-8').write(body)
print('wrote', a.out, len(body))
