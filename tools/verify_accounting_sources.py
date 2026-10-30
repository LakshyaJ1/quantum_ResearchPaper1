"""Retrieve the two primary accounting references used in the revision."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

import fitz
import requests

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'docs/revision/sources'


def main():
    for name,identifier,patterns in [
        ('walenta','1309.2583v2',[r'127',r'authentication']),
        ('fung','0910.0312v2',[r'logarith',r'authentication'])]:
        url=f'https://arxiv.org/pdf/{identifier}'
        response=requests.get(url,timeout=45)
        response.raise_for_status()
        if not response.content.startswith(b'%PDF'):
            raise RuntimeError(f'{url} did not return a PDF')
        path=DEST/f'{name}_primary.pdf'
        path.write_bytes(response.content)
        document=fitz.open(path)
        pages=[page.get_text() for page in document]
        (DEST/f'{name}_primary.txt').write_text('\n'.join(
            f'PAGE {i+1}\n{text}' for i,text in enumerate(pages)),encoding='utf-8')
        selected=[]
        for i,text in enumerate(pages):
            for pattern in patterns:
                hit=re.search(pattern,text,re.I)
                if hit:
                    selected.append({'page':i+1,'pattern':pattern,
                                     'context':text[max(0,hit.start()-160):hit.end()+280]})
        record={'url':url,'final_url':response.url,'status':response.status_code,
                'fetched_utc':datetime.now(timezone.utc).isoformat(),
                'sha256':hashlib.sha256(response.content).hexdigest(),
                'pages':len(document),'relevant_text':selected}
        (DEST/f'{name}_primary_fetch.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
        print(json.dumps({'name':name,'pages':len(document),'matches':selected[:8]},indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
