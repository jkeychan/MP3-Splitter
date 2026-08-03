"""Split an MP3 into sections at given millisecond offsets, then optionally edit ID3 tags.

Splitting is pure Python: no ffmpeg, no subprocess. Frames are located by
scanning the file's own MPEG frame headers (see mp3_frames.py) and cuts land
on frame boundaries, so output is byte-copied straight from the source —
no decoding, no re-encoding, no external binary.
"""

from __future__ import annotations

from pathlib import Path

import typer
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from rich import print as rprint
from rich.prompt import Confirm, Prompt

import mp3_frames

app = typer.Typer(add_completion=False, help=__doc__)

TAG_FIELDS = {"a": "artist", "b": "album", "t": "title"}


def parse_timestamps(raw: str, duration_ms: float) -> list[int]:
    try:
        values = [int(t.strip()) for t in raw.split(",") if t.strip()]
    except ValueError as exc:
        raise typer.BadParameter("Timestamps must be integers in milliseconds.") from exc

    valid = values and values == sorted(set(values)) and all(0 <= v <= duration_ms for v in values)
    if not valid:
        raise typer.BadParameter(
            "Timestamps must be unique, strictly increasing, and within the audio duration."
        )
    return values


def prompt_for_timestamps(duration_ms: float) -> list[int]:
    while True:
        raw = Prompt.ask(f"Enter split points in ms (0-{duration_ms:.0f}), comma separated")
        try:
            return parse_timestamps(raw, duration_ms)
        except typer.BadParameter as exc:
            rprint(f"[red]{exc}[/red]")


def unique_output_dir(base: Path) -> Path:
    candidate, i = base, 1
    while candidate.exists():
        i += 1
        candidate = base.with_name(f"{base.name}_{i}")
    candidate.mkdir(parents=True)
    return candidate


def split_file(stream: mp3_frames.AudioStream, timestamps_ms: list[int], output_dir: Path) -> list[Path]:
    bounds = [0, *(mp3_frames.frame_index_at(stream.frames, ms) for ms in timestamps_ms), len(stream.frames)]
    outputs = []
    for idx, (start, end) in enumerate(zip(bounds, bounds[1:]), start=1):
        if start >= end:
            continue
        out_path = output_dir / f"part{idx}.mp3"
        out_path.write_bytes(mp3_frames.slice_bytes(stream.data, stream.frames, start, end))
        outputs.append(out_path)
    return outputs


def load_tags(mp3_path: Path) -> EasyID3:
    try:
        return EasyID3(mp3_path)
    except ID3NoHeaderError:
        tags = EasyID3()
        tags.save(mp3_path)
        return EasyID3(mp3_path)


def edit_tags_interactively(mp3_path: Path) -> None:
    tags = load_tags(mp3_path)
    changed = False

    while True:
        rprint(f"\n[bold]Current tags for '{mp3_path.name}':[/bold]")
        for label, field in (("Artist", "artist"), ("Album", "album"), ("Title", "title")):
            rprint(f"  {label}: {tags.get(field, ['<none>'])[0]}")

        choice = Prompt.ask("[A]rtist, [B]lbum, [T]itle, [Q]uit", default="q").lower()
        field = TAG_FIELDS.get(choice)
        if field is None:
            break
        tags[field] = Prompt.ask(f"New {field}")
        changed = True

    if changed:
        tags.save()


@app.command()
def main(
    input_path: Path | None = typer.Argument(
        None, exists=True, help="MP3 file or directory of MP3s. Prompts if omitted."
    ),
    timestamps: str | None = typer.Option(
        None, "--timestamps", "-t",
        help="Comma-separated millisecond split points. Prompts per-file if omitted.",
    ),
    output_dir: Path | None = typer.Option(
        None, "--output-dir", "-o",
        help="Where to write split files. Defaults to a folder next to each source file.",
    ),
    edit_tags: bool = typer.Option(
        False, "--edit-tags/--no-edit-tags", help="Edit ID3 tags on the results after splitting."
    ),
) -> None:
    """Split MP3(s) into sections and optionally edit ID3 tags on the results."""
    if input_path is None:
        input_path = Path(Prompt.ask("Enter the path to an MP3 file or directory of MP3s"))
        if not input_path.exists():
            rprint(f"[red]Path not found: {input_path}[/red]")
            raise typer.Exit(code=1)

    interactive = timestamps is None
    mp3_files = [input_path] if input_path.is_file() else sorted(input_path.glob("*.mp3"))
    if not mp3_files:
        rprint("[red]No MP3 files found.[/red]")
        raise typer.Exit(code=1)

    should_edit_tags = edit_tags
    all_outputs: list[Path] = []

    for mp3_path in mp3_files:
        try:
            stream = mp3_frames.load_audio_stream(mp3_path)
        except mp3_frames.UnsupportedMp3Error as exc:
            rprint(f"[red]{mp3_path.name}: {exc}[/red]")
            continue

        duration_ms = stream.playable_duration_ms
        points = (
            parse_timestamps(timestamps, duration_ms) if timestamps
            else prompt_for_timestamps(duration_ms)
        )

        dest = unique_output_dir((output_dir or mp3_path.parent) / mp3_path.stem)
        outputs = split_file(stream, points, dest)
        all_outputs.extend(outputs)
        rprint(f"[green]Split '{mp3_path.name}' into {len(outputs)} parts in {dest}/[/green]")

    if not edit_tags and interactive:
        should_edit_tags = Confirm.ask("Update ID3 tags for the new files?", default=False)

    if should_edit_tags:
        for out_path in all_outputs:
            edit_tags_interactively(out_path)
        rprint("[green]ID3 tags updated![/green]")


if __name__ == "__main__":
    app()
