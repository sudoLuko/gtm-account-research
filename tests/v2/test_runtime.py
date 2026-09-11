import copy,hashlib,json,os,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(os.environ.get('GTM_V2_SKILL',Path(__file__).resolve().parents[2]/'gtm-account-research'));sys.path.insert(0,str(ROOT/'scripts'))
import validate,bundle,media

def put(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def fixture(root):
    # Synthetic explicit public-like fixture, not company claims or live research.
    source={'id':'S1','title':'Example employer role','url':'https://example.com/jobs/verification','author':None,'kind':'job','published_on':None,'publication_kind':'unknown','event_on':None,'retrieved_at':'2026-09-07T01:00:00Z','reviewed_at':'2026-09-07T01:05:00Z','date_notes':'No publication date visible.','path':'sources/S1.md','representation':'retained_text','derived_from':None,'correction_note':None,'extracted_coverage':'full','reviewed_coverage':'full','coverage_notes':'Fixture body reviewed.','action_ids':['A1']}
    e={'id':'E1','source_id':'S1','quote':'The role prepares test plans.','locator':{'line_start':2,'line_end':2,'description':'Role responsibilities','start_seconds':None,'end_seconds':None},'interpretation':'Advertised responsibility, not actual operation.','limits':'No installed tools or buyer established.','verification':{'status':'basic','notes':'Employer text attributed.','action_ids':['A1']}}
    claim={'id':'C1','text':'The job advert assigns test-plan preparation.','kind':'reported','evidence_ids':['E1'],'conflicting_evidence_ids':[],'limits':'Advertised only.'}
    a={'schema_version':'2.0','account_id':'example','research_as_of':'2026-09-06','research_timezone':'America/Los_Angeles','seller_profile':{'profile_id':'seller','revision':1,'sha256':'a'*64},'prospect':{'name':'Example','domain':'example.com'},'claims':[claim],'workflows':[{'id':'W1','title':'Test planning','scope':'Advertised role','step_claim_ids':['C1'],'connection_claim_ids':[]}],'assessment':{'disposition':'consider','rationale_claim_ids':['C1'],'limits':'No intent known.'},'unknowns':[]}
    dims={k:{'score':1,'evidence_ids':[],'question_ids':['Q1'],'basis':'No research yet.','change':'Baseline.','next_action':'Read role.'} for k in ['business','workflows','people_artifacts','existing_controls','seller_relevance','evidence_quality']}
    cp={'id':'K0','at':'2026-09-07T00:59:00Z','round_id':None,'dimensions':dims,'decision':'Investigate.'}
    cp2=copy.deepcopy(cp);cp2.update(id='K1',at='2026-09-07T01:06:00Z',round_id='R1',decision='Bounded stop.')
    for d in cp2['dimensions'].values():d.update(score=6,evidence_ids=['E1'],basis='Advertised work products known.',change='Specific responsibilities retained.',next_action='Reopen on new source.')
    log={'schema_version':'2.0','account_id':'example','actions':[{'id':'A1','at':'2026-09-07T01:00:00Z','question_ids':['Q1'],'tool':'fixture','request':'https://example.com/jobs/verification','outcome':'Body retained.','status':'success','source_ids':['S1'],'elapsed_seconds':None,'correction_of':None}],'questions':[{'id':'Q1','question':'Who prepares test plans?','parent_question_id':None,'source_ids':['S1'],'cue':'Role title.','expected_value':'Artifact ownership.','status':'answered','reason':'Advertised responsibility established.','next_action':None,'reopen_when':'Current actual-work example.'}],'rounds':[{'id':'R1','action_ids':['A1'],'finding_gain':'Role responsibility.','route_gain':'None.','verification_gain':'Employer attribution.','decision':'Question answered within advert scope.'}],'checkpoints':[cp,cp2],'final_assessment':{'status':'complete','coverage_review':'Synthetic single-question fixture only; no real account completeness claim.','unexplored':'Actual operating practice.','question_ids':[],'stop_reason':'Fixture scope answered.','reopen_when':'New evidence.'}}
    put(root/'account.json',a);put(root/'sources.json',{'schema_version':'2.0','account_id':'example','sources':[source],'evidence':[e]});put(root/'research-log.json',log)
    (root/'sources').mkdir(exist_ok=True);(root/'sources/S1.md').write_text('# Role\nThe role prepares test plans.\n');(root/'START_HERE.md').write_text('Synthetic fixture. Read account.json, sources.json and research-log.json.\n')
    return root
class Runtime(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=fixture(Path(self.tmp.name)/'run')
    def tearDown(self):self.tmp.cleanup()
    def edit(self,file,fn):p=self.root/file;d=validate.read(p);fn(d);put(p,d)
    def bad(self):self.assertRaises(ValueError,validate.run_check,self.root,True)
    def test_valid_timezone(self):validate.run_check(self.root,True)
    def test_quote_missing(self):self.edit('sources.json',lambda d:d['evidence'][0].update(quote='Invented quote'));self.bad()
    def test_whitespace_quote_rejected(self):
        for quote in [' ', '\t\n', '\u00a0']:
            with self.subTest(quote=repr(quote)):
                self.edit('sources.json',lambda d:d['evidence'][0].update(quote=quote));self.bad()
    def test_quote_whitespace_normalization_preserved(self):
        self.edit('sources.json',lambda d:d['evidence'][0].update(quote=' The  role\nprepares test plans. '))
        validate.run_check(self.root,True)
    def test_manifest_cannot_expand_export_scope(self):
        out=Path(self.tmp.name)/'bundle';bundle.export(self.root,out)
        (out/'seller-profile.json').write_text('Synthetic private seller context')
        m=validate.read(out/'manifest.json');m['files']['seller-profile.json']=validate.digest(out/'seller-profile.json');put(out/'manifest.json',m)
        with self.assertRaisesRegex(ValueError,'allowlist'):bundle.verify(out)
    def test_manifest_account_identity(self):
        out=Path(self.tmp.name)/'bundle';bundle.export(self.root,out)
        m=validate.read(out/'manifest.json');m['account_id']='different';put(out/'manifest.json',m)
        with self.assertRaisesRegex(ValueError,'account ID'):bundle.verify(out)
    def test_locator_wrong(self):self.edit('sources.json',lambda d:d['evidence'][0]['locator'].update(line_start=1,line_end=1));self.bad()
    def test_missing_claim_source(self):self.edit('account.json',lambda d:d['claims'][0].update(evidence_ids=['missing']));self.bad()
    def test_review_not_fetch(self):self.edit('sources.json',lambda d:d['sources'][0].update(reviewed_coverage='none'));self.bad()
    def test_future_local_capture(self):self.edit('sources.json',lambda d:d['sources'][0].update(retrieved_at='2026-09-08T01:00:00Z'));self.bad()
    def test_baseline_required(self):self.edit('research-log.json',lambda d:d['checkpoints'].pop(0));self.bad()
    def test_open_lead_not_complete(self):self.edit('research-log.json',lambda d:d['questions'][0].update(status='active',next_action='Inspect next source'));self.bad()
    def test_unknown_conflict_id(self):self.edit('account.json',lambda d:d['claims'][0].update(conflicting_evidence_ids=['fake']));self.bad()
    def test_path_escape(self):self.edit('sources.json',lambda d:d['sources'][0].update(path='sources/../../secret.md'));self.bad()
    def test_export_allowlist_and_relocation(self):
        (self.root/'seller-profile.json').write_text('PRIVATE SELLER SECRET')
        (self.root/'content.json').write_text('Legacy presentation content')
        (self.root/'report.pdf').write_bytes(b'Legacy PDF')
        out=Path(self.tmp.name)/'bundle';bundle.export(self.root,out);self.assertFalse((out/'seller-profile.json').exists());self.assertFalse((out/'content.json').exists());self.assertFalse((out/'report.pdf').exists())
        extracted=Path(self.tmp.name)/'moved'
        with zipfile.ZipFile(str(out)+'.zip') as z:z.extractall(extracted)
        bundle.verify(extracted)
    def test_tamper(self):
        out=Path(self.tmp.name)/'bundle';bundle.export(self.root,out);(out/'sources/S1.md').write_text('changed');self.assertRaises(ValueError,bundle.verify,out)
    def test_secret_url_blocks_export(self):
        with (self.root/'sources/S1.md').open('a') as f:f.write('https://example.com/a?token=secret\n')
        self.assertRaises(ValueError,bundle.export,self.root,Path(self.tmp.name)/'bundle')
    def test_schema_strict(self):self.edit('account.json',lambda d:d.update(garbage=True));self.bad()
    def test_duplicate_json(self):
        p=self.root/'bad.json';p.write_text('{"a":1,"a":2}');self.assertRaises(ValueError,validate.read,p)

    def test_linkedin_unknown_codecs(self):
        url,headers=media.selected_stream({'formats':[{'url':'https://example.com/video.mp4','ext':'mp4'}]})
        self.assertEqual(url,'https://example.com/video.mp4')
    def test_explicit_silent_video_not_audio(self):
        self.assertRaises(ValueError,media.selected_stream,{'formats':[{'url':'https://example.com/video.mp4','ext':'mp4','acodec':'none'}]})

    def test_manual_vtt(self):
        rows=media.parse_captions('WEBVTT\n\n00:01.000 --> 00:02.500\nTest &amp; verify.\n','vtt');self.assertEqual(rows,[{'start':1,'end':2.5,'text':'Test & verify.'}])
    def test_generated_json(self):self.assertEqual(media.parse_captions('{"events":[{"tStartMs":1000,"dDurationMs":2000,"segs":[{"utf8":"test"}]}]}','json3')[0]['end'],3)
    def test_missing_consent_no_model_import(self):self.assertRaises((FileNotFoundError,ValueError),media.transcribe,'https://example.com/video','/nonexistent-consent','/unused')
    def test_receipt_reuse(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'receipt.json';media.authorize(p,'Synthetic test approval, no actual install');media.consent(p);self.assertRaises(ValueError,media.authorize,p,'second')
    def test_chunks_bounded_offsets(self):
        cmd=[sys.executable,'-c','import sys;sys.stdout.buffer.write(bytes(32000*12))']
        chunks=list(media.stream_chunks(cmd,5,1,20));self.assertEqual([x[0] for x in chunks],[0,4,8]);self.assertLessEqual(max(len(x[1]) for x in chunks),160000)
    def test_decoder_failure(self):
        self.assertRaises(ValueError,list,media.stream_chunks([sys.executable,'-c','raise SystemExit(1)'],5,1,20))
if __name__=='__main__':unittest.main()
