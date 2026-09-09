import json, shutil, subprocess, tempfile, unittest
from pathlib import Path
from scripts.run_media_job import JobError, execute

ROOT = Path(__file__).resolve().parents[1]

class MediaWorkerTests(unittest.TestCase):
    def test_demo_validates(self):
        with tempfile.TemporaryDirectory() as output:
            report=execute(ROOT/"examples/layer-c-demo.json",Path(output),True)
            self.assertEqual((report["status"],report["scene_count"]),("validated",2))

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); path=root/"job.json"
            path.write_text(json.dumps({"schema_version":1,"scenes":[{"type":"image","source":"../asset.jpg","duration":1}]}))
            with self.assertRaisesRegex(JobError,"escapes"): execute(path,root/"out",True)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"FFmpeg is not installed")
    def test_demo_renders_playable_mp4(self):
        with tempfile.TemporaryDirectory() as output:
            target=Path(output); report=execute(ROOT/"examples/layer-c-demo.json",target)
            self.assertTrue((target/"documentary.mp4").is_file())
            video=next(s for s in report["ffprobe"]["streams"] if s["codec_type"]=="video")
            self.assertEqual((video["width"],video["height"]),(1280,720)); self.assertEqual(len(report["sha256"]),64)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"FFmpeg is not installed")
    def test_audio_mix_and_subtitle_render(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name,frequency in (("voice.wav",440),("music.wav",220)):
                subprocess.run(["ffmpeg","-loglevel","error","-y","-f","lavfi","-i",f"sine=frequency={frequency}:duration=0.5",str(root/name)],check=True)
            (root/"captions.srt").write_text("1\n00:00:00,000 --> 00:00:00,800\nLayer C\n",encoding="utf-8")
            job={"schema_version":1,"output":{"filename":"mixed.mp4","width":640,"height":360,"fps":24,"preset":"veryfast"},"scenes":[{"type":"color","duration":1,"color":"#123456"}],"audio":{"narration":"voice.wav","music":"music.wav","music_volume":.1},"subtitles":"captions.srt"}
            manifest=root/"job.json"; manifest.write_text(json.dumps(job),encoding="utf-8")
            report=execute(manifest,root/"out")
            kinds={stream["codec_type"] for stream in report["ffprobe"]["streams"]}
            self.assertEqual(kinds,{"video","audio"})

if __name__ == "__main__": unittest.main()
