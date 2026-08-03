# MP3-Splitter

Split an MP3 into sections at given time offsets, then optionally edit the
ID3 tags of the resulting files.

Splitting is pure Python — no ffmpeg, no subprocess, no external binary.
Cuts are made by parsing the file's own MPEG frame headers and copying whole
frames, so output is lossless and fast (no decode/re-encode step). See
[`mp3_frames.py`](mp3_frames.py) for how the frame parsing works.

## Install

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

If you don't have `uv` yet:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# or via a package manager
brew install uv        # macOS
pipx install uv         # any platform with pipx
```

See the [official install guide](https://docs.astral.sh/uv/getting-started/installation/)
for other options. Then, in this repo:

```bash
uv sync
```

## Usage

Run with no arguments for a fully interactive session (prompts for the file,
split points, and whether to edit tags afterward):

```bash
uv run mp3_splitter.py
```

Or drive it non-interactively:

```bash
uv run mp3_splitter.py song.mp3 --timestamps 1:00,2:00
uv run mp3_splitter.py ./album-dir --timestamps 45 --output-dir ./split --edit-tags
```

Split points can be plain seconds (`90`, `90.5`) or `M:SS` / `H:MM:SS`
(`1:30`, `1:02:03.5`) — mix and match freely in a comma-separated list. The
tool prints each file's duration before prompting so you know the valid
range. Output lands in a folder named after the source file
(`song/part1.mp3`, `song/part2.mp3`, ...), or under `--output-dir` if given.

Run `uv run mp3_splitter.py --help` for all options.

## Development

```bash
uv run pytest tests/ -v
```

The test suite validates frame parsing against [mutagen](https://github.com/quodlibet/mutagen)'s
independent MP3 parser (duration must match exactly, including LAME gapless
delay/padding) and, if `ffmpeg`/`ffprobe` are available, independently decodes
every split output file to confirm it's valid.
