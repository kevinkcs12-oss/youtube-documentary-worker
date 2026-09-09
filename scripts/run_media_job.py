#!/usr/bin/env python3
"""Deterministic, offline Layer C documentary media assembly worker."""
from __future__ import annotations

import argparse, hashlib, json, math, shutil, subprocess, sys, tempfile, time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

class JobError(RuntimeError): pass

@dataclass(frozen=True)
class Settings:
    width: int; height: int; fps: int; crf: int; preset: str; sample_rate: int

def run(command: list[str], capture: bool = False) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, check=True, text=True,
            stdout=subprocess.PIPE if capture else None, stderr=subprocess.PIPE if capture else None)
    except FileNotFoundError as exc: raise JobError(f"Required executable not found: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise JobError(f"Command failed ({command[0]}): {detail[-2000:]}") from exc

def require(condition: bool, message: str) -> None:
    if not condition: raise JobError(message)

def number(value: Any, label: str, minimum: float, maximum: float) -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{label} must be a number")
    value = float(value)
    require(math.isfinite(value) and minimum <= value <= maximum, f"{label} must be between {minimum} and {maximum}")
    return value

def resolve_asset(value: Any, root: Path, label: str) -> Path:
    require(isinstance(value, str) and value.strip() and "\x00" not in value, f"{label} must be a valid path")
    path = (root / value).resolve()
    try: path.relative_to(root)
    except ValueError as exc: raise JobError(f"{label} escapes the job directory: {value}") from exc
    require(path.is_file(), f"{label} does not exist: {value}")
    return path

def load_job(path: Path) -> tuple[dict[str, Any], Path]:
    require(path.is_file(), f"Job manifest not found: {path}")
    try: job = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: raise JobError(f"Cannot read job manifest: {exc}") from exc
    require(isinstance(job, dict), "Job manifest root must be an object")
    require(job.get("schema_version") == 1, "schema_version must be 1")
    return job, path.resolve().parent

def validate(job: dict[str, Any], root: Path) -> tuple[Settings, list[dict[str, Any]]]:
    output = job.get("output", {}); require(isinstance(output, dict), "output must be an object")
    width = int(number(output.get("width", 1920), "output.width", 320, 3840))
    height = int(number(output.get("height", 1080), "output.height", 240, 2160))
    require(width % 2 == 0 and height % 2 == 0, "output dimensions must be even")
    settings = Settings(width, height, int(number(output.get("fps", 30), "output.fps", 1, 60)),
        int(number(output.get("crf", 20), "output.crf", 0, 40)), str(output.get("preset", "medium")),
        int(number(output.get("sample_rate", 48000), "output.sample_rate", 8000, 96000)))
    require(settings.preset in {"ultrafast","superfast","veryfast","faster","fast","medium","slow","slower"}, "output.preset is not supported")
    scenes = job.get("scenes"); require(isinstance(scenes, list) and scenes, "scenes must be a non-empty array")
    require(len(scenes) <= 500, "scenes cannot contain more than 500 items")
    total = 0.0
    for i, scene in enumerate(scenes):
        label=f"scenes[{i}]"; require(isinstance(scene, dict), f"{label} must be an object")
        kind=scene.get("type"); require(kind in {"video","image","color"}, f"{label}.type must be video, image, or color")
        total += number(scene.get("duration"), f"{label}.duration", .1, 3600)
        if kind in {"video","image"}: resolve_asset(scene.get("source"), root, f"{label}.source")
        if "fit" in scene: require(scene["fit"] in {"contain","cover"}, f"{label}.fit must be contain or cover")
        if "start" in scene: number(scene["start"], f"{label}.start", 0, 86400)
        if kind == "color": require(isinstance(scene.get("color", "#111111"), str) and len(scene.get("color", "#111111")) <= 32, f"{label}.color is invalid")
    require(total <= 21600, "timeline cannot exceed six hours")
    audio=job.get("audio", {}); require(isinstance(audio, dict), "audio must be an object")
    for key in ("narration","music"):
        if key in audio: resolve_asset(audio[key], root, f"audio.{key}")
    if "music_volume" in audio: number(audio["music_volume"], "audio.music_volume", 0, 2)
    if "subtitles" in job: resolve_asset(job["subtitles"], root, "subtitles")
    return settings, scenes

def video_filter(s: Settings, fit: str = "contain") -> str:
    if fit == "cover":
        framing = (
            f"scale={s.width}:{s.height}:force_original_aspect_ratio=increase,"
            f"crop={s.width}:{s.height}"
        )
    else:
        framing = (
            f"scale={s.width}:{s.height}:force_original_aspect_ratio=decrease,"
            f"pad={s.width}:{s.height}:(ow-iw)/2:(oh-ih)/2:color=black"
        )
    return f"tpad=stop_mode=clone:stop_duration=3600,{framing},fps={s.fps},format=yuv420p,setsar=1"

def render_scene(scene: dict[str, Any], i: int, root: Path, target: Path, s: Settings) -> None:
    kind=scene["type"]
    if kind == "color": source=["-f","lavfi","-i",f"color=c={scene.get('color','#111111')}:s={s.width}x{s.height}:r={s.fps}"]
    elif kind == "image": source=["-loop","1","-i",str(resolve_asset(scene["source"],root,f"scenes[{i}].source"))]
    else:
        source=[]
        if scene.get("start") is not None: source += ["-ss",str(float(scene["start"]))]
        source += ["-i",str(resolve_asset(scene["source"],root,f"scenes[{i}].source"))]
    run(["ffmpeg","-hide_banner","-loglevel","error","-y",*source,"-t",str(float(scene["duration"])),"-an","-vf",video_filter(s, str(scene.get("fit","contain"))),"-c:v","libx264","-preset",s.preset,"-crf",str(s.crf),"-pix_fmt","yuv420p",str(target)])

def concat_scenes(paths: list[Path], target: Path) -> None:
    listing=target.with_suffix(".txt"); listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in paths),encoding="utf-8")
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(listing),"-c","copy",str(target)])

def finish_video(base: Path, target: Path, job: dict[str, Any], root: Path, s: Settings, duration: float) -> None:
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(base)]; audio=job.get("audio",{}); labels=[]; filters=[]; n=1
    if "narration" in audio:
        cmd += ["-i",str(resolve_asset(audio["narration"],root,"audio.narration"))]; filters.append(f"[{n}:a]aresample={s.sample_rate},apad,atrim=0:{duration}[narration]"); labels.append("[narration]"); n+=1
    if "music" in audio:
        cmd += ["-stream_loop","-1","-i",str(resolve_asset(audio["music"],root,"audio.music"))]; filters.append(f"[{n}:a]aresample={s.sample_rate},volume={float(audio.get('music_volume',.15))},atrim=0:{duration}[music]"); labels.append("[music]")
    if len(labels)==2: filters.append("".join(labels)+"amix=inputs=2:duration=longest:normalize=0[aout]")
    subtitles=resolve_asset(job["subtitles"],root,"subtitles") if "subtitles" in job else None
    if subtitles:
        escaped=str(subtitles).replace("\\","\\\\").replace(":","\\:").replace("'","\\'"); cmd += ["-vf",f"subtitles='{escaped}'"]
    if filters: cmd += ["-filter_complex",";".join(filters)]
    cmd += ["-map","0:v:0"]
    if labels: cmd += ["-map","[aout]" if len(labels)==2 else labels[0],"-c:a","aac","-b:a","192k","-ar",str(s.sample_rate)]
    cmd += ["-c:v","libx264" if subtitles else "copy"]
    if subtitles: cmd += ["-preset",s.preset,"-crf",str(s.crf),"-pix_fmt","yuv420p"]
    cmd += ["-t",str(duration),"-movflags","+faststart",str(target)]; run(cmd)

def sha256(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1048576),b""): digest.update(chunk)
    return digest.hexdigest()

def probe(path: Path) -> dict[str, Any]:
    result=run(["ffprobe","-v","error","-show_entries","format=duration,size,format_name:stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate","-of","json",str(path)],True)
    return json.loads(result.stdout)

def execute(job_path: Path, output_dir: Path, validate_only: bool=False) -> dict[str, Any]:
    job,root=load_job(job_path); settings,scenes=validate(job,root); output_dir.mkdir(parents=True,exist_ok=True); report_path=output_dir/"layer-c-report.json"
    if validate_only:
        report={"status":"validated","schema_version":1,"scene_count":len(scenes)}; report_path.write_text(json.dumps(report,indent=2)+"\n"); return report
    for executable in ("ffmpeg","ffprobe"): require(shutil.which(executable) is not None,f"{executable} is required")
    started=time.time(); name=job.get("output",{}).get("filename","documentary.mp4")
    require(isinstance(name,str) and Path(name).name==name and name.endswith(".mp4"),"output.filename must be a plain .mp4 filename")
    target=output_dir/name; duration=sum(float(x["duration"]) for x in scenes)
    with tempfile.TemporaryDirectory(prefix="layer-c-") as td:
        temp=Path(td); rendered=[]
        for i,scene in enumerate(scenes):
            path=temp/f"scene-{i:04d}.mp4"; render_scene(scene,i,root,path,settings); rendered.append(path)
        base=temp/"timeline.mp4"; concat_scenes(rendered,base); finish_video(base,target,job,root,settings,duration)
    report={"status":"completed","schema_version":1,"worker":"layer-c","output":target.name,"sha256":sha256(target),"scene_count":len(scenes),"requested_duration_seconds":duration,"elapsed_seconds":round(time.time()-started,3),"ffprobe":probe(target)}
    report_path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n"); return report

def main() -> int:
    parser=argparse.ArgumentParser(description="Render a Layer C documentary media job"); parser.add_argument("--job",type=Path,required=True); parser.add_argument("--output-dir",type=Path,default=Path("dist")); parser.add_argument("--validate-only",action="store_true"); args=parser.parse_args()
    try: print(json.dumps(execute(args.job.resolve(),args.output_dir.resolve(),args.validate_only),indent=2,sort_keys=True)); return 0
    except JobError as exc: print(f"Layer C job failed: {exc}",file=sys.stderr); return 2

if __name__ == "__main__": raise SystemExit(main())
