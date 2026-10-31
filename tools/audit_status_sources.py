#!/usr/bin/env python3
"""Read-only audit of known DLSS-NR status producers; never instruments engine code."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
from loclib import mask_cpp,find_matching,split_args,extract_string_expression,read_source_text,_string_literals_in_region

def inventory(root: Path):
    exact={};dynamic=[]
    paths=[]
    for scope in ('OptiScaler/shaders/dlssnr','OptiScaler/dlssnr'):
        paths += sorted(p for p in (root/scope).glob('*') if p.suffix in ('.cpp','.h'))
    for path in paths:
        text,_=read_source_text(path);masked=mask_cpp(text);rel=path.relative_to(root).as_posix()
        for match in re.finditer(r'\b(?:Say|say|Fail)\s*\(',masked):
            op=masked.find('(',match.start());end=find_matching(text,op)
            if end<0:continue
            args=split_args(text,op+1,end)
            if not args:continue
            a,b=args[0];expr=text[a:b].strip();source=extract_string_expression(expr)
            loc=f'{rel}:{text.count(chr(10),0,a)+1}'
            if source:exact.setdefault(source,[]).append(loc)
            elif '?' in masked[a:b] and '+' not in masked[a:b]:
                for _,_,source,_ in _string_literals_in_region(text,a,b):
                    if source:exact.setdefault(source,[]).append(loc)
            elif '+' in masked[a:b]:dynamic.append({'location':loc,'expression':expr})
        for match in re.finditer(r'\b(?:reason|spatialStatus|spatialFallbackReason|enlargementStatus|failureReason|status)\s*=',masked):
            end=masked.find(';',match.end())
            if end<0:continue
            source=extract_string_expression(text[match.end():end].strip())
            if source:exact.setdefault(source,[]).append(f'{rel}:{text.count(chr(10),0,match.end())+1}')
    return exact,dynamic

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    if not (args.source/'OptiScaler/dlssnr').is_dir():
        parser.error('source must contain OptiScaler/dlssnr')
    rows=json.loads((Path(__file__).resolve().parents[1]/'Localization/status.zh-CN.json').read_text())['entries']
    known={r['source'] for r in rows if not r.get('pattern')}
    exact,dynamic=inventory(args.source);missing={s:loc for s,loc in exact.items() if s not in known}
    result={'static_sources':len(exact),'missing_static':missing,'dynamic_compositions_for_manual_audit':dynamic,'note':'Vendor/runtime error payloads and unrecognized future text intentionally fall back to English; this audit does not claim game-tested coverage.'}
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(f'static status sources={len(exact)} missing={len(missing)} dynamic compositions={len(dynamic)}')
    return bool(missing)
if __name__=='__main__':raise SystemExit(main())
