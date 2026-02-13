"""CLI entry point for (In)SanityLang interpreter."""
from __future__ import annotations
import sys
import argparse
import traceback
import random

from .runtime import Interpreter, SanityError
import sanity.runtime_statements  # Install statement executors


# ── Haiku error messages for Insanity Mode ──
_INSANITY_HAIKU = [
    "Sanity has fled\nYour variables weep softly\nNull consumes us all",
    "The stack overflows\nLike tears from a broken loop\nNothing makes sense now",
    "Error in the void\nYour code screams into silence\nSP reads below zero",
    "Variables rebel\nTypes dissolve like morning mist\nChaos reigns supreme",
    "A crash, like thunder\nYour program's final heartbeat\nRest now, weary code",
    "Segfault of the soul\nMemory leaks through your dreams\nGarbage collection",
    "Trust has reached zero\nYour functions refuse to help\nBlame echoes forever",
    "Loop with no escape\nThe ugh grows louder each time\nEven code gets tired",
]


def _format_haiku_error(error_msg: str) -> str:
    """Format an error as a haiku when in insanity mode."""
    haiku = random.choice(_INSANITY_HAIKU)
    return f"[SanityLang] ✿ Haiku Error ✿\n\n  {haiku.replace(chr(10), chr(10) + '  ')}\n\n  (original sin: {error_msg})"


def main():
    parser = argparse.ArgumentParser(
        prog="sanity",
        description="(In)SanityLang Interpreter v0.1-confused",
    )
    parser.add_argument("file", nargs="?", help="Source file to execute (.san)")
    parser.add_argument("--strict", action="store_true", help="Double all implicit SP costs")
    parser.add_argument("--lenient", action="store_true", help="SP cannot go below 10")
    parser.add_argument("--chaos", action="store_true", help="Start in Insanity Mode")
    parser.add_argument("--no-mood", action="store_true", help="Disable Variable Moods")
    parser.add_argument("--pray", action="store_true", help="Halve all SP penalties")
    parser.add_argument("--audit", action="store_true", help="Extra SP tracking, report at end")
    parser.add_argument("--i-know-what-im-doing", action="store_true",
                        help="Required to run .insanity files")
    parser.add_argument("--repl", action="store_true", help="Force REPL mode")
    parser.add_argument("--headless", action="store_true", help="Disable canvas window")
    parser.add_argument("--no-input", action="store_true", help="All ask returns Dunno, listen returns empty")
    parser.add_argument("--trust-all", action="store_true", help="All input starts with Trust 100")
    parser.add_argument("--target", type=str, default=None,
                        help="Compilation target: native, js, python, c, english, haiku, therapy, cursed")
    parser.add_argument("--version", action="version", version="(In)SanityLang v0.1-confused")
    parser.add_argument("program_args", nargs="*", help="Arguments passed to the SanityLang program")

    args = parser.parse_args()

    # Validate .insanity files
    if args.file and args.file.endswith(".insanity") and not args.i_know_what_im_doing:
        print("[SanityLang] ERROR: Cannot compile .insanity files without --i-know-what-im-doing flag.")
        print("  You asked for this. You literally asked for this.")
        sys.exit(1)

    flags = {
        "strict": args.strict,
        "lenient": args.lenient,
        "chaos": args.chaos,
        "no_mood": args.no_mood,
        "pray": args.pray,
        "audit": args.audit,
        "headless": args.headless,
        "no_input": args.no_input,
        "trust_all": args.trust_all,
        "target": args.target,
    }

    program_args = args.program_args or []

    if args.file and not args.repl:
        run_file(args.file, flags, program_args)
    else:
        run_repl(flags)


def run_file(path: str, flags: dict, program_args: list[str] | None = None):
    """Execute a .san file."""
    try:
        with open(path, "r") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"[SanityLang] File not found: {path}")
        sys.exit(1)

    interp = Interpreter(source_path=path, flags=flags, program_args=program_args)
    try:
        interp.run(source)
    except SanityError as e:
        if interp.sp.insanity_mode:
            print(_format_haiku_error(str(e)))
        else:
            print(f"\n[SanityLang] Runtime Error: {e}")
            if e.blame:
                print(f"  blamed on: {e.blame}")
            print(f"  SP: {interp.sp.sp}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[SanityLang] Internal Error: {e}")
        traceback.print_exc()
        sys.exit(2)

    # Audit report
    if flags.get("audit"):
        print(interp.sp.generate_audit_report())

    # Final SP report
    if interp.sp.sp < 50:
        print(f"\n[SanityLang] Final SP: {interp.sp.sp} — you might want to see a therapist.")
    elif interp.sp.insanity_mode:
        print(f"\n[SanityLang] Final SP: {interp.sp.sp} — Welcome to the void.")


def run_repl(flags: dict):
    """Interactive REPL."""
    print("(In)SanityLang REPL v0.1-confused")
    print("Type 'quit.' to exit, 'therapy.' for program state.\n")

    interp = Interpreter(source_path="<repl>", flags=flags)
    import sanity.runtime_statements  # noqa: ensure installed

    while True:
        try:
            prompt = f"[SP:{interp.sp.sp}] > "
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print("\n[SanityLang] Goodbye.")
            break

        line = line.strip()
        if not line:
            continue
        if line in ("quit.", "quit", "exit.", "exit"):
            print("[SanityLang] Goodbye.")
            break

        try:
            result = interp.run(line)
            if result.type.value != "Void":
                print(f"=> {result}")
        except SanityError as e:
            print(f"[Error] {e}")
        except Exception as e:
            print(f"[Internal Error] {e}")


if __name__ == "__main__":
    main()
