#!/usr/bin/env python3
"""
History Future Now — Audio Narration Generator (Qwen3-TTS Voice Clone)

Generates MP3 narrations for all essays using Qwen3-TTS-12Hz-1.7B-Base,
cloning the author's voice from a short reference audio clip.

The author (Tristan Fischer) reads his own articles — single voice, authentic,
no more generic Google Cloud TTS voices.

Prerequisites:
    - NVIDIA GPU with ≥6 GB VRAM (8+ GB recommended)
    - qwen-tts package installed: pip install -U qwen-tts
    - ffmpeg installed
    - flash-attn installed (optional but recommended):
        pip install -U flash-attn --no-build-isolation
    - Voice reference clip at voice_reference/tristan.wav
    - Transcript of the clip at voice_reference/tristan.txt

Usage:
    python3 generate_audio_qwen.py                    # Generate all missing audio
    python3 generate_audio_qwen.py --article SLUG     # Generate for one article
    python3 generate_audio_qwen.py --force            # Regenerate all (overwrite)
    python3 generate_audio_qwen.py --dry-run          # Preview without loading model
    python3 generate_audio_qwen.py --test             # Generate 30s test clip only

Models:
    - Qwen/Qwen3-TTS-12Hz-1.7B-Base     (voice cloning from reference audio)
    - Qwen/Qwen3-TTS-Tokenizer-12Hz     (speech tokeniser, auto-downloaded)

The model weights are downloaded automatically on first run (~3.5 GB).
"""

import os
import re
import io
import sys
import json
import time
import wave
import yaml
import argparse
import subprocess
import tempfile
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"

ESSAYS_DIR = Path(__file__).parent / "essays"
OUTPUT_DIR = Path(__file__).parent.parent / "hfn-site-output"
AUDIO_DIR = OUTPUT_DIR / "audio"

VOICE_REF_DIR = Path(__file__).parent / "voice_reference"
VOICE_REF_AUDIO = VOICE_REF_DIR / "tristan.wav"
VOICE_REF_TEXT = VOICE_REF_DIR / "tristan.txt"

# Max characters per TTS generation call.
# Qwen3-TTS supports up to ~8192 tokens output, but shorter chunks produce
# more consistent quality. At ~12 tokens/sec and ~150 wpm, 1500 chars ≈ 60s
# of audio — a good balance between quality and throughput.
TTS_MAX_CHARS = 1500

# Sample rate output by Qwen3-TTS
SAMPLE_RATE = 24000


# ─── Text Extraction (shared with generate_audio.py) ─────────────────────────

def fix_encoding(text: str) -> str:
    replacements = {
        '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '--', '\u2026': '...',
        '\xa0': ' ', '\u00a3': 'pounds ', '\u20ac': 'euros ',
        'â\x80\x99': "'", 'â\x80\x98': "'", 'â\x80\x9c': '"', 'â\x80\x9d': '"',
        'â\x80\x93': '--', 'â\x80\x94': '-', 'â\x80\xa6': '...', 'Â ': ' ', 'Â': '',
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text


def extract_narration_text(filepath: Path) -> tuple[str, str, str]:
    """Extract clean narration text from a markdown essay."""
    content = filepath.read_text(encoding="utf-8", errors="replace")

    meta = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                meta = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                meta = {}
            body = parts[2]

    body = fix_encoding(body)

    title = meta.get("title", filepath.stem.replace("-", " ").title())
    title = re.sub(r"</?strong>", "", title).replace("&nbsp;", " ").replace("\xa0", " ").strip()

    slug = meta.get("slug", filepath.stem)
    slug = slug.replace("strong", "").replace("nbsp", "").strip("-")
    slug = re.sub(r"-+", "-", slug)

    body = re.sub(r"^\s*#\s+[^\n]+\n", "", body, count=1)
    body = re.sub(r"\n---\s*\n\s*##\s*THEN:.*$", "", body, flags=re.DOTALL)
    body = re.sub(r"\n##\s*References\s*\n.*$", "", body, flags=re.DOTALL)

    text = body
    text = re.sub(r"^#{1,6}\s+(.+)$", r"\n\1.\n", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()

    narration = f"{title}.\n\nBy Tristan Fischer.\n\n{text}"
    return title, slug, narration


# ─── Section Splitting ────────────────────────────────────────────────────────

def split_into_chunks(narration: str, max_chars: int = TTS_MAX_CHARS) -> list[str]:
    """Split narration into chunks that fit within TTS character limits.
    Splits at paragraph boundaries, then at sentence boundaries if needed."""
    paragraphs = re.split(r'\n\n+', narration)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks = []
    buffer = ""

    for para in paragraphs:
        if not buffer:
            buffer = para
        elif len(buffer) + len(para) + 2 <= max_chars:
            buffer += "\n\n" + para
        else:
            chunks.append(buffer)
            buffer = para

    if buffer:
        chunks.append(buffer)

    # Second pass: split any chunks that still exceed max_chars at sentence boundaries
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_chars:
            final_chunks.append(chunk)
            continue

        sentences = re.split(r'(?<=[.!?])\s+', chunk)
        current = ""
        for sentence in sentences:
            if current and len(current) + len(sentence) + 1 > max_chars:
                final_chunks.append(current.strip())
                current = sentence
            else:
                current = f"{current} {sentence}" if current else sentence
        if current.strip():
            final_chunks.append(current.strip())

    return final_chunks


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


# ─── Qwen3-TTS Model ─────────────────────────────────────────────────────────

_model = None
_voice_prompt = None


def load_model():
    """Load the Qwen3-TTS model. Called once, cached globally."""
    global _model
    if _model is not None:
        return _model

    import torch
    from qwen_tts import Qwen3TTSModel

    print(f"Loading model: {MODEL_ID}")
    print(f"  Device: cuda:0")

    # Check for flash-attn availability
    attn_impl = "eager"
    try:
        import flash_attn  # noqa: F401
        attn_impl = "flash_attention_2"
        print(f"  Attention: flash_attention_2")
    except ImportError:
        print(f"  Attention: eager (install flash-attn for faster inference)")

    _model = Qwen3TTSModel.from_pretrained(
        MODEL_ID,
        device_map="cuda:0",
        dtype=torch.bfloat16,
        attn_implementation=attn_impl,
    )

    print(f"  Model loaded successfully")
    return _model


def load_voice_prompt():
    """Load and cache the voice clone prompt from the reference audio.
    Computed once, reused across all generations."""
    global _voice_prompt
    if _voice_prompt is not None:
        return _voice_prompt

    model = load_model()

    if not VOICE_REF_AUDIO.exists():
        raise FileNotFoundError(
            f"Voice reference audio not found: {VOICE_REF_AUDIO}\n"
            f"Record a 10-30 second clip of your voice and save it as:\n"
            f"  {VOICE_REF_AUDIO}\n"
            f"See voice_reference/README.md for instructions."
        )

    ref_text = ""
    if VOICE_REF_TEXT.exists():
        ref_text = VOICE_REF_TEXT.read_text(encoding="utf-8").strip()
        print(f"  Voice reference: {VOICE_REF_AUDIO.name} ({len(ref_text)} chars transcript)")
    else:
        print(f"  Voice reference: {VOICE_REF_AUDIO.name} (no transcript — using x-vector only)")

    if ref_text:
        _voice_prompt = model.create_voice_clone_prompt(
            ref_audio=str(VOICE_REF_AUDIO),
            ref_text=ref_text,
            x_vector_only_mode=False,
        )
    else:
        _voice_prompt = model.create_voice_clone_prompt(
            ref_audio=str(VOICE_REF_AUDIO),
            ref_text="",
            x_vector_only_mode=True,
        )

    print(f"  Voice clone prompt cached")
    return _voice_prompt


def generate_chunk_audio(text: str) -> bytes:
    """Generate WAV audio for a single text chunk using the cloned voice.
    Returns WAV bytes."""
    import numpy as np

    model = load_model()
    voice_prompt = load_voice_prompt()

    wavs, sr = model.generate_voice_clone(
        text=text,
        language="English",
        voice_clone_prompt=voice_prompt,
    )

    audio_array = wavs[0]
    if not isinstance(audio_array, np.ndarray):
        audio_array = np.array(audio_array)

    # Normalise if needed
    peak = np.abs(audio_array).max()
    if peak > 1.0:
        audio_array = audio_array / peak

    return numpy_to_wav(audio_array, sr)


# ─── Main Generation ─────────────────────────────────────────────────────────

def generate_article_audio(filepath: Path, force: bool = False) -> bool:
    """Generate audio narration using the author's cloned voice."""
    title, slug, narration = extract_narration_text(filepath)
    output_path = AUDIO_DIR / f"{slug}.mp3"

    if output_path.exists() and not force:
        print(f"  [skip] {slug} (already exists)")
        return False

    word_count = len(narration.split())
    char_count = len(narration)
    est_minutes = round(word_count / 160, 1)

    print(f"  [{slug}]")
    print(f"    {word_count:,} words, {char_count:,} chars, ~{est_minutes} min estimated")

    chunks = split_into_chunks(narration)
    print(f"    {len(chunks)} chunks")

    wav_segments = []
    for i, chunk in enumerate(chunks):
        print(f"    [{i+1}/{len(chunks)}] {len(chunk):,} chars", end="", flush=True)
        t0 = time.time()

        wav_data = generate_chunk_audio(chunk)
        wav_segments.append(wav_data)

        elapsed = time.time() - t0
        # Estimate duration from WAV size: 24000 Hz * 2 bytes * 1 channel
        audio_secs = (len(wav_data) - 44) / (SAMPLE_RATE * 2)
        rtf = elapsed / audio_secs if audio_secs > 0 else 0
        print(f" → {audio_secs:.1f}s audio in {elapsed:.1f}s (RTF {rtf:.2f})")

    # Concatenate all WAV segments, then convert to MP3
    print(f"    Concatenating {len(wav_segments)} segments...")
    combined_wav = concatenate_wav_segments(wav_segments)
    final_mp3 = wav_to_mp3(combined_wav)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(final_mp3)

    total_mb = round(len(final_mp3) / (1024 * 1024), 2)
    total_audio_secs = (len(combined_wav) - 44) / (SAMPLE_RATE * 2)
    total_audio_mins = round(total_audio_secs / 60, 1)
    print(f"    Saved: {output_path.name} ({total_mb} MB, ~{total_audio_mins} min)")
    return True


def generate_test_clip():
    """Generate a short test clip to verify voice quality before full batch."""
    print("=" * 60)
    print("TEST MODE: Generating a short clip to verify voice quality")
    print("=" * 60)

    test_text = (
        "History does not repeat, but it rhymes. The patterns that shaped "
        "the rise and fall of civilisations — from Rome to the Ottoman Empire, "
        "from the British Empire to the European Union — are playing out again "
        "in our own time. The question is not whether these patterns will "
        "reassert themselves, but whether we have the wisdom to recognise them "
        "before it is too late."
    )

    print(f"\nTest text ({len(test_text)} chars):")
    print(f"  \"{test_text[:80]}...\"")
    print()

    t0 = time.time()
    wav_data = generate_chunk_audio(test_text)
    elapsed = time.time() - t0

    audio_secs = (len(wav_data) - 44) / (SAMPLE_RATE * 2)
    print(f"  Generated {audio_secs:.1f}s audio in {elapsed:.1f}s")

    mp3_data = wav_to_mp3(wav_data)

    test_output = AUDIO_DIR / "test_voice_clone.mp3"
    test_output.parent.mkdir(parents=True, exist_ok=True)
    test_output.write_bytes(mp3_data)

    print(f"  Saved: {test_output}")
    print(f"  Size: {round(len(mp3_data) / 1024, 1)} KB")
    print()
    print("Listen to this clip to verify the voice sounds right before")
    print("running the full batch. If it doesn't sound good, try:")
    print("  - A longer reference clip (15-30 seconds)")
    print("  - A cleaner recording (less background noise)")
    print("  - Adding/improving the transcript in voice_reference/tristan.txt")


def main():
    parser = argparse.ArgumentParser(
        description="Generate audio narrations using Qwen3-TTS voice cloning"
    )
    parser.add_argument("--article", type=str, help="Generate for a specific article slug")
    parser.add_argument("--force", action="store_true", help="Regenerate even if audio exists")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated")
    parser.add_argument("--test", action="store_true", help="Generate a short test clip only")
    parser.add_argument("--model", type=str, default=MODEL_ID,
                        help=f"HuggingFace model ID (default: {MODEL_ID})")
    args = parser.parse_args()

    global MODEL_ID
    if args.model != MODEL_ID:
        MODEL_ID = args.model

    import shutil
    if not shutil.which('ffmpeg'):
        print("ERROR: ffmpeg not found. Install with: sudo apt install ffmpeg")
        sys.exit(1)

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    if args.test:
        generate_test_clip()
        return

    essays = sorted(ESSAYS_DIR.glob("*.md"))
    if not essays:
        print(f"No essays found in {ESSAYS_DIR}")
        sys.exit(1)

    if args.article:
        matches = [f for f in essays if args.article in f.stem]
        if not matches:
            print(f"No essay matching '{args.article}' found")
            sys.exit(1)
        essays = matches

    if args.dry_run:
        print(f"DRY RUN — {len(essays)} essays")
        print(f"Model: {MODEL_ID}")
        print(f"Voice reference: {VOICE_REF_AUDIO}")
        print(f"Output: {AUDIO_DIR}")
        print()

        total_words = 0
        total_chars = 0
        for filepath in essays:
            title, slug, narration = extract_narration_text(filepath)
            words = len(narration.split())
            chars = len(narration)
            chunks = split_into_chunks(narration)
            total_words += words
            total_chars += chars
            exists = (AUDIO_DIR / f"{slug}.mp3").exists()
            status = "[exists]" if exists else "[pending]"
            print(f"  {status} {slug}: {words:,} words, {len(chunks)} chunks")

        est_audio_mins = round(total_words / 160)
        print(f"\nTotal: {total_words:,} words, {total_chars:,} chars")
        print(f"Estimated audio: ~{est_audio_mins} min ({round(est_audio_mins/60, 1)} hours)")
        return

    # Full generation
    print(f"Audio generation: {len(essays)} essays")
    print(f"Model: {MODEL_ID}")
    print(f"Voice reference: {VOICE_REF_AUDIO}")
    print(f"Output: {AUDIO_DIR}")
    print()

    generated = 0
    skipped = 0
    failed = 0

    for i, filepath in enumerate(essays, 1):
        print(f"\n[{i}/{len(essays)}]")
        try:
            if generate_article_audio(filepath, force=args.force):
                generated += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"    [FAILED] {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Done: {generated} generated, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    main()
