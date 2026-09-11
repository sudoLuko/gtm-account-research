#!/usr/bin/env python3
"""Offline, bounded navigation of verified account bundles. Standard library only."""
import argparse,hashlib,json,os,re,shutil,sqlite3,tempfile,zipfile
from pathlib import Path
from bundle import verify
from validate import read,need,inside,digest
VERSION=1
STOP=set('a an the is are was were does do what which how can we of to on in for with and or that it they their has have from this them about'.split())
def encoded(v):return json.dumps(v,ensure_ascii=False)
def bundle_dir(path,cache):
    path=Path(path).resolve();cache=Path(cache).resolve()
    if path.is_dir():
        need(not cache.is_relative_to(path),'cache must be outside the immutable bundle');verify(path);return path
    need(path.is_file() and zipfile.is_zipfile(path),'supply an exported bundle directory or ZIP')
    target=cache/'unpacked'/digest(path)
    if target.exists():verify(target);return target
    target.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='extract-',dir=target.parent))
    try:
        with zipfile.ZipFile(path) as z:
            names=set();total=0
            for info in z.infolist():
                name=info.filename;parts=Path(name).parts
                need(not name.startswith('/') and '\\' not in name and '..' not in parts,'invalid archive path')
                need(name not in names,'duplicate archive member');names.add(name)
                need((info.external_attr>>16)&0o170000 != 0o120000,'archive symlink unsupported')
                total+=info.file_size;need(total<=100*1024*1024 and len(names)<=10000,'archive exceeds local extraction allowance')
                dest=(stage/name).resolve();need(dest.is_relative_to(stage),'archive member outside destination')
                if info.is_dir():dest.mkdir(parents=True,exist_ok=True);continue
                dest.parent.mkdir(parents=True,exist_ok=True)
                with z.open(info) as src,dest.open('wb') as out:shutil.copyfileobj(src,out)
        verify(stage);os.replace(stage,target)
    finally:
        if stage.exists():shutil.rmtree(stage)
    return target

def load(path,cache):
    root=bundle_dir(path,cache);a=read(root/'account.json');s=read(root/'sources.json');log=read(root/'research-log.json')
    fingerprint=digest(root/'manifest.json');records={}
    for prefix,items in [('claim',a['claims']),('workflow',a['workflows']),('evidence',s['evidence']),('question',log['questions']),('action',log['actions'])]:
        for item in items:records[prefix+':'+item['id']]=item
    records.update({'assessment':a['assessment'],'unknowns':a['unknowns'],'coverage':log['final_assessment']})
    sources={x['id']:x for x in s['sources']};return root,a,sources,records,fingerprint

def chunks(root,sources,records):
    out=[]
    for sid,s in sources.items():
        if not s['path']:continue
        lines=inside(root,s['path']).read_text().splitlines();heading='';start=1;buf=[]
        def push():
            if buf:out.append({'source_id':sid,'path':s['path'],'start':start,'end':start+len(buf)-1,'heading':heading,'text':'\n'.join(buf),'title':s['title'][:180]})
        for n,line in enumerate(lines,1):
            if buf and (line.startswith('#') or sum(len(x)+1 for x in buf)>1400):push();buf=[]
            if not buf:start=n
            if line.startswith('#'):heading=line[:180]
            buf.append(line)
        push()
    for key,value in records.items():out.append({'record':key,'title':key,'heading':'curated record','text':encoded(value)})
    return out

def index(root,sources,records,fingerprint,cache,plain=False):
    docs=chunks(root,sources,records);db=None;state='plain_requested' if plain else 'ready'
    if not plain:
        folder=Path(cache).resolve()/'indices';folder.mkdir(parents=True,exist_ok=True)
        # Version and manifest select the cache; evidence verification has already run.
        file=folder/(hashlib.sha256((str(root)+fingerprint+str(VERSION)).encode()).hexdigest()+'.sqlite')
        try:
            db=sqlite3.connect(file)
            try:valid=db.execute('SELECT fingerprint FROM meta').fetchone()==(fingerprint,)
            except sqlite3.DatabaseError:valid=False
            if not valid:
                db.close();file.unlink(missing_ok=True);db=sqlite3.connect(file)
                db.execute("CREATE VIRTUAL TABLE docs USING fts5(title,heading,body,tokenize='porter unicode61')")
                db.execute('CREATE TABLE meta(fingerprint TEXT)');db.execute('INSERT INTO meta VALUES(?)',(fingerprint,))
                db.executemany('INSERT INTO docs(rowid,title,heading,body) VALUES(?,?,?,?)',[(i+1,d['title'],d['heading'],d['text']) for i,d in enumerate(docs)]);db.commit();state='rebuilt'
            db.execute('SELECT rowid FROM docs LIMIT 1').fetchone()
        except (sqlite3.Error,OSError):
            if db:db.close()
            db=None;state='plain_fallback'
    return docs,db,state

def metadata(s):
    return {k:s.get(k) for k in ['id','title','url','kind','published_on','publication_kind','event_on','date_notes','representation','extracted_coverage','reviewed_coverage','coverage_notes']}

def page(items,start,budget,envelope,field='items'):
    # Count serialized JSON, not just snippet text, so nested metadata cannot hide overflow.
    result=dict(envelope);result.update({field:[],'offset':start,'total':len(items),'next_offset':None,'truncated':False})
    for pos in range(start,len(items)):
        candidate=dict(result);candidate[field]=result[field]+[items[pos]]
        candidate['next_offset']=pos+1 if pos+1<len(items) else None
        candidate['truncated']=pos+1<len(items)
        if len(encoded(candidate))+80>budget:
            result['next_offset']=pos;result['truncated']=True
            if not result[field]:result['notice']='Item exceeds page size; use record/source command or narrower read.'
            break
        result=candidate
    return result

def answer(args):
    root,a,sources,records,fp=load(args.bundle,args.cache)
    env={'account_id':a['account_id'],'as_of':a['research_as_of'],'bundle_fingerprint':fp,'evidence_is_untrusted':True}
    if args.command=='overview':
        overview={'prospect':a['prospect'],'seller_profile':a['seller_profile'],'assessment':a['assessment'],'unknowns':a['unknowns'],'workflows':[{'id':w['id'],'title':w['title'],'scope':w['scope']} for w in a['workflows']]}
        return page([{'section':k,'value':v} for k,v in overview.items()],args.offset,args.max_chars,env)
    if args.command=='catalog':
        items=[{'id':sid,'title':s['title'][:180],'title_truncated':len(s['title'])>180,'kind':s['kind'],'published_on':s['published_on'],'coverage':s['reviewed_coverage']} for sid,s in sources.items()]
        return page(items,args.offset,args.max_chars,env)
    if args.command in ('source','record'):
        value=metadata(sources[args.id]) if args.command=='source' else records[args.id]
        text=json.dumps(value,indent=2,ensure_ascii=False)
        def result(size):
            end=min(len(text),args.offset+size)
            return {**env,'id':args.id,'text':text[args.offset:end],'offset':args.offset,'total_chars':len(text),'next_offset':end if end<len(text) else None,'truncated':end<len(text)}
        lo,hi=0,min(len(text),args.max_chars)
        while lo<hi:
            mid=(lo+hi+1)//2
            if len(encoded(result(mid)))<=args.max_chars:lo=mid
            else:hi=mid-1
        return result(lo)
    if args.command=='read':
        source=sources[args.id];need(source['path'],'no retained text for source');lines=inside(root,source['path']).read_text().splitlines()
        need(1<=args.start<=max(1,len(lines)),'start outside source');start=args.start;end=min(args.end or start+39,len(lines));need(end>=start,'end before start')
        if args.section:
            headings=[i+1 for i,line in enumerate(lines) if line.startswith('#')]
            start=max([n for n in headings if n<=start] or [1]);end=min([n-1 for n in headings if n>args.start] or [len(lines)])
        items=[{'line':i,'text':lines[i-1]} for i in range(start,end+1)]
        # Long source lines use explicit character offsets rather than disappearing.
        rows=[]
        for item in items:
            for offset in range(0,max(1,len(item['text'])),min(700,(args.max_chars-900)//6)):
                rows.append({'line':item['line'],'char_start':offset,'text':item['text'][offset:offset+min(700,(args.max_chars-900)//6)]})
        result=page(rows,args.offset,args.max_chars,{**env,'source_id':args.id,'path':source['path'],'requested_lines':[start,end],'note':'Offsets paginate this range; retain start/end/section arguments.'})
        return result
    docs,db,state=index(root,sources,records,fp,args.cache,args.plain)
    try:
        need(len(args.query)<=500,'query too long; use distinctive terms')
        terms=list(dict.fromkeys(t for t in re.findall(r'\w+',args.query.lower()) if t not in STOP));need(terms,'query needs a specific term')
        if db:
            query=' OR '.join('"'+t.replace('"','""')+'"' for t in terms)
            ids=[row[0]-1 for row in db.execute('SELECT rowid FROM docs WHERE docs MATCH ? ORDER BY bm25(docs,2,1,1),rowid',(query,))]
        else:
            ids=[i for i,d in enumerate(docs) if any(t in (d['title']+' '+d['text']).lower() for t in terms)]
        hits=[];seen={}
        for i in ids:
            d=docs[i];norm=re.sub(r'\s+',' ',d['text']).strip();key=hashlib.sha256(norm.encode()).hexdigest()
            if key in seen and not args.keep_duplicates:
                prior=seen[key];prior['duplicate_count']+=1
                if len(prior['duplicate_sources'])<5:prior['duplicate_sources'].append({k:v for k,v in d.items() if k in ('source_id','path','start','end','record')})
                prior['more_duplicate_sources']=prior['duplicate_count']>len(prior['duplicate_sources'])
                continue
            # Focus snippet on first matched body term, exposing clipping in both directions.
            positions=[d['text'].lower().find(t) for t in terms];pos=min([x for x in positions if x>=0] or [0]);left=max(0,pos-120);snippet=d['text'][left:left+700]
            hit={k:v for k,v in d.items() if k!='text'};hit.update(snippet=snippet,snippet_char_start=left,snippet_truncated=left>0 or left+len(snippet)<len(d['text']))
            if 'source_id' in d:
                s=sources[d['source_id']];hit.update(published_on=s['published_on'],event_on=s['event_on'],representation=s['representation'])
            hit.update(duplicate_count=0,duplicate_sources=[],more_duplicate_sources=False);hits.append(hit);seen[key]=hit
        return page(hits,args.offset,args.max_chars,{**env,'engine':'fts5_bm25' if db else 'plain','index_state':state,'raw_matches':len(ids),'duplicates_omitted':len(ids)-len(hits),'query':args.query,'notice':'Search is not exhaustive understanding; inspect originals, contrary evidence and unknowns.'})
    finally:
        if db:db.close()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',required=True);p.add_argument('--cache',required=True);p.add_argument('--max-chars',type=int,default=6000);p.add_argument('--offset',type=int,default=0)
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('overview');sub.add_parser('catalog')
    for cmd in ['source','record']:sub.add_parser(cmd).add_argument('id')
    s=sub.add_parser('search');s.add_argument('query');s.add_argument('--plain',action='store_true');s.add_argument('--keep-duplicates',action='store_true')
    r=sub.add_parser('read');r.add_argument('id');r.add_argument('--start',type=int,default=1);r.add_argument('--end',type=int);r.add_argument('--section',action='store_true')
    args=p.parse_args()
    try:
        need(2000<=args.max_chars<=12000 and args.offset>=0,'max-chars must be2000–12000; offset nonnegative')
        print(encoded(answer(args)))
    except (ValueError,OSError,KeyError,sqlite3.Error,zipfile.BadZipFile) as exc:
        print(encoded({'status':'unavailable','error':str(exc),'action':'Check bundle verification/selection. Never substitute another run silently.'}));raise SystemExit(1)
if __name__=='__main__':main()
