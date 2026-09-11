#!/usr/bin/env python3
"""Caption-first public media inspection; raw media stays in pipes/RAM.
Model/dependency files and an explicit consent receipt may live on disk.
Outputs JSON text only. This helper makes no transcription API calls.
"""
import argparse,base64,json,os,queue,shutil,signal,socket,subprocess,sys,threading,time
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlsplit
from validate import public_url,need,read

def now():return datetime.now(timezone.utc).isoformat()
def executable(name):
    p=shutil.which(name);need(p is not None,name+' unavailable; installation requires user authorization');return p

def metadata(url,timeout=60):
    public_url(url)
    cmd=[executable('yt-dlp'),'--ignore-config','--no-cache-dir','--no-playlist','--skip-download','--dump-single-json','--no-warnings','--socket-timeout','20','--retries','1','--',url]
    # Only metadata on stdout. Signed internal media URLs are never returned to the agent.
    p=subprocess.run(cmd,capture_output=True,timeout=timeout)
    need(p.returncode==0,'media metadata unavailable (extractor exit '+str(p.returncode)+'); use a public alternative or record access limit')
    return json.loads(p.stdout)
def safe_metadata(d,url):
    raw=d.get('upload_date');pub=f'{raw[:4]}-{raw[4:6]}-{raw[6:]}' if raw and len(raw)==8 else None
    return {'url':url,'title':d.get('title'),'publisher':d.get('uploader'),'published_on':pub,'duration_seconds':d.get('duration'),'retrieved_at':now()}

def parse_captions(body,ext):
    if ext=='json3':
        d=json.loads(body);return [{'start':e['tStartMs']/1000,'end':(e['tStartMs']+e.get('dDurationMs',0))/1000,'text':''.join(s.get('utf8','') for s in e.get('segs',[])).strip()} for e in d.get('events',[]) if e.get('segs')]
    import re,html
    def sec(v):
        a=v.replace(',','.').split(':');return sum(float(x)*60**i for i,x in enumerate(reversed(a)))
    rows=[]
    for block in re.split(r'\n\s*\n',body.replace('\r','')):
        lines=block.splitlines();match=next(((i,re.match(r'(\d{1,2}:\d{2}(?::\d{2})?[.,]\d+)\s+-->\s+(\d{1,2}:\d{2}(?::\d{2})?[.,]\d+)',line)) for i,line in enumerate(lines) if '-->' in line),None)
        if not match or not match[1]:continue
        i,m=match;t=html.unescape(re.sub('<[^>]*>','', '\n'.join(lines[i+1:]))).strip()
        if t:rows.append({'start':sec(m[1]),'end':sec(m[2]),'text':t})
    return rows

def captions(url,language='en',fetch=None):
    d=metadata(url) if fetch is None else fetch;info=safe_metadata(d,url)
    for kind in ['subtitles','automatic_captions']:
        tracks=d.get(kind) or {};langs=[language]+[x for x in tracks if x.startswith(language+'-')]
        for lang in dict.fromkeys(langs):
            formats=tracks.get(lang,[])
            for ext in ['json3','vtt','srt']:
                track=next((x for x in formats if x.get('ext')==ext and x.get('url')),None)
                if not track:continue
                need(urlsplit(track['url']).scheme=='https','non-HTTPS caption URL refused')
                headers={k:v for k,v in d.get('http_headers',{}).items() if k.lower() in ('user-agent','referer','accept-language')}
                try:
                    with urlopen(Request(track['url'],headers=headers),timeout=30) as resp:
                        body=resp.read(8*1024*1024+1);need(len(body)<=8*1024*1024,'caption limit exceeded')
                    rows=parse_captions(body.decode('utf-8-sig'),ext)
                    if rows:return {**info,'status':'captions','origin':kind,'language':lang,'segments':rows,'coverage':'caption track returned; review coverage must be recorded separately'}
                except Exception:continue
    return {**info,'status':'no_usable_captions','segments':[],'limit':'No accessible supported caption track; visual captions may still exist. Local ASR requires consent.'}

def authorize(path,note):
    need(note.strip(),'actual user authorization reference required')
    p=Path(path);need(not p.exists(),'receipt exists; reuse it or write a new receipt after changed authorization')
    p.parent.mkdir(parents=True,exist_ok=True)
    value={'scope':'local-base-transcription','model':'base','host':socket.gethostname(),'authorized_at':now(),'authorization_reference':note}
    with p.open('x') as f:json.dump(value,f,indent=2)
    try:p.chmod(0o600)
    except OSError:pass
    return {'status':'authorization_recorded','model':'base'}
def consent(path):
    d=read(path);need(d.get('scope')=='local-base-transcription' and d.get('model')=='base' and d.get('host')==socket.gethostname(),'consent missing, wrong scope or different host');need(d.get('authorization_reference'),'consent attribution missing')

def selected_stream(d,video=False):
    formats=d.get('formats') or [d]
    # LinkedIn MP4 metadata often omits codec fields; absence is unknown, not no audio.
    def usable(f):
        codec=f.get('vcodec' if video else 'acodec')
        return f.get('url','').startswith('https://') and codec!='none' and (codec is not None or f.get('ext') in ('mp4','webm','mov','m4a','mp3','ogg'))
    fs=[f for f in formats if usable(f)]
    need(fs,'no usable public media stream')
    if video:fs.sort(key=lambda f:(abs((f.get('height') or 480)-480),f.get('tbr') or 0))
    else:fs.sort(key=lambda f:(f.get('vcodec') not in (None,'none'),f.get('abr') or f.get('tbr') or 1e9))
    f=fs[0];return f['url'],{**d.get('http_headers',{}),**f.get('http_headers',{})}

def ffmpeg_command(d,start=0,duration=None,frame=False):
    url,headers=selected_stream(d,video=frame)
    cmd=[executable('ffmpeg'),'-hide_banner','-loglevel','error','-nostdin','-rw_timeout','30000000','-protocol_whitelist','https,tls,tcp,crypto,http']
    h=''.join(k+': '+str(v)+'\r\n' for k,v in headers.items() if k.lower() in ('user-agent','referer','accept-language') and '\n' not in str(v) and '\r' not in str(v))
    if h:cmd+=['-headers',h]
    if start:cmd+=['-ss',str(start)]
    cmd+=['-i',url]
    if duration:cmd+=['-t',str(duration)]
    if frame:cmd+=['-frames:v','1','-vf','scale=960:-2','-f','image2pipe','-vcodec','mjpeg','pipe:1']
    else:cmd+=['-vn','-ac','1','-ar','16000','-f','s16le','pipe:1']
    return cmd

def audio_commands(url,start=0,duration=None):
    public_url(url)
    # Delegate language/default ranking and transport to yt-dlp. Never choose by
    # lowest bitrate: dubbed tracks may rank first in an unsorted format list.
    download=[executable('yt-dlp'),'--ignore-config','--no-cache-dir','--no-playlist',
              '--no-progress','--socket-timeout','20','--retries','1',
              '--fragment-retries','1','--abort-on-unavailable-fragments',
              '-f','bestaudio/best','-o','-','--',url]
    decode=[executable('ffmpeg'),'-hide_banner','-loglevel','error','-nostdin','-i','pipe:0']
    # Seeking after input decodes/discards the prefix of this non-seekable pipe.
    if start:decode+=['-ss',str(start)]
    if duration is not None:decode+=['-t',str(duration)]
    decode+=['-vn','-ac','1','-ar','16000','-f','s16le','pipe:1']
    return download,decode

_process_stop_lock=threading.Lock()
def stop_process(process):
    if process is None:return
    # The watchdog and generator finalizer may arrive together. Serialize reaping
    # and never signal a PID/group after we have observed that process exit.
    with _process_stop_lock:
        if process.poll() is not None:return
        if os.name=='posix':
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            except PermissionError:
                if process.poll() is None:process.kill()
        else:process.kill()
        process.wait()

def stream_chunks(command,chunk_seconds=30,overlap_seconds=1,timeout=1200,
                  upstream_command=None,expected_seconds=None):
    need(5<=chunk_seconds<=120 and 0<=overlap_seconds<chunk_seconds,'invalid chunk config')
    need(timeout>0 and (expected_seconds is None or expected_seconds>0),'invalid stream limit')
    upstream=None;process=None;thread=None
    q=queue.Queue(maxsize=2);done=threading.Event();expired=threading.Event()
    deadline=time.monotonic()+timeout
    def expire():
        expired.set()
        for child in (process,upstream):
            if child is not None:
                try:stop_process(child)
                except OSError:pass
    timer=None
    def put(x):
        while not done.is_set():
            try:q.put(x,timeout=.2);return
            except queue.Full:pass
    def reader():
        try:
            while not done.is_set():
                block=process.stdout.read(65536)
                if not block:break
                put(block)
        finally:put(None)
    try:
        opts={'stderr':subprocess.DEVNULL,'bufsize':0,'start_new_session':os.name=='posix'}
        if upstream_command:
            upstream=subprocess.Popen(upstream_command,stdout=subprocess.PIPE,**opts)
        process=subprocess.Popen(command,stdin=upstream.stdout if upstream else subprocess.DEVNULL,
                                 stdout=subprocess.PIPE,**opts)
        if upstream:upstream.stdout.close()
        timer=threading.Timer(timeout,expire);timer.daemon=True;timer.start()
        thread=threading.Thread(target=reader,daemon=True);thread.start()
        size=int(chunk_seconds*32000);keep=int(overlap_seconds*32000)
        buf=bytearray();offset=0;received=0
        while True:
            remaining=deadline-time.monotonic()
            need(remaining>0 and not expired.is_set(),'media runtime timeout')
            try:block=q.get(timeout=min(remaining,30))
            except queue.Empty:raise ValueError('media runtime timeout' if expired.is_set() else 'media stalled')
            need(not expired.is_set(),'media runtime timeout')
            if block is None:break
            received+=len(block);buf.extend(block)
            while len(buf)>=size:
                yield offset/32000,bytes(buf[:size])
                del buf[:size-keep];offset+=size-keep
        code=process.wait(timeout=max(.01,min(10,deadline-time.monotonic())))
        need(not expired.is_set(),'media runtime timeout')
        need(code==0,'media decode failed; partial transcript must be labeled')
        need(received>0,'media decode returned no audio')
        if upstream:
            # A bounded decoder may close its input after reaching the requested
            # duration. Broken pipe/termination of its producer is then expected.
            reached=expected_seconds is not None and received/32000>=expected_seconds-.02
            if not reached:
                upstream_code=upstream.wait(timeout=max(.01,min(10,deadline-time.monotonic())))
                need(upstream_code==0,'media download failed; partial transcript must be labeled')
        if len(buf)>keep or offset==0:
            buf=buf[:len(buf)//2*2]
            if buf:yield offset/32000,bytes(buf)
    finally:
        done.set()
        if timer:timer.cancel()
        for child in (process,upstream):
            if child is not None:stop_process(child)
        if process and process.stdout:process.stdout.close()
        if upstream and upstream.stdout:upstream.stdout.close()
        if thread:thread.join(timeout=1)

def transcribe(url,receipt,model_dir,start=0,duration=None,chunk=30,timeout=1200,language=None,model_path=None):
    consent(receipt)
    try:import numpy as np;from faster_whisper import WhisperModel
    except ImportError:raise ValueError('local dependencies missing; approved isolated install required; no API fallback')
    if model_path:
        local=Path(model_path).expanduser().resolve()
        need(local.is_dir() and (local/'model.bin').is_file() and (local/'config.json').is_file(),'select an existing faster-whisper/CTranslate2 model directory')
        model=WhisperModel(str(local),device='cpu',compute_type='int8',local_files_only=True)
    else:
        need(model_dir is not None,'approved model cache required')
        model=WhisperModel('base',device='cpu',compute_type='int8',download_root=str(model_dir))
    d=metadata(url);result={**safe_metadata(d,url),'origin':'faster-whisper/local-model/int8/cpu' if model_path else 'faster-whisper/base/int8/cpu','status':'transcribed','segments':[],'coverage':'selected interval' if duration or start else 'decoded stream','chunk_overlap_seconds':1,'notes':'Overlapping chunks may repeat words; timestamps use source clock. Not speaker diarization or audiovisual verification.'}
    began=time.monotonic()
    try:
        download,decode=audio_commands(url,start,duration)
        result['audio_selection']='yt-dlp bestaudio/best with native default language ranking; ASR language hint does not select a dubbed track'
        result['transport']='yt-dlp stdout -> FFmpeg stdin -> PCM chunks in memory'
        with closing(stream_chunks(decode,chunk,1,timeout,upstream_command=download,expected_seconds=duration)) as chunks:
            for offset,pcm in chunks:
                samples=np.frombuffer(pcm,dtype='<i2').astype(np.float32)/32768.0
                segments,info=model.transcribe(samples,language=language,beam_size=5,vad_filter=True)
                for seg in segments:result['segments'].append({'start':start+offset+seg.start,'end':start+offset+seg.end,'text':seg.text.strip()})
                need(time.monotonic()-began<timeout,'transcription runtime timeout')
    except Exception as e:
        result['status']='partial' if result['segments'] else 'failed';result['limit']=str(e) if isinstance(e,ValueError) else 'transcription/decoder failure'
    result['elapsed_seconds']=round(time.monotonic()-began,3);return result

def main():
    ap=argparse.ArgumentParser();subs=ap.add_subparsers(dest='mode',required=True)
    au=subs.add_parser('authorize');au.add_argument('--receipt',required=True);au.add_argument('--authorization-reference',required=True)
    st=subs.add_parser('status');st.add_argument('--receipt')
    cap=subs.add_parser('captions');cap.add_argument('url');cap.add_argument('--language',default='en')
    tr=subs.add_parser('transcribe');tr.add_argument('url');tr.add_argument('--receipt',required=True);models=tr.add_mutually_exclusive_group(required=True);models.add_argument('--model-dir');models.add_argument('--model-path');tr.add_argument('--start',type=float,default=0);tr.add_argument('--duration',type=float);tr.add_argument('--chunk-seconds',type=int,default=30);tr.add_argument('--timeout',type=int,default=1200);tr.add_argument('--language')
    fr=subs.add_parser('frame');fr.add_argument('url');fr.add_argument('--at',type=float,required=True)
    args=ap.parse_args()
    try:
        if args.mode=='authorize':result=authorize(args.receipt,args.authorization_reference)
        elif args.mode=='status':
            import importlib.util
            result={'yt_dlp':bool(shutil.which('yt-dlp')),'ffmpeg':bool(shutil.which('ffmpeg')),'faster_whisper':bool(importlib.util.find_spec('faster_whisper')),'numpy':bool(importlib.util.find_spec('numpy')),'model':'base','receipt_valid':False}
            if args.receipt:
                try:consent(args.receipt);result['receipt_valid']=True
                except Exception:pass
        elif args.mode=='captions':result=captions(args.url,args.language)
        elif args.mode=='transcribe':
            need(args.start>=0 and (args.duration is None or args.duration>0) and args.timeout>0,'invalid interval/timeout');result=transcribe(args.url,args.receipt,args.model_dir,args.start,args.duration,args.chunk_seconds,args.timeout,args.language,args.model_path)
        else:
            need(args.at>=0,'negative frame time');d=metadata(args.url);proc=subprocess.run(ffmpeg_command(d,args.at,frame=True),stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=60);need(proc.returncode==0 and proc.stdout,'frame unavailable');need(len(proc.stdout)<8*1024*1024,'frame too large');result={**safe_metadata(d,args.url),'at':args.at,'mime_type':'image/jpeg','base64':base64.b64encode(proc.stdout).decode()}
        print(json.dumps(result,ensure_ascii=False))
    except Exception as e:
        # Avoid leaking signed URLs or provider diagnostics. Known local validation errors are safe.
        message=str(e) if isinstance(e,ValueError) and 'http' not in str(e) else type(e).__name__+': media action unavailable'
        print(json.dumps({'status':'unavailable','reason':message}));sys.exit(1)
if __name__=='__main__':main()
