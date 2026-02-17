#!/usr/bin/env python3
"""
History Future Now — Discussion Audio Renderer (Qwen3-TTS)

Renders discussion scripts to audio using Qwen3-TTS voice cloning.
Two voices: James (author's voice) and Elena (a designed/reference female voice).

This replaces the Gemini TTS renderer in generate_discussions.py with a
self-hosted solution — no API keys, no rate limits, no cost per request.

Prerequisites:
    - NVIDIA GPU with ≥6 GB VRAM
    - qwen-tts package installed: pip install -U qwen-tts
    - ffmpeg installed
    - Voice references in voice_reference/:
        - tristan.wav + tristan.txt  (James — author's voice)
        - elena.wav + elena.txt      (Elena — female voice)
      OR set ELENA_SPEAKER to use a built-in CustomVoice speaker

Usage:
    python3 generate_discussions_audio_qwen.py                    # Render all
    python3 generate_discussions_audio_qwen.py --article SLUG     # Render one
    python3 generate_discussions_audio_qwen.py --force            # Re-render all
    python3 generate_discussions_audio_qwen.py --dry-run          # Preview only
    python3 generate_discussions_audio_qwen.py --test             # Short test clip
"""

import os
import re
import io
import sys
import json
import time
import wave
import argparse
import subprocess
import tempfile
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

BASE_MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"

# Elena voice strategy: "clone" uses a reference clip, "builtin" uses CustomVoice
# Set to "builtin" if you don't have a female reference clip yet
ELENA_VOICE_MODE = os.environ.get("ELENA_VOICE_MODE", "clone")

# If using builtin mode, which CustomVoice speaker for Elena.
# Options: Vivian (Chinese), Serena (Chinese), Sohee (Korean), Ono_Anna (Japanese)
# None of these are native English speakers, so "clone" mode with a reference clip
# is strongly preferred.
ELENA_BUILTIN_SPEAKER = "Vivian"
CUSTOMVOICE_MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"

SCRIPTS_DIR = Path(__file__).parent / "discussion_scripts"
OUTPUT_DIR = Path(__file__).parent.parent / "hfn-site-output"
DISCUSSION_DIR = OUTPUT_DIR / "audio" / "discussions"

VOICE_REF_DIR = Path(__file__).parent / "voice_reference"
JAMES_REF_AUDIO = VOICE_REF_DIR / "tristan.wav"
JAMES_REF_TEXT = VOICE_REF_DIR / "tristan.txt"
ELENA_REF_AUDIO = VOICE_REF_DIR / "elena.wav"
ELENA_REF_TEXT = VOICE_REF_DIR / "elena.txt"

TTS_MAX_CHARS = 1500
SAMPLE_RATE = 24000

# ─── Audio Utilities ──────────────────────────────────────────────────────────

def numpy_to_wav(audio_array, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Convert a numpy float32 audio array to WAV bytes."""
    import numpy as np
    audio_int16 = (audio_array * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())
    return buf.getvalue()


def wav_to_mp3(wav_data: bytes) -> bytes:
    """Convert WAV to MP3 using ffmpeg."""
    result = subprocess.run(
        ['ffmpeg', '-y', '-i', 'pipe:0',
         '-codec:a', 'libmp3lame', '-b:a', '128k', '-f', 'mp3', 'pipe:1'],
        input=wav_data,
        capture_output=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {result.stderr.decode()[:500]}")
    return result.stdout


def concatenate_wav_segments(segments: list[bytes]) -> bytes:
    """Concatenate multiple WAV segments into one using ffmpeg."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_list = []
        for i, seg in enumerate(segments):
            seg_path = os.path.join(tmpdir, f"seg_{i:04d}.wav")
            with open(seg_path, 'wb') as f:
                f.write(seg)
            file_list.append(seg_path)

        list_path = os.path.join(tmpdir, "files.txt")
        with open(list_path, 'w') as f:
            for fp in file_list:
                f.write(f"file '{fp}'\n")

        output_path = os.path.join(tmpdir, "output.wav")
        result = subprocess.run(
            ['ffmpeg', '-y', '-f', 'concat', '-safe', '0',
             '-i', list_path, '-codec:a', 'pcm_s16le', output_path],
            capture_output=True, timeout=300,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg concat error: {result.stderr.decode()[:500]}")

        with open(output_path, 'rb') as f:
            return f.read()


# ─── Model Management ────────────────────────────────────────────────────────

_base_model = None
_custom_model = None
_james_prompt = None
_elena_prompt = None


def load_base_model():
    """Load the Base model for voice cloning."""
    global _base_model
    if _base_model is not None:
        return _base_model

    import torch
    from qwen_tts import Qwen3TTSModel

    attn_impl = "eager"
    try:
        import flash_attn  # noqa: F401
        attn_impl = "flash_attention_2"
    except ImportError:
        pass

    print(f"  Loading Base model: {BASE_MODEL_ID} (attention: {attn_impl})")
    _base_model = Qwen3TTSModel.from_pretrained(
        BASE_MODEL_ID,
        device_map="cuda:0",
        dtype=torch.bfloat16,
        attn_implementation=attn_impl,
    )
    return _base_model


def load_custom_model():
    """Load the CustomVoice model (only needed if Elena uses builtin speaker)."""
    global _custom_model
    if _custom_model is not None:
        return _custom_model

    import torch
    from qwen_tts import Qwen3TTSModel

    attn_impl = "eager"
    try:
        import flash_attn  # noqa: F401
        attn_impl = "flash_attention_2"
    except ImportError:
        pass

    print(f"  Loading CustomVoice model: {CUSTOMVOICE_MODEL_ID} (attention: {attn_impl})")
    _custom_model = Qwen3TTSModel.from_pretrained(
        CUSTOMVOICE_MODEL_ID,
        device_map="cuda:0",
        dtype=torch.bfloat16,
        attn_implementation=attn_impl,
    )
    return _custom_model


def get_james_prompt():
    """Get or create the cached voice clone prompt for James (author's voice)."""
    global _james_prompt
    if _james_prompt is not None:
        return _james_prompt

    model = load_base_model()

    if not JAMES_REF_AUDIO.exists():
        raise FileNotFoundError(
            f"James voice reference not found: {JAMES_REF_AUDIO}\n"
            f"This is the author's voice clip. See voice_reference/README.md."
        )

    ref_text = ""
    if JAMES_REF_TEXT.exists():
        ref_text = JAMES_REF_TEXT.read_text(encoding="utf-8").strip()

    if ref_text:
        _james_prompt = model.create_voice_clone_prompt(
            ref_audio=str(JAMES_REF_AUDIO),
            ref_text=ref_text,
        )
    else:
        _james_prompt = model.create_voice_clone_prompt(
            ref_audio=str(JAMES_REF_AUDIO),
            ref_text="",
            x_vector_only_mode=True,
        )
    print(f"  James voice prompt cached (from {JAMES_REF_AUDIO.name})")
    return _james_prompt


def get_elena_prompt():
    """Get or create the cached voice clone prompt for Elena."""
    global _elena_prompt
    if _elena_prompt is not None:
        return _elena_prompt

    if ELENA_VOICE_MODE == "clone":
        if not ELENA_REF_AUDIO.exists():
            raise FileNotFoundError(
                f"Elena voice reference not found: {ELENA_REF_AUDIO}\n"
                f"Either provide a female voice reference clip, or set\n"
                f"  export ELENA_VOICE_MODE=builtin\n"
                f"to use a built-in speaker instead."
            )

        model = load_base_model()
        ref_text = ""
        if ELENA_REF_TEXT.exists():
            ref_text = ELENA_REF_TEXT.read_text(encoding="utf-8").strip()

        if ref_text:
            _elena_prompt = model.create_voice_clone_prompt(
                ref_audio=str(ELENA_REF_AUDIO),
                ref_text=ref_text,
            )
        else:
            _elena_prompt = model.create_voice_clone_prompt(
                ref_audio=str(ELENA_REF_AUDIO),
                ref_text="",
                x_vector_only_mode=True,
            )
        print(f"  Elena voice prompt cached (cloned from {ELENA_REF_AUDIO.name})")
    else:
        _elena_prompt = "builtin"
        print(f"  Elena using built-in speaker: {ELENA_BUILTIN_SPEAKER}")

    return _elena_prompt


# ─── TTS Generation ──────────────────────────────────────────────────────────

def generate_turn_audio(speaker: str, text: str) -> bytes:
    """Generate WAV audio for a single discussion turn."""
    import numpy as np

    # Strip delivery cues like [dry], [emphatic] etc.
    text = re.sub(r'^\[[\w]+\]\s*', '', text.strip())
    if not text:
        return b''

    if speaker == "James":
        model = load_base_model()
        prompt = get_james_prompt()
        wavs, sr = model.generate_voice_clone(
            text=text,
            language="English",
            voice_clone_prompt=prompt,
        )
    elif speaker == "Elena" and ELENA_VOICE_MODE == "clone":
        model = load_base_model()
        prompt = get_elena_prompt()
        wavs, sr = model.generate_voice_clone(
            text=text,
            language="English",
            voice_clone_prompt=prompt,
        )
    else:
        # Elena with builtin speaker
        model = load_custom_model()
        wavs, sr = model.generate_custom_voice(
            text=text,
            language="English",
            speaker=ELENA_BUILTIN_SPEAKER,
        )

    audio_array = wavs[0]
    if not isinstance(audio_array, np.ndarray):
        audio_array = np.array(audio_array)

    peak = np.abs(audio_array).max()
    if peak > 1.0:
        audio_array = audio_array / peak

    return numpy_to_wav(audio_array, sr)


def add_silence(duration_ms: int = 300) -> bytes:
    """Generate a short silence WAV segment for natural pauses between turns."""
    import numpy as np
    n_samples = int(SAMPLE_RATE * duration_ms / 1000)
    silence = np.zeros(n_samples, dtype=np.float32)
    return numpy_to_wav(silence, SAMPLE_RATE)


# ─── Script Chunking ─────────────────────────────────────────────────────────

def chunk_turns_for_tts(script: list[dict], max_chars: int = TTS_MAX_CHARS) -> list[list[dict]]:
    """Group consecutive same-speaker turns, splitting long ones.
    Each chunk is rendered as a single TTS call."""
    chunks = []

    for turn in script:
        text = turn['text'].strip()
        speaker = turn['speaker']

        if len(text) <= max_chars:
            chunks.append([turn])
        else:
            # Split long turns at sentence boundaries
            sentences = re.split(r'(?<=[.!?])\s+', text)
            current_text = ""
            for sentence in sentences:
                if current_text and len(current_text) + len(sentence) + 1 > max_chars:
                    chunks.append([{'speaker': speaker, 'text': current_text.strip()}])
                    current_text = sentence
                else:
                    current_text = f"{current_text} {sentence}" if current_text else sentence
            if current_text.strip():
                chunks.append([{'speaker': speaker, 'text': current_text.strip()}])

    return chunks


# ─── Main Rendering ──────────────────────────────────────────────────────────

def render_script_to_audio(script: list[dict], output_path: Path) -> None:
    """Render a full discussion script to MP3."""
    total_chars = sum(len(t['text']) for t in script)
    print(f"    Rendering {len(script)} turns ({total_chars:,} chars)...")

    silence_between_turns = add_silence(400)
    silence_between_speakers = add_silence(600)

    wav_segments = []
    prev_speaker = None

    for i, turn in enumerate(script):
        speaker = turn['speaker']
        text = turn['text'].strip()
        if not text:
            continue

        # Add pause between turns
        if prev_speaker is not None:
            if speaker != prev_speaker:
                wav_segments.append(silence_between_speakers)
            else:
                wav_segments.append(silence_between_turns)

        label = "J" if speaker == "James" else "E"
        print(f"      [{i+1}/{len(script)}] {label}: {len(text)} chars", end="", flush=True)
        t0 = time.time()

        # Handle long turns by chunking
        if len(text) > TTS_MAX_CHARS:
            chunks = chunk_turns_for_tts([turn])
            for ci, chunk in enumerate(chunks):
                wav = generate_turn_audio(chunk[0]['speaker'], chunk[0]['text'])
                if wav:
                    wav_segments.append(wav)
        else:
            wav = generate_turn_audio(speaker, text)
            if wav:
                wav_segments.append(wav)

        elapsed = time.time() - t0
        print(f" ({elapsed:.1f}s)")
        prev_speaker = speaker

    if not wav_segments:
        raise RuntimeError("No audio segments generated")

    print(f"    Concatenating {len(wav_segments)} segments...")
    combined_wav = concatenate_wav_segments(wav_segments)
    final_mp3 = wav_to_mp3(combined_wav)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(final_mp3)

    total_mb = round(len(final_mp3) / (1024 * 1024), 2)
    total_audio_secs = (len(combined_wav) - 44) / (SAMPLE_RATE * 2)
    total_audio_mins = round(total_audio_secs / 60, 1)
    print(f"    Saved: {output_path.name} ({total_mb} MB, ~{total_audio_mins} min)")


def generate_test_clip():
    """Generate a short two-voice test clip."""
    print("=" * 60)
    print("TEST MODE: Two-voice discussion test clip")
    print("=" * 60)

    test_script = [
        {"speaker": "James", "text": "The Ottoman Empire ran a multinational state for six centuries. That's five centuries longer than the EU has managed so far."},
        {"speaker": "Elena", "text": "That's a rather generous comparison. The Ottomans held it together with military force and a millet system. The EU uses trade agreements and strongly worded letters."},
        {"speaker": "James", "text": "And yet the result is the same. Diverse populations, competing interests, a central bureaucracy trying to keep it all together."},
        {"speaker": "Elena", "text": "The difference is consent. Nobody voted to join the Ottoman Empire."},
        {"speaker": "James", "text": "Fair point. Though I wonder how many EU citizens feel they voted for what they actually got."},
    ]

    output_path = DISCUSSION_DIR / "test_discussion.mp3"
    render_script_to_audio(test_script, output_path)

    print()
    print(f"Test clip saved: {output_path}")
    print("Listen to verify both voices sound distinct and natural.")


def main():
    parser = argparse.ArgumentParser(
        description="Render discussion scripts to audio using Qwen3-TTS"
    )
    parser.add_argument("--article", type=str, help="Specific article slug")
    parser.add_argument("--force", action="store_true", help="Re-render existing audio")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--test", action="store_true", help="Generate a short test clip")
    args = parser.parse_args()

    import shutil
    if not shutil.which('ffmpeg'):
        print("ERROR: ffmpeg not found. Install with: sudo apt install ffmpeg")
        sys.exit(1)

    DISCUSSION_DIR.mkdir(parents=True, exist_ok=True)

    if args.test:
        generate_test_clip()
        return

    scripts = sorted(SCRIPTS_DIR.glob("*.json")) if SCRIPTS_DIR.exists() else []
    if not scripts:
        print(f"No discussion scripts found in {SCRIPTS_DIR}")
        print("Run: python3 generate_discussions.py scripts")
        sys.exit(1)

    if args.article:
        scripts = [s for s in scripts if args.article in s.stem]
        if not scripts:
            print(f"No script matching '{args.article}'")
            sys.exit(1)

    if args.dry_run:
        print(f"DRY RUN — {len(scripts)} discussion scripts")
        print(f"James voice: {JAMES_REF_AUDIO}")
        elena_desc = f"{ELENA_REF_AUDIO}" if ELENA_VOICE_MODE == "clone" else f"builtin:{ELENA_BUILTIN_SPEAKER}"
        print(f"Elena voice: {elena_desc}")
        print(f"Output: {DISCUSSION_DIR}")
        print()

        for sp in scripts:
            slug = sp.stem
            script = json.loads(sp.read_text(encoding='utf-8'))
            words = sum(len(t['text'].split()) for t in script)
            james_turns = sum(1 for t in script if t['speaker'] == 'James')
            elena_turns = sum(1 for t in script if t['speaker'] == 'Elena')
            exists = (DISCUSSION_DIR / f"{slug}.mp3").exists()
            status = "[exists]" if exists else "[pending]"
            print(f"  {status} {slug[:60]}: {len(script)} turns (J:{james_turns}/E:{elena_turns}), {words:,} words")
        return

    print(f"Discussion audio rendering: {len(scripts)} scripts")
    print(f"Model: {BASE_MODEL_ID}")
    print(f"James voice: {JAMES_REF_AUDIO}")
    elena_desc = f"{ELENA_REF_AUDIO}" if ELENA_VOICE_MODE == "clone" else f"builtin:{ELENA_BUILTIN_SPEAKER}"
    print(f"Elena voice: {elena_desc}")
    print(f"Output: {DISCUSSION_DIR}")
    print()

    generated = 0
    skipped = 0
    failed = 0

    for i, script_path in enumerate(scripts, 1):
        slug = script_path.stem
        output_path = DISCUSSION_DIR / f"{slug}.mp3"

        print(f"\n[{i}/{len(scripts)}] {slug[:60]}")

        if output_path.exists() and not args.force:
            print(f"  [skip] Audio already exists")
            skipped += 1
            continue

        try:
            script = json.loads(script_path.read_text(encoding='utf-8'))
            render_script_to_audio(script, output_path)
            generated += 1
        except Exception as e:
            print(f"  [FAILED] {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Done: {generated} generated, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    main()
