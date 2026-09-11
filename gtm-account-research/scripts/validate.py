#!/usr/bin/env python3
"""Offline schema + referential checks. No external dependency or network.
Validates the keyword subset used by the shipped JSON Schemas; rejects unknown keywords.
Semantic truth and discovery completeness still require human/agent review.
"""
import argparse, calendar, hashlib, ipaddress, json, re, sys
from datetime import datetime,date
from pathlib import Path
from urllib.parse import urlsplit,parse_qsl
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
def need(ok,msg):
    if not ok: raise ValueError(msg)
def read(p):
    def unique(pairs):
        d={}
        for k,v in pairs:
            need(k not in d,'duplicate key: '+k);d[k]=v
        return d
    return json.loads(Path(p).read_text(),object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def timestamp(v):
    t=datetime.fromisoformat(v.replace('Z','+00:00'));need(t.tzinfo is not None,'timestamp needs timezone');return t

def public_url(v):
    u=urlsplit(v);need(u.scheme=='https' and u.hostname and not u.username and not u.password,'public HTTPS URL required')
    h=u.hostname.lower();need(h not in ('localhost',) and '.' in h and not h.endswith(('.local','.internal','.localhost')),'local hostname')
    try: ip=ipaddress.ip_address(h)
    except ValueError: pass
    else:need(ip.is_global,'nonpublic IP')
    need(not any(re.search(r'token|signature|credential|api.?key|password',k,re.I) for k,_ in parse_qsl(u.query)),'signed/secret URL')

def partial_date(v):
    need(bool(re.fullmatch(r'\d{4}(-\d{2})?(-\d{2})?',v)),'invalid date precision')
    date.fromisoformat(v+('-01-01' if len(v)==4 else '-01' if len(v)==7 else ''))
def schema_check(v,s,where='$'):
    allowed={'$schema','$id','type','properties','required','additionalProperties','items','minItems','minLength','minimum','maximum','pattern','enum','anyOf','format'}
    need(set(s)<=allowed,'unsupported schema keywords '+str(set(s)-allowed))
    if 'anyOf' in s:
        for sub in s['anyOf']:
            try:schema_check(v,sub,where);return
            except (ValueError,TypeError):pass
        raise ValueError(where+': no union alternative matches')
    if 'enum' in s:need(v in s['enum'],where+': invalid enum')
    if 'type' in s:
        types={'object':dict,'array':list,'string':str,'integer':int,'number':(int,float),'boolean':bool,'null':type(None)}
        need(isinstance(v,types[s['type']]) and not (isinstance(v,bool) and s['type'] in ('integer','number')),where+': wrong type')
    if isinstance(v,dict):
        props=s.get('properties',{});need(set(s.get('required',[]))<=set(v),where+': missing fields '+str(set(s.get('required',[]))-set(v)))
        if s.get('additionalProperties') is False:need(set(v)<=set(props),where+': extra fields '+str(set(v)-set(props)))
        for k,x in v.items():
            if k in props:schema_check(x,props[k],where+'.'+k)
    if isinstance(v,list):
        need(len(v)>=s.get('minItems',0),where+': too few items')
        for i,x in enumerate(v):schema_check(x,s.get('items',{}),where+f'[{i}]')
    if isinstance(v,str):
        need(len(v)>=s.get('minLength',0),where+': empty text')
        if 'pattern' in s:need(re.search(s['pattern'],v),where+': pattern')
        fmt=s.get('format')
        if fmt=='timestamp':timestamp(v)
        elif fmt=='date':date.fromisoformat(v);need(len(v)==10,'full date required')
        elif fmt=='partial-date':partial_date(v)
        elif fmt=='public-url':public_url(v)
        elif fmt=='source-path':need(bool(re.fullmatch(r'sources/[A-Za-z0-9_.-]+\.(md|txt|vtt|json)',v)),where+': source path')
    if isinstance(v,(int,float)) and not isinstance(v,bool):need(s.get('minimum',v)<=v<=s.get('maximum',v),where+': out of bounds')
def check_doc(d,name):schema_check(d,read(ROOT/'schemas'/f'{name}.schema.json'))
def index(rows):
    d={x['id']:x for x in rows};need(len(d)==len(rows),'duplicate IDs');return d
def refs(ids,table,label):
    need(len(ids)==len(set(ids)),label+': duplicate refs');need(set(ids)<=set(table),label+': unknown refs '+str(set(ids)-set(table)))
def inside(root,rel):
    root=Path(root).resolve();p=(root/rel).resolve();need(p.is_relative_to(root),'path escapes root');need(not (root/rel).is_symlink(),'symlink refused');return p

def seller_check(p):
    d=read(p);check_doc(d,'seller-profile');sources=index(d['sources']);claims=index(d['capabilities']+d['limits']+d['customer_workflows']);gaps=index(d['unknowns'])
    refs(d['seller']['source_ids'],sources,'seller identity')
    for c in claims.values():refs(c['source_ids'],sources,c['id']);need(not(c['basis']=='inferred' and c['availability']=='supported'),'inference cannot confirm support')
    for h in d['fit_hypotheses']+d['exclusion_hypotheses']:refs(h['basis_claim_ids'],claims,h['id'])
    for g in gaps.values():refs(g['related_claim_ids'],claims,g['id'])
    refs(d['readiness']['blocking_gap_ids'],gaps,'blocking gaps')
    need(set(d['readiness']['blocking_gap_ids'])=={g['id'] for g in gaps.values() if g['blocks_research']},'inconsistent blocking gaps')
    if d['readiness']['status']!='needs_input':
        need(not d['readiness']['blocking_gap_ids'],'ready with blocking gaps');need(any(c['basis']!='inferred' for c in d['capabilities']),'ready requires sourced capability')
    return d

def run_check(root,final=False):
    root=Path(root);a=read(root/'account.json');s=read(root/'sources.json');l=read(root/'research-log.json')
    for doc,name in [(a,'account'),(s,'sources'),(l,'research-log')]:check_doc(doc,name)
    need(a['account_id']==s['account_id']==l['account_id'],'account IDs disagree')
    tz=ZoneInfo(a['research_timezone']);asof=date.fromisoformat(a['research_as_of'])
    ss=index(s['sources']);es=index(s['evidence']);cs=index(a['claims']);qs=index(l['questions']);acts=index(l['actions']);rounds=index(l['rounds']);index(l['checkpoints']);index(a['workflows']);index(a['unknowns'])
    for src in ss.values():
        refs(src['action_ids'],acts,src['id']);
        if src['derived_from']:refs([src['derived_from']],ss,'derivative');need(src['derived_from']!=src['id'],'self derivative')
        need((src['published_on'] is None)==(src['publication_kind']=='unknown'),'publication kind/date mismatch')
        if src['retrieved_at']:
            rt=timestamp(src['retrieved_at']);need(rt.astimezone(tz).date()<=asof,'capture after research day')
            if src['published_on']:need(date.fromisoformat(src['published_on']+('-01-01' if len(src['published_on'])==4 else '-01' if len(src['published_on'])==7 else ''))<=rt.astimezone(tz).date(),'publication after capture')
        if src['reviewed_at']:
            rv=timestamp(src['reviewed_at']);need(rv.astimezone(tz).date()<=asof,'review after research day')
            if src['retrieved_at']:need(rv>=timestamp(src['retrieved_at']),'review before retrieval')
        if src['path']:need(inside(root,src['path']).is_file(),'missing source text')
        else:need(src['extracted_coverage'] in ('none','metadata_only') and src['reviewed_coverage'] in ('none','metadata_only'),'missing body with full/selected coverage')
    for e in es.values():
        refs([e['source_id']],ss,e['id']);src=ss[e['source_id']];need(src['path'] is not None and src['reviewed_coverage'] in ('selected','full'),e['id']+': evidence without body review')
        loc=e['locator'];lines=inside(root,src['path']).read_text().splitlines();st,en=loc['line_start'],loc['line_end'];need(1<=st<=en<=len(lines),'invalid passage lines')
        norm=lambda t:re.sub(r'\s+',' ',t).strip()
        quote=norm(e['quote']);need(bool(quote),e['id']+': empty normalized quote')
        need(quote in norm('\n'.join(lines[st-1:en])),e['id']+': quote absent at locator')
        x,y=loc['start_seconds'],loc['end_seconds'];need((x is None)==(y is None) and (x is None or x<y),'invalid media interval')
        refs(e['verification']['action_ids'],acts,'verification')
    for c in cs.values():
        refs(c['evidence_ids'],es,c['id']);refs(c['conflicting_evidence_ids'],es,c['id']);need(c['kind']=='unresolved' or c['evidence_ids'],c['id']+': supported/inferred claim lacks evidence')
    for w in a['workflows']:
        refs(w['step_claim_ids'],cs,w['id']);refs(w['connection_claim_ids'],cs,w['id'])
    refs(a['assessment']['rationale_claim_ids'],cs,'assessment')
    for u in a['unknowns']:refs([u['question_id']],qs,'unknown')
    for q in qs.values():
        refs(q['source_ids'],ss,q['id'])
        if q['parent_question_id']:refs([q['parent_question_id']],qs,'parent');need(q['parent_question_id']!=q['id'],'self parent')
        need(q['status'] not in ('open','active') or q['next_action'],q['id']+': open lead needs next action')
    for act in acts.values():
        refs(act['question_ids'],qs,act['id']);refs(act['source_ids'],ss,act['id'])
        if act['correction_of']:refs([act['correction_of']],acts,'correction');need(act['correction_of']!=act['id'],'self correction')
    for r in rounds.values():refs(r['action_ids'],acts,r['id'])
    previous=None;covered=[]
    for c in l['checkpoints']:
        t=timestamp(c['at']);need(previous is None or t>=previous,'checkpoint time reversed');previous=t
        if c['round_id']:refs([c['round_id']],rounds,'checkpoint round');covered.append(c['round_id'])
        for d in c['dimensions'].values():refs(d['evidence_ids'],es,'checkpoint evidence');refs(d['question_ids'],qs,'checkpoint gaps')
    need(l['checkpoints'][0]['round_id'] is None,'baseline required');need(set(covered)==set(rounds),'round checkpoints incomplete')
    f=l['final_assessment'];refs(f['question_ids'],qs,'final gaps')
    if final:need(f['status']!='in_progress','research unfinished')
    if f['status']=='complete':need(not any(q['status'] in ('open','active','budget_limited','access_blocked') for q in qs.values()),'complete with outstanding/resource-blocked leads')
    for name in ['account.json','sources.json','research-log.json','START_HERE.md']:
        if (root/name).exists():
            txt=(root/name).read_text();need(not re.search(r'/Users/|/private/|file://|(?i:api[_-]?key)\s*[:=]\s*[\"\']?[A-Za-z0-9_-]{12}',txt),'private path/credential pattern in '+name)
    return a,s,l

def main():
    ap=argparse.ArgumentParser();ap.add_argument('kind',choices=['seller','run']);ap.add_argument('path');ap.add_argument('--final',action='store_true');args=ap.parse_args()
    try:
        result=seller_check(args.path) if args.kind=='seller' else run_check(args.path,args.final)
        print(json.dumps({'status':'passed','scope':'structure, references, retained quotes; not factual completeness'}))
    except (ValueError,KeyError,TypeError,OSError) as e:print(str(e),file=sys.stderr);sys.exit(1)
if __name__=='__main__':main()
