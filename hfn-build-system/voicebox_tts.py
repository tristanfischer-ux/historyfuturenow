#!/usr/bin/env python3
"""
Voicebox TTS Client — Local voice synthesis via Voicebox REST API.

Voicebox (https://github.com/jamiepine/voicebox) is an open-source voice
cloning studio powered by Qwen3-TTS. This module wraps its REST API so that
HFN's audio pipeline can use locally-cloned voices instead of cloud TTS.

Benefits over Google Cloud TTS / Gemini TTS:
    - No API costs — runs entirely on local hardware
    - Voice cloning — consistent, distinctive character voices
    - No rate limits — generate as fast as your GPU allows
    - Privacy — audio never leaves your machine
    - Instruct mode — control delivery style per-utterance

Prerequisites:
    - Voicebox running locally (or on a network machine)
    - At least one voice profile created with audio samples
    - A Qwen3-TTS model downloaded (1.7B recommended)

Configuration (environment variables):
    VOICEBOX_URL        Base URL (default: http://localhost:8000)
    VOICEBOX_PROFILE_MALE    Profile ID for male British narrator
    VOICEBOX_PROFILE_FEMALE  Profile ID for female British narrator
    VOICEBOX_PROFILE_JAMES   Profile ID for James (debate speaker)
    VOICEBOX_PROFILE_ELENA   Profile ID for Elena (debate speaker)
    VOICEBOX_MODEL_SIZE      Model size: "1.7B" or "0.6B" (default: 1.7B)
"""

import os
import io
import time
import wave
import json
import logging
import subprocess
import tempfile
import requests
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────

VOICEBOX_URL = os.environ.get("VOICEBOX_URL", "http://localhost:8000")
VOICEBOX_MODEL_SIZE = os.environ.get("VOICEBOX_MODEL_SIZE", "1.7B")

# Voice profile IDs — set these after creating profiles in Voicebox
VOICEBOX_PROFILE_MALE = os.environ.get("VOICEBOX_PROFILE_MALE", "")
VOICEBOX_PROFILE_FEMALE = os.environ.get("VOICEBOX_PROFILE_FEMALE", "")
VOICEBOX_PROFILE_JAMES = os.environ.get("VOICEBOX_PROFILE_JAMES", "")
VOICEBOX_PROFILE_ELENA = os.environ.get("VOICEBOX_PROFILE_ELENA", "")

# Request timeouts (voice generation can be slow on CPU)
GENERATE_TIMEOUT = int(os.environ.get("VOICEBOX_TIMEOUT", "300"))


# ─── Health & Discovery ───────────────────────────────────────────────────────

def is_voicebox_available() -> bool:
    """Check whether a Voicebox server is reachable and healthy."""
    try:
        resp = requests.get(f"{VOICEBOX_URL}/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("status") == "healthy"
    except (requests.ConnectionError, requests.Timeout):
        pass
    return False


def get_server_health() -> dict:
    """Return full health info from the Voicebox server."""
    resp = requests.get(f"{VOICEBOX_URL}/health", timeout=10)
    resp.raise_for_status()
    return resp.json()


def list_profiles() -> list[dict]:
    """List all voice profiles on the Voicebox server."""
    resp = requests.get(f"{VOICEBOX_URL}/profiles", timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_profile(profile_id: str) -> dict:
    """Get a single voice profile by ID."""
    resp = requests.get(f"{VOICEBOX_URL}/profiles/{profile_id}", timeout=10)
    resp.raise_for_status()
    return resp.json()


# ─── Voice Generation ─────────────────────────────────────────────────────────

def generate_speech(
    text: str,
    profile_id: str,
    language: str = "en",
    instruct: Optional[str] = None,
    seed: Optional[int] = None,
    model_size: Optional[str] = None,
    max_retries: int = 3,
) -> bytes:
    """
    Generate speech audio via the Voicebox API.

    Args:
        text:        The text to synthesise.
        profile_id:  Voicebox voice profile ID.
        language:    Language code (default "en").
        instruct:    Optional delivery instruction, e.g.
                     "Speak in a dry, sardonic British tone".
        seed:        Optional random seed for reproducibility.
        model_size:  "1.7B" or "0.6B" (defaults to env config).

    Returns:
        WAV audio bytes.
    """
    payload = {
        "profile_id": profile_id,
        "text": text,
        "language": language,
        "model_size": model_size or VOICEBOX_MODEL_SIZE,
    }
    if instruct:
        payload["instruct"] = instruct
    if seed is not None:
        payload["seed"] = seed

    last_error = None
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                f"{VOICEBOX_URL}/generate",
                json=payload,
                timeout=GENERATE_TIMEOUT,
            )

            if resp.status_code == 503:
                wait = 10 + (attempt * 10)
                logger.warning(
                    "Voicebox busy (503), attempt %d/%d, waiting %ds",
                    attempt + 1, max_retries, wait,
                )
                time.sleep(wait)
                last_error = "Server busy (503)"
                continue

            resp.raise_for_status()
            break

        except requests.Timeout:
            wait = 5 + (attempt * 5)
            logger.warning(
                "Voicebox timeout, attempt %d/%d, waiting %ds",
                attempt + 1, max_retries, wait,
            )
            time.sleep(wait)
            last_error = "Request timeout"
            continue

    else:
        raise RuntimeError(
            f"Voicebox generation failed after {max_retries} retries: {last_error}"
        )

    generation = resp.json()
    generation_id = generation["id"]

    audio_resp = requests.get(
        f"{VOICEBOX_URL}/audio/{generation_id}",
        timeout=60,
    )
    audio_resp.raise_for_status()
    return audio_resp.content


def generate_speech_for_narration(
    text: str,
    voice: str = "male",
    instruct: Optional[str] = None,
) -> bytes:
    """
    Generate narration audio using the configured male/female profile.

    This is the main entry point for article narration. It maps
    "male"/"female" to the configured Voicebox profile IDs.

    Args:
        text:      Text to narrate.
        voice:     "male" or "female".
        instruct:  Optional delivery instruction.

    Returns:
        WAV audio bytes.
    """
    if voice == "male":
        profile_id = VOICEBOX_PROFILE_MALE
        if not profile_id:
            raise ValueError(
                "VOICEBOX_PROFILE_MALE not set. "
                "Create a male voice profile in Voicebox and set the env var."
            )
    elif voice == "female":
        profile_id = VOICEBOX_PROFILE_FEMALE
        if not profile_id:
            raise ValueError(
                "VOICEBOX_PROFILE_FEMALE not set. "
                "Create a female voice profile in Voicebox and set the env var."
            )
    else:
        raise ValueError(f"Unknown voice '{voice}', expected 'male' or 'female'")

    default_instruct = (
        "Speak clearly in a warm, authoritative British accent. "
        "Natural pacing, as if reading a well-written essay aloud."
    )

    return generate_speech(
        text=text,
        profile_id=profile_id,
        language="en",
        instruct=instruct or default_instruct,
    )


def generate_speech_for_debate(
    text: str,
    speaker: str = "James",
    delivery_cue: Optional[str] = None,
) -> bytes:
    """
    Generate debate audio for James or Elena.

    Maps speaker names to Voicebox profile IDs and translates
    delivery cues from the discussion script format into Voicebox
    instruct strings.

    Args:
        text:          Dialogue text (without speaker label).
        speaker:       "James" or "Elena".
        delivery_cue:  Optional cue like "[dry]", "[emphatic]", etc.

    Returns:
        WAV audio bytes.
    """
    if speaker == "James":
        profile_id = VOICEBOX_PROFILE_JAMES or VOICEBOX_PROFILE_MALE
        base_instruct = (
            "Speak as a sharp, confident British male analyst. "
            "Quick, witty, data-driven. Think BBC Radio 4 presenter."
        )
    elif speaker == "Elena":
        profile_id = VOICEBOX_PROFILE_ELENA or VOICEBOX_PROFILE_FEMALE
        base_instruct = (
            "Speak as an animated, direct British female analyst. "
            "Warm, clear, confident. Matches the pace of a lively debate."
        )
    else:
        raise ValueError(f"Unknown speaker '{speaker}', expected 'James' or 'Elena'")

    if not profile_id:
        raise ValueError(
            f"No Voicebox profile configured for {speaker}. "
            f"Set VOICEBOX_PROFILE_{speaker.upper()} or the male/female fallback."
        )

    # Map delivery cues to instruct modifiers
    cue_map = {
        "dry": "Deliver this line with dry, understated wit.",
        "emphatic": "Emphasise this point with conviction and energy.",
        "amused": "Deliver with a hint of amusement, almost a smile.",
        "conceding": "Speak reluctantly, as if conceding a difficult point.",
        "frustrated": "Let some frustration show — this matters.",
        "surprised": "Sound genuinely surprised by what was just said.",
        "sardonic": "Deliver with sharp, sardonic edge.",
        "heated": "Speak with real heat and passion.",
        "thoughtful": "Slower, more measured — thinking aloud.",
        "clipped": "Short, clipped delivery. No wasted words.",
    }

    instruct = base_instruct
    if delivery_cue:
        cue_key = delivery_cue.strip("[]").lower()
        if cue_key in cue_map:
            instruct += f" {cue_map[cue_key]}"

    return generate_speech(
        text=text,
        profile_id=profile_id,
        language="en",
        instruct=instruct,
    )


# ─── Audio Conversion Helpers ─────────────────────────────────────────────────

def wav_to_mp3(wav_data: bytes, bitrate: str = "128k") -> bytes:
    """Convert WAV bytes to MP3 using ffmpeg."""
    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", "pipe:0",
            "-codec:a", "libmp3lame",
            "-b:a", bitrate,
            "-f", "mp3",
            "pipe:1",
        ],
        input=wav_data,
        capture_output=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {result.stderr.decode()[:500]}")
    return result.stdout


def concatenate_wav_segments(segments: list[bytes]) -> bytes:
    """Concatenate multiple WAV byte segments into one WAV file."""
    if not segments:
        raise ValueError("No segments to concatenate")

    if len(segments) == 1:
        return segments[0]

    with tempfile.TemporaryDirectory() as tmpdir:
        file_list = []
        for i, seg in enumerate(segments):
            seg_path = os.path.join(tmpdir, f"seg_{i:04d}.wav")
            with open(seg_path, "wb") as f:
                f.write(seg)
            file_list.append(seg_path)

        list_path = os.path.join(tmpdir, "files.txt")
        with open(list_path, "w") as f:
            for fp in file_list:
                f.write(f"file '{fp}'\n")

        output_path = os.path.join(tmpdir, "output.wav")
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", list_path,
                "-codec:a", "pcm_s16le",
                output_path,
            ],
            capture_output=True,
            timeout=300,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg concat error: {result.stderr.decode()[:500]}")

        with open(output_path, "rb") as f:
            return f.read()


def concatenate_and_convert_to_mp3(
    wav_segments: list[bytes],
    bitrate: str = "128k",
) -> bytes:
    """Concatenate WAV segments and convert the result to MP3."""
    combined_wav = concatenate_wav_segments(wav_segments)
    return wav_to_mp3(combined_wav, bitrate)


# ─── Profile Setup Helpers ────────────────────────────────────────────────────

def create_voice_profile(
    name: str,
    description: str = "",
    language: str = "en",
) -> dict:
    """
    Create a new voice profile on the Voicebox server.

    Returns the created profile dict (including its ID).
    """
    payload = {
        "name": name,
        "language": language,
    }
    if description:
        payload["description"] = description

    resp = requests.post(
        f"{VOICEBOX_URL}/profiles",
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def add_sample_to_profile(
    profile_id: str,
    audio_path: str,
    reference_text: str,
) -> dict:
    """
    Upload an audio sample to a voice profile for cloning.

    Args:
        profile_id:     The profile to add the sample to.
        audio_path:     Path to a WAV/MP3 file of the reference voice.
        reference_text:  Transcript of what is said in the audio.

    Returns:
        The created sample dict.
    """
    with open(audio_path, "rb") as f:
        resp = requests.post(
            f"{VOICEBOX_URL}/profiles/{profile_id}/samples",
            files={"file": (Path(audio_path).name, f)},
            data={"reference_text": reference_text},
            timeout=60,
        )
    resp.raise_for_status()
    return resp.json()


# ─── Convenience: Check Readiness ────────────────────────────────────────────

def check_voicebox_ready(require_profiles: bool = True) -> tuple[bool, str]:
    """
    Comprehensive readiness check.

    Returns (is_ready, message) tuple.
    """
    if not is_voicebox_available():
        return False, (
            f"Voicebox server not reachable at {VOICEBOX_URL}. "
            "Start Voicebox or set VOICEBOX_URL."
        )

    health = get_server_health()

    if not health.get("model_loaded") and not health.get("model_downloaded"):
        return False, (
            "No TTS model downloaded in Voicebox. "
            "Open the Voicebox app and download a Qwen3-TTS model."
        )

    if require_profiles:
        profiles = list_profiles()
        if not profiles:
            return False, (
                "No voice profiles found in Voicebox. "
                "Create at least one profile with audio samples."
            )

        if not VOICEBOX_PROFILE_MALE and not VOICEBOX_PROFILE_FEMALE:
            return False, (
                "No voice profile IDs configured. Set at least:\n"
                "  VOICEBOX_PROFILE_MALE=<profile-id>\n"
                "  VOICEBOX_PROFILE_FEMALE=<profile-id>\n"
                f"Available profiles: {', '.join(p['name'] + ' (' + p['id'] + ')' for p in profiles)}"
            )

    return True, "Voicebox ready"


if __name__ == "__main__":
    """Quick diagnostic when run directly."""
    print("Voicebox TTS Client — Diagnostic")
    print(f"  Server URL: {VOICEBOX_URL}")
    print()

    ready, msg = check_voicebox_ready(require_profiles=False)
    if not ready:
        print(f"  Status: NOT READY — {msg}")
    else:
        print("  Status: CONNECTED")
        health = get_server_health()
        print(f"  Model loaded:  {health.get('model_loaded')}")
        print(f"  Model size:    {health.get('model_size', 'N/A')}")
        print(f"  GPU:           {health.get('gpu_type', 'None')}")
        print(f"  Backend:       {health.get('backend_type', 'unknown')}")

        print()
        profiles = list_profiles()
        if profiles:
            print(f"  Voice Profiles ({len(profiles)}):")
            for p in profiles:
                marker = ""
                if p["id"] == VOICEBOX_PROFILE_MALE:
                    marker = " ← MALE"
                elif p["id"] == VOICEBOX_PROFILE_FEMALE:
                    marker = " ← FEMALE"
                elif p["id"] == VOICEBOX_PROFILE_JAMES:
                    marker = " ← JAMES"
                elif p["id"] == VOICEBOX_PROFILE_ELENA:
                    marker = " ← ELENA"
                print(f"    {p['id']}  {p['name']} ({p['language']}){marker}")
        else:
            print("  No voice profiles found.")

        print()
        print("  Profile env vars:")
        print(f"    VOICEBOX_PROFILE_MALE   = {VOICEBOX_PROFILE_MALE or '(not set)'}")
        print(f"    VOICEBOX_PROFILE_FEMALE = {VOICEBOX_PROFILE_FEMALE or '(not set)'}")
        print(f"    VOICEBOX_PROFILE_JAMES  = {VOICEBOX_PROFILE_JAMES or '(not set)'}")
        print(f"    VOICEBOX_PROFILE_ELENA  = {VOICEBOX_PROFILE_ELENA or '(not set)'}")
