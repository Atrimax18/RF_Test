
"""ba4_new.py  quick-and-dirty .s4p helper

Operations
~~~~~~~~~~~
createhalf <input.s4p> [output.s4p]
    Split an IEEE-P370 2xThru fixture in half and save one side.

add <fileA.s4p> <fileB.s4p> [output.s4p]
    Cascade two networks (A x B) and write the result.

sub <fileA.s4p> <fileB.s4p> [output.s4p]
    Point-wise subtraction |S|:  result = A - B.

Run with -h / --help for this same text.
"""
from __future__ import annotations

import sys
from pathlib import Path

import skrf as rf
import matplotlib.pyplot as plt

APP_DIR = Path(__file__).resolve().parent  # folder containing this script

HELP = f"""
Simple .s4p helper

USAGE:
  python {Path(__file__).name} createhalf <input.s4p> [output.s4p]
  python {Path(__file__).name} add        <fileA.s4p> <fileB.s4p> [output.s4p]
  python {Path(__file__).name} sub        <fileA.s4p> <fileB.s4p> [output.s4p]
"""

# -----------------------------------------------------------------------------
# Utility helpers
# -----------------------------------------------------------------------------

def _same_freq(ntw_a: rf.Network, ntw_b: rf.Network) -> tuple[rf.Network, rf.Network]:
    """Ensure *ntw_b* is on *ntw_a*'s frequency grid."""
    if ntw_a.frequency != ntw_b.frequency:
        ntw_b = ntw_b.interpolate(ntw_a.frequency)
    return ntw_a, ntw_b


def _plot_quick(ntw: rf.Network, title: str):
    """Non‑blocking quick plot for visual sanity checks (ignored if no display)."""
    try:
        plt.figure(); plt.title(title)
        ntw.s21.plot_s_db(label="|S21|"); plt.legend(); plt.tight_layout()
    except Exception:
        pass

# -----------------------------------------------------------------------------
# High‑level operations
# -----------------------------------------------------------------------------

def create_half_network(src: Path, dst: Path) -> None:
    full = rf.Network(str(src))
    two_x = rf.IEEEP370_MM_NZC_2xThru(dummy_2xthru=full, z0=50, name="2xThru")
    half = two_x.se_side1
    half.write_touchstone(str(dst))
    _plot_quick(half, dst.name)
    print(f"[OK] half → {dst}")


def cascade_networks(a: Path, b: Path, dst: Path) -> None:
    ntw_a, ntw_b = map(rf.Network, (str(a), str(b)))
    ntw_a, ntw_b = _same_freq(ntw_a, ntw_b)
    out = rf.cascade(ntw_a, ntw_b)
    out.write_touchstone(str(dst))
    print(f"[OK] {a.name} ∘ {b.name} → {dst}")


def subtract_networks(a: Path, b: Path, dst: Path) -> None:
    ntw_a, ntw_b = map(rf.Network, (str(a), str(b)))
    ntw_a, ntw_b = _same_freq(ntw_a, ntw_b)
    diff = ntw_a.s - ntw_b.s
    out = rf.Network(frequency=ntw_a.frequency, s=diff, z0=ntw_a.z0, name="diff")
    out.write_touchstone(str(dst))
    print(f"[OK] {a.name} - {b.name} → {dst}")

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main(argv: list[str]):
    if not argv or argv[0] in ("-h", "--help"):
        print(HELP); sys.exit(0)

    op, *args = argv
    op = op.lower()

    try:
        if op == "createhalf":
            if not 1 <= len(args) <= 2:
                raise ValueError("createhalf expects 1-2 args")
            src = Path(args[0])
            dst = Path(args[1]) if len(args) == 2 else src.with_stem(src.stem + "_half")
            create_half_network(src, dst)

        elif op in {"add", "sub"}:
            if not 2 <= len(args) <= 3:
                raise ValueError(f"{op} expects 2-3 args")
            a, b = map(Path, args[:2])
            default_name = f"{a.stem}_{b.stem}_{'sum' if op == 'add' else 'diff'}.s4p"
            dst = Path(args[2]) if len(args) == 3 else APP_DIR / default_name
            (cascade_networks if op == "add" else subtract_networks)(a, b, dst)

        else:
            raise ValueError(f"Unknown operation: {op}")

    except (FileNotFoundError, ValueError) as err:
        print(err)
        print(HELP)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
