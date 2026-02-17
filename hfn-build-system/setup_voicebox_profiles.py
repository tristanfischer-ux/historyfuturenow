#!/usr/bin/env python3
"""
Voicebox Voice Profile Setup — Interactive helper for HFN audio pipeline.

Creates the four voice profiles needed by the HFN audio system:
  1. Male Narrator   — article narration (alternating voice)
  2. Female Narrator  — article narration (alternating voice)
  3. James            — debate speaker (male, centre-right analyst)
  4. Elena            — debate speaker (female, progressive analyst)

After creating profiles, you add audio samples (short clips of the target
voice) and then set the profile IDs as environment variables.

Prerequisites:
    - Voicebox server running (https://github.com/jamiepine/voicebox)
    - A Qwen3-TTS model downloaded in Voicebox

Usage:
    python3 setup_voicebox_profiles.py              # Interactive setup
    python3 setup_voicebox_profiles.py --status      # Check current status
    python3 setup_voicebox_profiles.py --create-all  # Create all four profiles
    python3 setup_voicebox_profiles.py --add-sample PROFILE_ID audio.wav "transcript"
"""

import os
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from voicebox_tts import (
    VOICEBOX_URL,
    VOICEBOX_PROFILE_MALE,
    VOICEBOX_PROFILE_FEMALE,
    VOICEBOX_PROFILE_JAMES,
    VOICEBOX_PROFILE_ELENA,
    is_voicebox_available,
    get_server_health,
    list_profiles,
    create_voice_profile,
    add_sample_to_profile,
    check_voicebox_ready,
)

# The four profiles HFN needs
HFN_PROFILES = [
    {
        "name": "HFN Male Narrator",
        "description": "British male voice for article narration. Warm, authoritative, measured.",
        "language": "en",
        "env_var": "VOICEBOX_PROFILE_MALE",
        "current_id": VOICEBOX_PROFILE_MALE,
    },
    {
        "name": "HFN Female Narrator",
        "description": "British female voice for article narration. Clear, engaging, professional.",
        "language": "en",
        "env_var": "VOICEBOX_PROFILE_FEMALE",
        "current_id": VOICEBOX_PROFILE_FEMALE,
    },
    {
        "name": "James (HFN Debate)",
        "description": "Sharp British male analyst. Dry wit, data-driven, centre-right. BBC Radio 4 presenter style.",
        "language": "en",
        "env_var": "VOICEBOX_PROFILE_JAMES",
        "current_id": VOICEBOX_PROFILE_JAMES,
    },
    {
        "name": "Elena (HFN Debate)",
        "description": "Animated British female analyst. Direct, punchy, progressive. Foreign correspondent energy.",
        "language": "en",
        "env_var": "VOICEBOX_PROFILE_ELENA",
        "current_id": VOICEBOX_PROFILE_ELENA,
    },
]


def cmd_status():
    """Show current Voicebox status and profile configuration."""
    print("Voicebox Integration Status")
    print(f"  Server URL: {VOICEBOX_URL}")
    print()

    if not is_voicebox_available():
        print("  Server: NOT REACHABLE")
        print()
        print("  To start Voicebox:")
        print("    1. Download from https://github.com/jamiepine/voicebox/releases")
        print("    2. Launch the app (it starts the backend automatically)")
        print("    3. Or run the backend directly:")
        print("       cd voicebox/backend && pip install -r requirements.txt")
        print("       python -m backend.server --host 0.0.0.0 --port 8000")
        return

    health = get_server_health()
    print(f"  Server: CONNECTED")
    print(f"  Model loaded:     {health.get('model_loaded')}")
    print(f"  Model downloaded: {health.get('model_downloaded')}")
    print(f"  Model size:       {health.get('model_size', 'N/A')}")
    print(f"  GPU:              {health.get('gpu_type', 'None (CPU)')}")
    print(f"  Backend:          {health.get('backend_type', 'unknown')}")

    if not health.get('model_downloaded'):
        print()
        print("  No model downloaded. Open Voicebox and download Qwen3-TTS (1.7B recommended).")
        return

    print()
    profiles = list_profiles()
    print(f"  Voice Profiles ({len(profiles)}):")

    if not profiles:
        print("    (none)")
    else:
        for p in profiles:
            print(f"    {p['id']}  {p['name']} ({p['language']})")

    print()
    print("  HFN Profile Configuration:")
    for prof in HFN_PROFILES:
        pid = prof["current_id"]
        status = f"= {pid}" if pid else "(not set)"
        print(f"    {prof['env_var']:30s} {status}")

    # Check for missing profiles
    missing = [p for p in HFN_PROFILES if not p["current_id"]]
    if missing:
        print()
        print(f"  {len(missing)} profile(s) not configured. Run:")
        print("    python3 setup_voicebox_profiles.py --create-all")


def cmd_create_all():
    """Create all four HFN voice profiles in Voicebox."""
    if not is_voicebox_available():
        print(f"ERROR: Voicebox not reachable at {VOICEBOX_URL}")
        sys.exit(1)

    existing = list_profiles()
    existing_names = {p["name"] for p in existing}

    created = []
    skipped = []

    for prof in HFN_PROFILES:
        if prof["name"] in existing_names:
            match = next(p for p in existing if p["name"] == prof["name"])
            print(f"  [skip] '{prof['name']}' already exists (ID: {match['id']})")
            skipped.append((prof, match["id"]))
            continue

        result = create_voice_profile(
            name=prof["name"],
            description=prof["description"],
            language=prof["language"],
        )
        pid = result["id"]
        print(f"  [created] '{prof['name']}' (ID: {pid})")
        created.append((prof, pid))

    print()
    print("=" * 60)
    print("Profile IDs — add these to your environment:")
    print()

    all_profiles = created + skipped
    for prof, pid in sorted(all_profiles, key=lambda x: x[0]["env_var"]):
        print(f"  export {prof['env_var']}={pid}")

    print()
    print("Next steps:")
    print("  1. Add the exports above to your shell profile (~/.bashrc or ~/.zshrc)")
    print("  2. Add voice samples to each profile (short audio clips + transcripts):")
    print("     python3 setup_voicebox_profiles.py --add-sample <PROFILE_ID> sample.wav \"transcript text\"")
    print("  3. For best results, provide 2-3 samples of 10-30 seconds each")
    print("  4. Test with: python3 generate_audio.py --backend voicebox --article <slug> --force")


def cmd_add_sample(profile_id: str, audio_path: str, reference_text: str):
    """Add an audio sample to a voice profile."""
    if not is_voicebox_available():
        print(f"ERROR: Voicebox not reachable at {VOICEBOX_URL}")
        sys.exit(1)

    audio_file = Path(audio_path)
    if not audio_file.exists():
        print(f"ERROR: Audio file not found: {audio_path}")
        sys.exit(1)

    result = add_sample_to_profile(profile_id, audio_path, reference_text)
    print(f"  [added] Sample to profile {profile_id}")
    print(f"    Audio: {audio_path}")
    print(f"    Text:  {reference_text[:80]}...")
    print(f"    ID:    {result['id']}")


def main():
    parser = argparse.ArgumentParser(
        description="Set up Voicebox voice profiles for HFN audio pipeline"
    )
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument("--create-all", action="store_true", help="Create all four HFN profiles")
    parser.add_argument(
        "--add-sample",
        nargs=3,
        metavar=("PROFILE_ID", "AUDIO_PATH", "REFERENCE_TEXT"),
        help="Add an audio sample to a profile",
    )
    args = parser.parse_args()

    if args.create_all:
        cmd_create_all()
    elif args.add_sample:
        cmd_add_sample(*args.add_sample)
    elif args.status:
        cmd_status()
    else:
        cmd_status()


if __name__ == "__main__":
    main()
