import argparse,copy,json,os,sys,tempfile,unittest,zipfile,types
from pathlib import Path
from unittest.mock import patch,Mock
SKILL=Path(os.environ.get('GTM_V2_SKILL',Path(__file__).resolve().parents[2]/'gtm-account-research'))
sys.path.insert(0,str(SKILL/'scripts'));sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v2'))
import qa,bundle,media
from test_runtime import fixture
class QA(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name);self.run=fixture(self.p/'run');self.out=self.p/'bundle';bundle.export(self.run,self.out)
 def tearDown(self):self.tmp.cleanup()
 def call(self,cmd,**kw):
  args=argparse.Namespace(bundle=str(self.out),cache=str(self.p/'cache'),max_chars=2000,offset=0,command=cmd,id='S1',start=1,end=None,section=False,query='test plans',plain=False,keep_duplicates=False)
  for k,v in kw.items():setattr(args,k,v)
  v=qa.answer(args);self.assertLessEqual(len(qa.encoded(v)),args.max_chars);return v
 def test_verified_identity_and_catalog(self):
  self.assertEqual(self.call('overview')['account_id'],'example');self.assertEqual(self.call('catalog')['items'][0]['id'],'S1')
 def test_lexical_raw_and_curated(self):
  r=self.call('search');self.assertEqual(r['engine'],'fts5_bm25');self.assertTrue(r['items'])
 def test_plain_fallback(self):self.assertEqual(self.call('search',plain=True)['engine'],'plain')
 def test_unavailable_fts_falls_back(self):
  with patch.object(qa.sqlite3,'connect',side_effect=qa.sqlite3.OperationalError('missing module')):self.assertEqual(self.call('search')['engine'],'plain')
 def test_tampered_source_rejected(self):
  (self.out/'sources/S1.md').write_text('tampered');self.assertRaises(ValueError,self.call,'search')
 def test_cache_inside_bundle_rejected(self):self.assertRaises(ValueError,self.call,'catalog',cache=str(self.out/'cache'))
 def test_zip_roundtrip(self):self.assertEqual(self.call('catalog',bundle=str(self.out)+'.zip')['account_id'],'example')
 def test_zip_escape_rejected(self):
  z=self.p/'bad.zip'
  with zipfile.ZipFile(z,'w') as f:f.writestr('../escape.txt','bad')
  self.assertRaises(ValueError,self.call,'catalog',bundle=str(z));self.assertFalse((self.p/'escape.txt').exists())
 def test_record_char_pagination_roundtrip(self):
  root,a,s,r,fp=qa.load(self.out,self.p/'cache');r['unknowns']='x' # actual exported records tested below
  expected=json.dumps(qa.load(self.out,self.p/'cache')[3]['evidence:E1'],indent=2,ensure_ascii=False);parts=[];offset=0
  while True:
   v=self.call('record',id='evidence:E1',offset=offset);parts.append(v['text'])
   if v['next_offset'] is None:break
   self.assertGreater(v['next_offset'],offset);offset=v['next_offset']
  self.assertEqual(''.join(parts),expected)
 def test_long_line_pagination_no_loss(self):
  long='"\\'*3000;f=self.run/'sources/S1.md';f.write_text(f.read_text()+'\n'+long+'\n');new=self.p/'long';bundle.export(self.run,new)
  n=len((new/'sources/S1.md').read_text().splitlines());offset=0;parts=[]
  while True:
   v=self.call('read',bundle=str(new),start=n,end=n,offset=offset);parts.extend(x['text'] for x in v['items'])
   if v['next_offset'] is None:break
   self.assertGreater(v['next_offset'],offset);offset=v['next_offset']
  self.assertEqual(''.join(parts),long)
 def test_raw_only_fact_retrievable(self):
  f=self.run/'sources/S1.md';f.write_text(f.read_text()+'\n## Unselected\nThe calibration marker is CERULEAN-731.\n');new=self.p/'raw';bundle.export(self.run,new)
  v=self.call('search',bundle=str(new),query='CERULEAN');self.assertTrue(any(x.get('source_id')=='S1' for x in v['items']))
 def test_new_valid_bundle_rebuilds_index(self):
  one=self.call('search');f=self.run/'sources/S1.md';f.write_text(f.read_text()+'\nNew sentinel CERULEAN\n');new=self.p/'new';bundle.export(self.run,new)
  two=self.call('search',bundle=str(new),query='CERULEAN');self.assertNotEqual(one['bundle_fingerprint'],two['bundle_fingerprint']);self.assertEqual(two['index_state'],'rebuilt')
 def test_corrupt_index_fallback(self):
  self.call('search');f=next((self.p/'cache/indices').glob('*.sqlite'));f.write_bytes(b'bad index');v=self.call('search');self.assertIn(v['engine'],['plain','fts5_bm25']);self.assertTrue(v['items'])
 def test_missing_source_and_bad_start(self):
  self.assertRaises(KeyError,self.call,'read',id='absent');self.assertRaises(ValueError,self.call,'read',start=999)
 def test_duplicate_group_keeps_origin(self):
  root,a,s,r,fp=qa.load(self.out,self.p/'cache');original=qa.chunks(root,s,r);d=copy.deepcopy(next(x for x in original if 'source_id' in x));d['source_id']='S2';s['S2']=s['S1'];docs=[d,dict(d,source_id='S1')]
  with patch.object(qa,'load',return_value=(root,a,s,r,fp)),patch.object(qa,'index',return_value=(docs,None,'plain_requested')):
   v=self.call('search',plain=True);self.assertEqual(len(v['items']),1);self.assertEqual(v['items'][0]['duplicate_sources'][0]['source_id'],'S1')
   v=self.call('search',plain=True,keep_duplicates=True);self.assertEqual(len(v['items']),2)
class Reuse(unittest.TestCase):
 def test_local_model_no_download(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);(p/'model.bin').write_bytes(b'fixture');(p/'config.json').write_text('{}');receipt=p/'receipt.json';media.authorize(receipt,'synthetic authorized test fixture')
   factory=Mock();fake=types.ModuleType('faster_whisper');fake.WhisperModel=factory
   with patch.dict(sys.modules,{'faster_whisper':fake,'numpy':types.ModuleType('numpy')}),patch.object(media,'metadata',return_value={}),patch.object(media,'audio_commands',return_value=([],[])),patch.object(media,'stream_chunks',return_value=(x for x in [])):
    result=media.transcribe('https://example.com/video',receipt,None,model_path=str(p))
   self.assertTrue(factory.call_args.kwargs['local_files_only']);self.assertNotIn('download_root',factory.call_args.kwargs);self.assertEqual(result['origin'],'faster-whisper/local-model/int8/cpu')
if __name__=='__main__':unittest.main()
