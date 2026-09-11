#!/usr/bin/env python3
"""Explicit allowlist export; no seller docs, code, approval receipts or raw media."""
import argparse,json,re,shutil,sys,zipfile
from pathlib import Path
from validate import read,need,digest,inside,run_check

def audit_text(text,label):
    need(not re.search(r'/Users/|/private/|file://|(?i:authorization:\s*bearer|-----BEGIN .*PRIVATE KEY)',text),'private content pattern in '+label)
    need(not re.search(r'https?://[^\s<>]*[?&](?:[^=\s]*(?:token|signature|credential|api.?key|password)[^=\s]*)=',text,re.I),'signed URL in '+label)

def export_names(sources):
    return ['account.json','sources.json','research-log.json','START_HERE.md']+list(dict.fromkeys(x['path'] for x in sources['sources'] if x['path']))

def export(run,output):
    run=Path(run);out=Path(output);need(not out.exists(),'output exists; preserve old exports')
    a,s,l=run_check(run,True);need((run/'START_HERE.md').is_file(),'START_HERE missing')
    names=export_names(s)
    for name in names:audit_text(inside(run,name).read_text(),name)
    out.mkdir(parents=True)
    try:
        for name in names:
            dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(inside(run,name),dest)
        manifest={'schema_version':'2.0','account_id':a['account_id'],'files':{name:digest(out/name) for name in names},'scope':'Prospect JSON/text only. Seller profile referenced by identity/revision/hash; internal seller sources not included.'}
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        verify(out)
        with zipfile.ZipFile(str(out)+'.zip','x',zipfile.ZIP_DEFLATED) as z:
            for name in names+['manifest.json']:z.write(out/name,name)
    except Exception:
        # Failed exports retained for diagnosis; never announce as verified.
        raise
    return {'status':'verified','output':str(out),'zip':str(out)+'.zip','files':len(names),'limits':'Static checks cannot identify all sensitive prose or establish claim truth; producing agent must review export scope.'}

def verify(out):
    out=Path(out);m=read(out/'manifest.json');expected=set(m['files'])|{'manifest.json'};actual={str(f.relative_to(out)) for f in out.rglob('*') if f.is_file()}
    a,s,_=run_check(out,True)
    need(set(m['files'])==set(export_names(s)),'manifest violates prospect export allowlist')
    need(m['account_id']==a['account_id'],'manifest account ID mismatch')
    need(expected==actual,'unmanifested or missing files')
    for name,h in m['files'].items():p=inside(out,name);need(p.is_file() and digest(p)==h,'changed export '+name);audit_text(p.read_text(),name)
    return {'status':'verified','files':len(m['files'])}

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True)
    e=sp.add_parser('export');e.add_argument('--run',required=True);e.add_argument('--output',required=True)
    v=sp.add_parser('verify');v.add_argument('--output',required=True)
    a=ap.parse_args()
    try:print(json.dumps(export(a.run,a.output) if a.cmd=='export' else verify(a.output)))
    except (ValueError,OSError,KeyError) as e:print(str(e),file=sys.stderr);sys.exit(1)
if __name__=='__main__':main()
