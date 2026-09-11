import io,os,shutil,struct,subprocess,sys,tempfile,time,unittest,wave
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]/'gtm-account-research'
sys.path.insert(0,str(ROOT/'scripts'))
import media

class NativePipeline(unittest.TestCase):
    def track_processes(self):
        made=[];real=subprocess.Popen
        def create(*a,**kw):
            p=real(*a,**kw);made.append(p);return p
        return made,patch.object(media.subprocess,'Popen',side_effect=create)

    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg required for real pipe/seek check')
    def test_real_decoder_seek_and_overlap(self):
        # Real native pipe layout, synthetic WAV in RAM. Compare exact samples
        # so an input/output seek mix-up or offset drift cannot pass by shape.
        producer=[sys.executable,'-c',"import io,wave,struct,sys; b=io.BytesIO(); w=wave.open(b,'wb'); w.setparams((1,2,16000,0,'NONE','not compressed')); w.writeframes(b''.join(struct.pack('<h',i%30001-15000) for i in range(320000))); w.close(); sys.stdout.buffer.write(b.getvalue())"]
        _,decode=media.audio_commands('https://example.com/video',2,12)
        made,track=self.track_processes()
        with track:chunks=list(media.stream_chunks(decode,5,1,15,producer,12))
        self.assertEqual([a for a,_ in chunks],[0,4,8])
        joined=chunks[0][1]+b''.join(b[32000:] for _,b in chunks[1:])
        expected=b''.join(struct.pack('<h',i%30001-15000) for i in range(32000,224000))
        self.assertEqual(joined,expected)
        self.assertTrue(all(p.poll() is not None for p in made))

    def test_download_failure_not_successful_eof(self):
        producer=[sys.executable,'-c','raise SystemExit(7)']
        decoder=[sys.executable,'-c','import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())']
        made,track=self.track_processes()
        with track,self.assertRaises(ValueError):list(media.stream_chunks(decoder,5,1,5,producer))
        self.assertTrue(all(p.poll() is not None for p in made))

    def test_failure_after_partial_chunks_is_not_complete(self):
        producer=[sys.executable,'-c','import sys;sys.stdout.buffer.write(bytes(32000*7));sys.stdout.buffer.flush();raise SystemExit(7)']
        decoder=[sys.executable,'-c','import sys;sys.stdout.buffer.write(sys.stdin.buffer.read())']
        chunks=media.stream_chunks(decoder,5,1,5,producer)
        self.assertEqual(len(next(chunks)[1]),160000)
        with self.assertRaisesRegex(ValueError,'download failed'):list(chunks)

    def test_timeout_reaps_both_processes(self):
        producer=[sys.executable,'-c','import time;time.sleep(30)']
        decoder=[sys.executable,'-c','import sys;sys.stdout.buffer.write(sys.stdin.buffer.read())']
        made,track=self.track_processes();start=time.monotonic()
        with track,self.assertRaises(ValueError):list(media.stream_chunks(decoder,5,1,.3,producer))
        self.assertLess(time.monotonic()-start,5)
        self.assertTrue(all(p.poll() is not None for p in made))

    def test_consumer_abort_reaps_both(self):
        producer=[sys.executable,'-c','import sys,time;sys.stdout.buffer.write(bytes(32000*7));sys.stdout.buffer.flush();time.sleep(30)']
        decoder=[sys.executable,'-u','-c',"import sys\nwhile True:\n b=sys.stdin.buffer.read(32000)\n if not b:break\n sys.stdout.buffer.write(b);sys.stdout.buffer.flush()"]
        made,track=self.track_processes()
        with track:
            chunks=media.stream_chunks(decoder,5,1,5,producer)
            next(chunks);chunks.close()
        self.assertTrue(all(p.poll() is not None for p in made))

    def test_decoder_launch_failure_reaps_producer(self):
        made,track=self.track_processes()
        with track,self.assertRaises(FileNotFoundError):
            list(media.stream_chunks(['/nonexistent-decoder'],5,1,5,[sys.executable,'-c','import time;time.sleep(30)']))
        self.assertTrue(all(p.poll() is not None for p in made))

    def test_completed_interval_allows_producer_cutoff(self):
        producer=[sys.executable,'-c','import time;time.sleep(30)']
        decoder=[sys.executable,'-c','import sys;sys.stdout.buffer.write(bytes(32000*5))']
        made,track=self.track_processes()
        with track:chunks=list(media.stream_chunks(decoder,5,1,5,producer,5))
        self.assertEqual(len(chunks),1)
        self.assertTrue(all(p.poll() is not None for p in made))

if __name__=='__main__':unittest.main()
