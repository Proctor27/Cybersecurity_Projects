"""
©AngelaMos | 2026
cli.py

Typer CLI application with five encoding subcommands

Defines the b64tool Typer app and its five commands: encode, decode,
detect, peel, and chain. Each command resolves its input from a
positional argument, --file, or stdin, delegates to the appropriate
logic module, then passes results to formatter.py for display. The
chain command applies a comma-separated sequence of formats in order,
passing each encoded output as the next step's input.

Key exports:
  app - The Typer application instance registered as the CLI entry point

Connects to:
  __init__.py - imports __version__
  constants.py - imports EncodingFormat, ExitCode, PEEL_MAX_DEPTH
  encoders.py - imports encode, decode, encode_url, decode_url
  detector.py - imports detect_encoding, score_all_formats
  peeler.py - imports peel
  formatter.py - imports all print_* functions
  utils.py - imports resolve_input_bytes, resolve_input_text
  test_cli.py - exercises all commands via Typer's CliRunner
"""

from pathlib import Path
from typing import Annotated
import json
import sys
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from base64_tool import __version__
from base64_tool.constants import (
    EncodingFormat,
    ExitCode,
    PEEL_MAX_DEPTH,
)
from base64_tool.detector import detect_encoding, score_all_formats
from base64_tool.encoders import (
    decode,
    encode,
    encode_url,
    decode_url,
    stream_encode_base64
)
from base64_tool.formatter import (
    print_chain_result,
    print_decoded,
    print_detection,
    print_encoded,
    print_peel_result,
)
from base64_tool.peeler import peel
from base64_tool.utils import (
    resolve_input_bytes,
    resolve_input_text,
    detect_file_type,
    calculate_shannon_entropy,
    interpret_entropy
)
from base64_tool.recipe import execute_recipe

app = typer.Typer(
    name = "b64tool",
    help = ("Multi-format encoding/decoding CLI "
            "with recursive layer detection"),
    no_args_is_help = True,
    pretty_exceptions_show_locals = False,
)

_console = Console(stderr = True)


def _version_callback(value: bool) -> None:
    if value:
        _console.print(f"b64tool v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help = "Show version and exit.",
            callback = _version_callback,
            is_eager = True,
        ),
    ] = False,
) -> None:
    pass


"""@app.command(name = "encode")
def encode_cmd(
    data: Annotated[
        str | None,
        typer.Argument(help = "Data to encode."),
    ] = None,
    fmt: Annotated[
        EncodingFormat,
        typer.Option(
            "--format",
            "-f",
            help = "Target encoding format.",
        ),
    ] = EncodingFormat.BASE64,
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            "-i",
            help = "Read input from file.",
        ),
    ] = None,
    form: Annotated[
        bool,
        typer.Option(
            "--form",
            help = "Use form-encoding for URL (space becomes +).",
        ),
    ] = False,
) -> None:
    try:
        raw = resolve_input_bytes(data, file)
        if fmt == EncodingFormat.URL and form:
            result = encode_url(raw, form = True)
        else:
            result = encode(raw, fmt)
        print_encoded(result, fmt)
    except typer.BadParameter:
        raise
    except Exception as exc:
        _console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code = ExitCode.ERROR) from None"""

"""@app.command(name = "encode")
def encode_cmd(
    data: Annotated[
        str | None,
        typer.Argument(help = "Data to encode."),
    ] = None,
    fmt: Annotated[
        EncodingFormat,
        typer.Option(
            "--format",
            "-f",
            help = "Target encoding format.",
        ),
    ] = EncodingFormat.BASE64,
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            "-i",
            help = "Read input from file.",
        ),
    ] = None,
    form: Annotated[
        bool,
        typer.Option(
            "--form",
            help = "Use form-encoding for URL (space becomes +).",
        ),
    ] = False,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help = "Write output directly to file.",
        ),
    ] = None,
) -> None:
    try:
        raw = resolve_input_bytes(data, file)
        if fmt == EncodingFormat.URL and form:
            result = encode_url(raw, form = True)
        else:
            result = encode(raw, fmt)
            
        if output:
            output.write_text(result, encoding="utf-8")
            _console.print(f"[green]Successfully wrote output to {output}[/green]")
        else:
            print_encoded(result, fmt)
    except typer.BadParameter:
        raise
    except Exception as exc:
        _console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code = ExitCode.ERROR) from None"""

def resolve_alphabet(alphabet: str | None, alphabet_file: Path | None) -> str | None:
    """Resolve alphabet from string or file option."""
    if alphabet_file and alphabet_file.exists():
        return alphabet_file.read_text(encoding="utf-8").strip()
    return alphabet

"""@app.command(name = "encode")
def encode_cmd(
    data: Annotated[
        str | None,
        typer.Argument(help = "Data to encode."),
    ] = None,
    fmt: Annotated[
        EncodingFormat,
        typer.Option(
            "--format",
            "-f",
            help = "Target encoding format.",
        ),
    ] = EncodingFormat.BASE64,
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            "-i",
            help = "Read input from file.",
        ),
    ] = None,
    form: Annotated[
        bool,
        typer.Option(
            "--form",
            help = "Use form-encoding for URL (space becomes +).",
        ),
    ] = False,
    alphabet: Annotated[
        str | None,
        typer.Option(
            "--alphabet",
            "-a",
            help = "Custom alphabet string for base64.",
        ),
    ] = None,
    alphabet_file: Annotated[
        Path | None,
        typer.Option(
            "--alphabet-file",
            help = "Path to file containing custom alphabet.",
        ),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help = "Write output directly to file.",
        ),
    ] = None,
) -> None:
    try:
        raw = resolve_input_bytes(data, file)
        resolved_alpha = resolve_alphabet(alphabet, alphabet_file)
        
        if fmt == EncodingFormat.URL and form:
            result = encode_url(raw, form = True)
        elif resolved_alpha and fmt == EncodingFormat.BASE64:
            result = encode(raw, fmt, alphabet=resolved_alpha)
        else:
            result = encode(raw, fmt)
            
        if output:
            output.write_text(result, encoding="utf-8")
            _console.print(f"[green]Successfully wrote output to {output}[/green]")
        else:
            print_encoded(result, fmt)
    except typer.BadParameter:
        raise
    except Exception as exc:
        _console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code = ExitCode.ERROR) from None"""

@app.command(name="encode")
def encode_cmd(
    text: Annotated[
        str | None,
        typer.Argument(help="Input text or payload to encode."),
    ] = None,
    format: Annotated[
        EncodingFormat,
        typer.Option("--format", "-f", help="Target encoding format."),
    ] = EncodingFormat.BASE64,
    alphabet: Annotated[
        str | None,
        typer.Option("--alphabet", help="Custom alphabet string."),
    ] = None,
    alphabet_file: Annotated[
        Path | None,
        typer.Option("--alphabet-file", help="Path to file containing custom alphabet."),
    ] = None,
    input_file: Annotated[
        Path | None,
        typer.Option("--input", "-i", help="Input file to encode."),
    ] = None,
    stream: Annotated[
        bool,
        typer.Option("--stream", help="Enable streaming mode for large files with constant memory."),
    ] = False,
) -> None:
    try:
        resolved_alpha = resolve_alphabet(alphabet, alphabet_file)
        kwargs = {"alphabet": resolved_alpha} if resolved_alpha else {}

        if input_file:
            if not input_file.exists():
                raise typer.BadParameter(f"Input file not found: {input_file}")
            
            if stream:
                # Streaming mode: constant memory generator processing
                with open(input_file, "rb") as f:
                    for chunk_output in stream_encode_base64(f, **kwargs):
                        sys.stdout.write(chunk_output)
                sys.stdout.write("\n")
                return
            else:
                # Standard mode
                data = input_file.read_text(encoding="utf-8")
        else:
            if not text:
                raise typer.BadParameter("Provide either text argument or --input file.")
            data = text

        # Normal execution for direct strings or non-streaming file reads
        result = encode(data, format, **kwargs)
        _print_result(result, format, "encoded")

    except Exception as exc:
        _console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=ExitCode.ERROR) from None

"""@app.command(name = "decode")
def decode_cmd(
    data: Annotated[
        str | None,
        typer.Argument(help = "Data to decode."),
    ] = None,
    fmt: Annotated[
        EncodingFormat,
        typer.Option(
            "--format",
            "-f",
            help = "Source encoding format.",
        ),
    ] = EncodingFormat.BASE64,
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            "-i",
            help = "Read input from file.",
        ),
    ] = None,
    form: Annotated[
        bool,
        typer.Option(
            "--form",
            help = "Use form-decoding for URL (+ becomes space).",
        ),
    ] = False,
) -> None:
    try:
        text = resolve_input_text(data, file)
        if fmt == EncodingFormat.URL and form:
            result = decode_url(text, form = True)
        else:
            result = decode(text, fmt)
        print_decoded(result)
    except typer.BadParameter:
        raise
    except Exception as exc:
        _console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code = ExitCode.ERROR) from None"""
"""@app.command(name = "decode")
def decode_cmd(
    data: Annotated[
        str | None,
        typer.Argument(help = "Data to decode."),
    ] = None,
    fmt: Annotated[
        EncodingFormat,
        typer.Option(
            "--format",
            "-f",
            help = "Source encoding format.",
        ),
    ] = EncodingFormat.BASE64,
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            "-i",
            help = "Read input from file.",
        ),
    ] = None,
    form: Annotated[
        bool,
        typer.Option(
            "--form",
            help = "Use form-decoding for URL (+ becomes space).",
        ),
    ] = False,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help = "Write output directly to file.",
        ),
    ] = None,
) -> None:
    try:
        text = resolve_input_text(data, file)
        if fmt == EncodingFormat.URL and form:
            result = decode_url(text, form = True)
        else:
            result = decode(text, fmt)
            
        if output:
            output.write_bytes(result)
            _console.print(f"[green]Successfully wrote decoded output to {output}[/green]")
        else:
            print_decoded(result)
    except typer.BadParameter:
        raise
    except Exception as exc:
        _console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code = ExitCode.ERROR) from None"""

"""@app.command(name = "decode")
def decode_cmd(
    data: Annotated[
        str | None,
        typer.Argument(help = "Data to decode."),
    ] = None,
    fmt: Annotated[
        EncodingFormat,
        typer.Option(
            "--format",
            "-f",
            help = "Source encoding format.",
        ),
    ] = EncodingFormat.BASE64,
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            "-i",
            help = "Read input from file.",
        ),
    ] = None,
    form: Annotated[
        bool,
        typer.Option(
            "--form",
            help = "Use form-decoding for URL (+ becomes space).",
        ),
    ] = False,
    alphabet: Annotated[
        str | None,
        typer.Option(
            "--alphabet",
            "-a",
            help = "Custom alphabet string for base64.",
        ),
    ] = None,
    alphabet_file: Annotated[
        Path | None,
        typer.Option(
            "--alphabet-file",
            help = "Path to file containing custom alphabet.",
        ),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help = "Write output directly to file.",
        ),
    ] = None,
) -> None:
    try:
        text = resolve_input_text(data, file)
        resolved_alpha = resolve_alphabet(alphabet, alphabet_file)
        
        if fmt == EncodingFormat.URL and form:
            result = decode_url(text, form = True)
        elif resolved_alpha and fmt == EncodingFormat.BASE64:
            result = decode(text, fmt, alphabet=resolved_alpha)
        else:
            result = decode(text, fmt)
            
        if output:
            output.write_bytes(result)
            _console.print(f"[green]Successfully wrote decoded output to {output}[/green]")
        else:
            print_decoded(result)
    except typer.BadParameter:
        raise
    except Exception as exc:
        _console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code = ExitCode.ERROR) from None
"""
@app.command(name = "decode")
def decode_cmd(
    data: Annotated[
        str | None,
        typer.Argument(help = "Data to decode."),
    ] = None,
    fmt: Annotated[
        EncodingFormat,
        typer.Option(
            "--format",
            "-f",
            help = "Source encoding format.",
        ),
    ] = EncodingFormat.BASE64,
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            "-i",
            help = "Read input from file.",
        ),
    ] = None,
    form: Annotated[
        bool,
        typer.Option(
            "--form",
            help = "Use form-decoding for URL (+ becomes space).",
        ),
    ] = False,
    alphabet: Annotated[
        str | None,
        typer.Option(
            "--alphabet",
            "-a",
            help = "Custom alphabet string for base64.",
        ),
    ] = None,
    alphabet_file: Annotated[
        Path | None,
        typer.Option(
            "--alphabet-file",
            help = "Path to file containing custom alphabet.",
        ),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help = "Write output directly to file.",
        ),
    ] = None,
) -> None:
    try:
        text = resolve_input_text(data, file)
        resolved_alpha = resolve_alphabet(alphabet, alphabet_file)
        
        if fmt == EncodingFormat.URL and form:
            result = decode_url(text, form = True)
        elif resolved_alpha and fmt == EncodingFormat.BASE64:
            result = decode(text, fmt, alphabet=resolved_alpha)
        else:
            result = decode(text, fmt)
            
        # Challenge 10: Automatic Binary Format Detection
        file_type = detect_file_type(result)
        if file_type:
            _console.print(f"[bold green][*] Detected File Type:[/bold green] {file_type}")
            
        if output:
            output.write_bytes(result)
            _console.print(f"[green]Successfully wrote decoded output to {output}[/green]")
        else:
            print_decoded(result)
            
    except typer.BadParameter:
        raise
    except Exception as exc:
        _console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code = ExitCode.ERROR) from None
    
"""@app.command(name = "detect")
def detect_cmd(
    data: Annotated[
        str | None,
        typer.Argument(help = "Data to analyze."),
    ] = None,
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            "-i",
            help = "Read input from file.",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-V",
            help = "Show per-format score breakdown.",
        ),
    ] = False,
) -> None:
    try:
        text = resolve_input_text(data, file)
        results = detect_encoding(text)
        scores = score_all_formats(text) if verbose else None
        print_detection(results, verbose_scores = scores)
    except typer.BadParameter:
        raise
    except Exception as exc:
        _console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code = ExitCode.ERROR) from None"""
@app.command(name = "detect")
def detect_cmd(
    data: Annotated[
        str | None,
        typer.Argument(help = "Data to analyze."),
    ] = None,
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            "-i",
            help = "Read input from file.",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-V",
            help = "Show per-format score breakdown.",
        ),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            "-j",
            help = "Output results in structured JSON format.",
        ),
    ] = False,
) -> None:
    try:
        text = resolve_input_text(data, file)
        results = detect_encoding(text)
        
        if json_output:
            # Format DetectionResult objects into a structure matching the challenge example
            output_data = {
                "results": [
                    {
                        "format": r.format.value,
                        "confidence": r.confidence,
                        "decoded_preview": r.decoded.decode("utf-8",errors="ignore") if isinstance(r.decoded, bytes) else str(r.decoded),
                    }
                    for r in results
                ]
            }
            typer.echo(json.dumps(output_data, indent=2))
            return

        scores = score_all_formats(text) if verbose else None
        print_detection(results, verbose_scores = scores)
    except typer.BadParameter:
        raise
    except Exception as exc:
        _console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code = ExitCode.ERROR) from None

"""@app.command(name = "peel")
def peel_cmd(
    data: Annotated[
        str | None,
        typer.Argument(help = "Data to recursively decode."),
    ] = None,
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            "-i",
            help = "Read input from file.",
        ),
    ] = None,
    max_depth: Annotated[
        int,
        typer.Option(
            "--max-depth",
            "-d",
            help = "Maximum decoding layers.",
        ),
    ] = PEEL_MAX_DEPTH,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-V",
            help = "Show per-format score breakdown at each layer.",
        ),
    ] = False,
) -> None:
    try:
        text = resolve_input_text(data, file)
        result = peel(text, max_depth = max_depth, verbose = verbose)
        print_peel_result(result, verbose = verbose)
    except typer.BadParameter:
        raise
    except Exception as exc:
        _console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code = ExitCode.ERROR) from None"""
@app.command(name = "peel")
def peel_cmd(
    data: Annotated[
        str | None,
        typer.Argument(help = "Data to recursively decode."),
    ] = None,
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            "-i",
            help = "Read input from file.",
        ),
    ] = None,
    max_depth: Annotated[
        int,
        typer.Option(
            "--max-depth",
            "-d",
            help = "Maximum decoding layers.",
        ),
    ] = PEEL_MAX_DEPTH,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-V",
            help = "Show per-format score breakdown at each layer.",
        ),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            "-j",
            help = "Output results in structured JSON format.",
        ),
    ] = False,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help = "Write final peeled output directly to file.",
        ),
    ] = None,
) -> None:
    try:
        text = resolve_input_text(data, file)
        result = peel(text, max_depth = max_depth, verbose = verbose)
        
        if json_output:
            output_data = {
                "success": result.success,
                "final_output": result.final_output.decode("utf-8", errors="ignore"),
                "layers": [
                    {
                        "depth": layer.depth,
                        "format": layer.format.value,
                        "confidence": layer.confidence,
                        "encoded_preview": layer.encoded_preview,
                    }
                    for layer in result.layers
                ]
            }
            json_str = json.dumps(output_data, indent=2)
            if output:
                output.write_text(json_str, encoding="utf-8")
                _console.print(f"[green]Successfully wrote JSON output to {output}[/green]")
            else:
                typer.echo(json_str)
            return

        if output:
            output.write_bytes(result.final_output)
            _console.print(f"[green]Successfully wrote final peeled output to {output}[/green]")
        else:
            print_peel_result(result, verbose = verbose)
    except typer.BadParameter:
        raise
    except Exception as exc:
        _console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code = ExitCode.ERROR) from None


@app.command(name = "chain")
def chain_cmd(
    data: Annotated[
        str | None,
        typer.Argument(help = "Data to encode through chain."),
    ] = None,
    steps: Annotated[
        str,
        typer.Option(
            "--steps",
            "-s",
            help = ("Comma-separated encoding formats "
                    "(e.g. base64,hex,url)."),
        ),
    ] = "base64",
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            "-i",
            help = "Read input from file.",
        ),
    ] = None,
) -> None:
    try:
        raw = resolve_input_bytes(data, file)
        formats = _parse_chain_steps(steps)
        intermediates: list[tuple[EncodingFormat, str]] = []
        current = raw

        for step_fmt in formats:
            encoded = encode(current, step_fmt)
            intermediates.append((step_fmt, encoded))
            current = encoded.encode("utf-8")

        final = intermediates[-1][1] if intermediates else ""
        print_chain_result(intermediates, final)
    except typer.BadParameter:
        raise
    except Exception as exc:
        _console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code = ExitCode.ERROR) from None


def _parse_chain_steps(raw: str) -> list[EncodingFormat]:
    formats: list[EncodingFormat] = []
    valid_names = ", ".join(f.value for f in EncodingFormat)

    for step in raw.split(","):
        cleaned = step.strip().lower()
        try:
            formats.append(EncodingFormat(cleaned))
        except ValueError:
            raise typer.BadParameter(
                f"Unknown format '{cleaned}'. "
                f"Valid formats: {valid_names}"
            ) from None

    if not formats:
        raise typer.BadParameter("At least one step is required.")

    return formats

@app.command(name = "decode-chain")
def decode_chain_cmd(
    data: Annotated[
        str | None,
        typer.Argument(help = "Data to decode through chain."),
    ] = None,
    steps: Annotated[
        str,
        typer.Option(
            "--steps",
            "-s",
            help = ("Comma-separated encoding formats "
                    "(e.g. base64,hex,url)."),
        ),
    ] = "base64",
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            "-i",
            help = "Read input from file.",
        ),
    ] = None,
) -> None:
    try:
        text = resolve_input_text(data, file)
        # Parse the forward steps, then reverse them for unwinding
        forward_formats = _parse_chain_steps(steps)
        formats = list(reversed(forward_formats))
        
        current = text
        for i, step_fmt in enumerate(formats, 1):
            decoded_bytes = decode(current, step_fmt)
            try:
                current = decoded_bytes.decode("utf-8")
            except UnicodeDecodeError:
                current = str(decoded_bytes)
            _console.print(f"# Step {i}: {step_fmt} decode → {repr(current)}")
            
    except typer.BadParameter:
        raise
    except Exception as exc:
        _console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code = ExitCode.ERROR) from None



def format_hexdump(data: bytes) -> str:
    """Format bytes into a traditional hex dump view (16 bytes per line)."""
    lines = []
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        # Offset (8-digit hex)
        offset_str = f"{i:08x}"
        
        # Hex bytes representation (split into two groups of 8 for readability or flat 16)
        hex_str = " ".join(f"{b:02x}" for b in chunk)
        # Pad spacing if chunk is less than 16 bytes
        hex_str = hex_str.ljust(47)
        
        # ASCII representation
        ascii_str = "".join(
            chr(b) if 32 <= b <= 126 else "." for b in chunk
        )
        
        lines.append(f"{offset_str}  {hex_str}  |{ascii_str}|")
    return "\n".join(lines)


@app.command(name = "hexdump")
def hexdump_cmd(
    data: Annotated[
        str | None,
        typer.Argument(help = "Encoded data to decode and dump."),
    ] = None,
    format: Annotated[
        EncodingFormat,
        typer.Option(
            "--format",
            "-f",
            help = "Input encoding format.",
        ),
    ] = EncodingFormat.BASE64,
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            "-i",
            help = "Read input from file.",
        ),
    ] = None,
) -> None:
    try:
        text = resolve_input_text(data, file)
        decoded_bytes = decode(text, format)
        dump_output = format_hexdump(decoded_bytes)
        _console.print(dump_output)
    except typer.BadParameter:
        raise
    except Exception as exc:
        _console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code = ExitCode.ERROR) from None


@app.command(name = "analyze")
def analyze_cmd(
    file: Annotated[
        Path,
        typer.Option(
            "--file",
            "-i",
            help = "Path to file containing encoded samples (one per line).",
        ),
    ],
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help = "Output analysis results as JSON.",
        ),
    ] = False,
) -> None:
    try:
        if not file.exists():
            raise typer.BadParameter(f"Input file not found: {file}")

        total_lines = 0
        failures = 0
        ambiguous_count = 0
        format_counts: dict[str, int] = {}
        confidence_sums: dict[str, float] = {}

        lines = file.read_text(encoding="utf-8").splitlines()

        for raw_line in lines:
            sample = raw_line.strip()
            if not sample or sample.startswith("#"):
                continue  # Skip empty lines or comments

            total_lines += 1
            results = detect_encoding(sample)

            if not results:
                failures += 1
                continue

            # Check for ambiguous detections (matching multiple formats above threshold)
            if len(results) > 1:
                ambiguous_count += 1

            # Track primary (highest confidence) or all matching formats
            # Here we track the best match for distribution, or all matches
            best_match = results[0]
            fmt_name = best_match.format.value
            format_counts[fmt_name] = format_counts.get(fmt_name, 0) + 1
            confidence_sums[fmt_name] = confidence_sums.get(fmt_name, 0.0) + best_match.confidence

        # Compile statistics
        stats = {
            "total_samples": total_lines,
            "detection_failures": failures,
            "ambiguous_samples": ambiguous_count,
            "formats": {}
        }

        for fmt, count in format_counts.items():
            avg_conf = confidence_sums[fmt] / count if count > 0 else 0.0
            stats["formats"][fmt] = {
                "count": count,
                "percentage": round((count / total_lines) * 100, 2) if total_lines > 0 else 0,
                "average_confidence": round(avg_conf, 2)
            }

        if as_json:
            print(json.dumps(stats, indent=2))
        else:
            _console.print(f"\n[bold cyan]Encoding Frequency Analysis Summary[/bold cyan]")
            _console.print(f"Total Samples Analyzed: {total_lines}")
            _console.print(f"Detection Failures: [red]{failures}[/red]")
            _console.print(f"Ambiguous Matches (Multiple Formats): [yellow]{ambiguous_count}[/yellow]\n")

            table = Table(title="Format Distribution")
            table.add_column("Format", style="magenta")
            table.add_column("Count", justify="right")
            table.add_column("Share (%)", justify="right")
            table.add_column("Avg Confidence", justify="right")

            for fmt, data in stats["formats"].items():
                table.add_row(
                    fmt.upper(),
                    str(data["count"]),
                    f"{data['percentage']}%",
                    str(data["average_confidence"])
                )

            _console.print(table)

    except typer.BadParameter:
        raise
    except Exception as exc:
        _console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code = ExitCode.ERROR) from None

@app.command(name="entropy")
def entropy_cmd(
    text: Annotated[
        str | None,
        typer.Argument(help="Input text or payload to analyze."),
    ] = None,
    file: Annotated[
        Path | None,
        typer.Option("--file", "-i", help="Read input from file."),
    ] = None,
) -> None:
    try:
        if file:
            if not file.exists():
                raise typer.BadParameter(f"Input file not found: {file}")
            data_bytes = file.read_bytes()
        else:
            if not text:
                raise typer.BadParameter("Provide either text argument or --file.")
            data_bytes = text.encode("utf-8")
        
        score = calculate_shannon_entropy(data_bytes)
        description = interpret_entropy(score)
        
        _console.print(Panel.fit(
            f"[bold cyan]Shannon Entropy Score:[/bold cyan] {score} / 8.0\n"
            f"[bold yellow]Analysis:[/bold yellow] {description}",
            title="Florence Entropy Triage"
        ))
    except Exception as exc:
        _console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=ExitCode.ERROR) from None



@app.command(name="recipe")
def recipe_cmd(
    text: Annotated[
        str | None,
        typer.Argument(help="Input data to process through the recipe."),
    ] = None,
    recipe_file: Annotated[
        Path,
        typer.Option("--import", "-m", help="Path to CyberChef recipe JSON file."),
    ] = None,
    file: Annotated[
        Path | None,
        typer.Option("--file", "-i", help="Read input data from file."),
    ] = None,
) -> None:
    try:
        input_data = resolve_input_text(text, file)
        
        if not recipe_file or not recipe_file.exists():
            raise typer.BadParameter("A valid CyberChef recipe JSON file must be provided via --import.")
            
        result = execute_recipe(input_data, recipe_file)
        
        if isinstance(result, bytes):
            _console.print(f"[yellow]<Binary result of {len(result)} bytes>[/yellow]")
        else:
            _console.print(result)
            
    except Exception as exc:
        _console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=ExitCode.ERROR) from None