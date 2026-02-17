# Voice Reference for Qwen3-TTS Voice Cloning

This directory holds the reference audio clip used to clone the author's voice
for all article narrations on History Future Now.

## What you need

### 1. `tristan.wav` — Your voice reference clip

A short recording of your voice that the TTS model will clone. The model
needs just **3 seconds minimum**, but **10-30 seconds** gives better results.

**Recording guidelines:**

- **Length:** 10-30 seconds of continuous speech
- **Content:** Read a passage from one of your articles — something with your
  natural cadence and tone. A paragraph from any HFN essay works well.
- **Quality:** Clear audio, minimal background noise. A decent microphone in a
  quiet room is sufficient — studio quality is not required.
- **Format:** WAV (16-bit, mono or stereo, any sample rate — the model resamples
  internally). MP3 also works but WAV is preferred.
- **Style:** Read naturally, as you would narrate an article. Not too fast, not
  too slow. The model picks up pace, pitch, and tone from the reference.

**Quick recording options:**

- **macOS:** Open QuickTime Player → File → New Audio Recording → Record → Save
  (exports as .m4a — convert to .wav with `ffmpeg -i recording.m4a tristan.wav`)
- **Any OS:** Use [Audacity](https://www.audacityteam.org/) (free, open-source)
- **Phone:** Voice Memos app → Share → transfer to computer → convert to WAV
- **Browser:** https://online-voice-recorder.com/ (exports WAV directly)

### 2. `tristan.txt` — Transcript of the reference clip

A plain text file containing the **exact words spoken** in the reference audio.
This significantly improves voice cloning quality because the model can align
your speech patterns with the text.

**Example:**

If your `tristan.wav` is you reading this passage:

> History does not repeat, but it rhymes. The patterns that shaped the rise
> and fall of civilisations are playing out again in our own time.

Then `tristan.txt` should contain exactly:

```
History does not repeat, but it rhymes. The patterns that shaped the rise and fall of civilisations are playing out again in our own time.
```

**Important:** The transcript must match the audio exactly — same words, same
order. Pauses, "um"s, and false starts should be omitted from the transcript
(the model handles the alignment).

If you don't provide a transcript, the model falls back to x-vector-only mode
(speaker embedding without text alignment). This still works but produces
slightly less faithful voice cloning.

## Testing your reference

Before generating all 62 articles, test with a short clip:

```bash
cd hfn-build-system
python3 generate_audio_qwen.py --test
```

This generates a ~30-second test clip at `hfn-site-output/audio/test_voice_clone.mp3`.
Listen to it. If it sounds like you, proceed with the full batch. If not:

- Try a longer reference clip (20-30 seconds)
- Try a cleaner recording environment
- Make sure the transcript matches exactly
- Try a different passage — some speech patterns clone better than others

## Files in this directory

| File | Purpose | Required |
|------|---------|----------|
| `tristan.wav` | Voice reference audio clip | Yes |
| `tristan.txt` | Transcript of the audio clip | Strongly recommended |
| `README.md` | This file | — |

## GPU requirements

The Qwen3-TTS-12Hz-1.7B-Base model needs:
- ~3.5 GB VRAM (bfloat16)
- ~6 GB VRAM total with KV cache during generation
- Any NVIDIA GPU from GTX 1080 Ti onwards should work
- RTX 3090/4090 or cloud A10/T4 for faster inference
- With flash-attn installed, memory usage drops significantly
