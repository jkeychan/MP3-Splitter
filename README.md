# MP3-Splitter

Split an MP3 into sections at given millisecond offsets, then optionally edit
the ID3 tags of the resulting files.

Splitting is pure Python — no ffmpeg, no subprocess, no external binary.
Cuts are made by parsing the file's own MPEG frame headers and copying whole
frames, so output is lossless and fast (no decode/re-encode step). See
[`mp3_frames.py`](mp3_frames.py) for how the frame parsing works.

## Install

Requires Python 3.10+.

```bash
pip install -r requirements.txt
```

## Usage

Run with no arguments for a fully interactive session (prompts for the file,
split points, and whether to edit tags afterward):

```bash
python mp3_splitter.py
```

Or drive it non-interactively:

```bash
python mp3_splitter.py song.mp3 --timestamps 60000,120000
python mp3_splitter.py ./album-dir --timestamps 45000 --output-dir ./split --edit-tags
```

Split points are millisecond offsets from the start of the file. Output
lands in a folder named after the source file (`song/part1.mp3`,
`song/part2.mp3`, ...), or under `--output-dir` if given.

Run `python mp3_splitter.py --help` for all options.

## Development

```bash
pip install -r requirements.txt pytest
pytest tests/ -v
```

The test suite validates frame parsing against [mutagen](https://github.com/quodlibet/mutagen)'s
independent MP3 parser (duration must match exactly, including LAME gapless
delay/padding) and, if `ffmpeg`/`ffprobe` are available, independently decodes
every split output file to confirm it's valid.
