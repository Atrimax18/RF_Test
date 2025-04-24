
"""ba4_new.py - CLI helper for .s4p network manipulation

Operations
----------
createhalf   Split a 2xThru fixture in half (IEEE P370) and save one side.
add          Cascade two 4-port networks and save the result.
sub          Point-wise subtraction of |S|-matrices (A - B).

Examples
--------
python ba4_new.py createhalf source_file.s4p
python ba4_new.py add file1.s4p file2.s4p {output file will be created}
python ba4_new.py sub file1.s4p file2.s4p {output file will be created}
"""


import skrf as rf

import matplotlib.pyplot as plt
from pathlib import Path
import sys

app_dir = Path(__file__).resolve().parent

HELP = f"""

  USAGE: Command line helper for .s4p network manipulation.
    OPERATIONS: createhalf takes argument 1 (source file *.s4p) and saves divided half of the signal in real|magnitude or db format (Y,Z,S)
                cascade takes 2 arguments (2 source files) and saves the cascade result in real,magnitude or db format (Y,Z,S)
                diff takes 2 arguments (2 source files) and saves the difference result in real,magnitude or db format (Y,Z,S)
  Arguments: OPERATION      argument1      argument2       argument3
             createhalf     <input.s4p>     ri|ma|db
              cascade       <file1.s4p>    <file2.s4p>     ri|ma|db
                diff        <file1.s4p>    <file2.s4p>     ri|ma|db
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
    """Non-blocking quick plot for visual sanity checks (ignored if no display)."""
    try:
        plt.figure(); plt.title(title)
        ntw.s21.plot_s_db(label="|S21|"); plt.legend(); plt.tight_layout()
    except Exception:
        pass


def create_half_network(input_path: Path, output_path: Path, val_set) -> Path:
    """Create a new S4P file as half-value copy of the input file."""
    # Load the input S4P file

    ntw1 = rf.Network(input_path)
    ntw1diff = ntw1.copy()
    ntw1diff.se2gmm(p=2)

    # plot differential return loss
    plt.figure(figsize=(10, 5)) 
    plt.subplot(1, 2, 1)
    plt.suptitle(input_path.name)
    ntw1diff.s11.plot_s_db(label = 'sdd11')
    plt.legend()

    # plot differential insertion loss
    plt.subplot(1, 2, 2)
    ntw1diff.s21.plot_s_db(label = 'sdd21')
    plt.legend()    
    
    # Create a new network with half values
    ##### Split into 2 halves #####
    mm_dm = rf.IEEEP370_MM_NZC_2xThru(dummy_2xthru = ntw1, z0 = 50, name = '2xthru')

    fix1 = mm_dm.se_side1
    fix1.name = 'thru'
    mm_side1 = fix1.copy()
    mm_side1.se2gmm(p = 2)

    # plot differential return loss of one half
    plt.figure(figsize=(10, 5)) 
    plt.suptitle("AFTER SPLITTING: "+ output_path.name)                 
    plt.subplot(1, 2, 1)
    mm_side1.s11.plot_s_db(label = 'sdd11')
    plt.legend()

    # plot differential insertion loss of one half
    plt.subplot(1, 2, 2)
    mm_side1.s21.plot_s_db(label = 'sdd21')
    plt.legend()
    plt.show()
    # save 4-port S-parameters of one half
    fix1.write_touchstone(output_path, form=val_set)
    
def cascade_networks(a: Path, b: Path, dst: Path, val_set) -> None:
    ntw_a, ntw_b = map(rf.Network, (str(a), str(b)))
    ntw_a, ntw_b = _same_freq(ntw_a, ntw_b)
    # out = rf.cascade(ntw_a, ntw_b)
    rf_cascade = ntw_a ** ntw_b
    #out = rf.Network(frequency=ntw_a.frequency, s=rf_cascade, z0=ntw_a.z0, name="rf_cascade")
    #out.write_touchstone(str(dst), form=val_set)
    rf_cascade.write_touchstone(str(dst), form=val_set)

    fixtur_sum = rf.Network(dst)

    ntw_add = fixtur_sum.copy()
    ntw_add.se2gmm(p=2)
    

    # plot differential return loss of one half
    plt.figure(figsize=(10, 5)) 
    plt.suptitle("CASCADE SUM: "+ dst.name)                 
    plt.subplot(1, 2, 1)
    ntw_add.s11.plot_s_db(label = 'sdd11')
    plt.legend()

    # plot differential insertion loss of one half
    plt.subplot(1, 2, 2)
    ntw_add.s21.plot_s_db(label = 'sdd21')
    plt.legend()
    plt.show()
    print(f"[OK] {a.name} + {b.name} → {dst}")    

def subtract_networks(a: Path, b: Path, dst: Path, val_set) -> None:
    ntw_a, ntw_b = map(rf.Network, (str(a), str(b)))
    ntw_a, ntw_b = _same_freq(ntw_a, ntw_b)
    # diff = ntw_a.s - ntw_b.s --------> ERROR calculation
    rf_diff = ntw_a ** ntw_b.inv
    ##out = rf.Network(frequency=ntw_a.frequency, s=rf_diff, z0=ntw_a.z0, name="rf_diff")
    ##out.write_touchstone(str(dst), form=val_set)
    rf_diff.write_touchstone(str(dst), form=val_set)


    fixtur_diff = rf.Network(dst)
    

    ntw_add = fixtur_diff.copy()
    fixture_diff_2 = rf_diff.copy()
    
    ntw_add.se2gmm(p=2)
    fixture_diff_2.se2gmm(p=2)

    # plot differential return loss of one half
    plt.figure(figsize=(10, 5)) 
    plt.suptitle("Substruct FILES: "+ dst.name)                 
    plt.subplot(1, 2, 1)
    ntw_add.s11.plot_s_db(label = 'sdd11')
    plt.legend()

    # plot differential insertion loss of one half
    plt.subplot(1, 2, 2)
    ntw_add.s21.plot_s_db(label = 'sdd21')
    plt.legend()
    plt.show()
    print(f"[OK] {a.name} - {b.name} → {dst}")
# ---------------------------------------------------------------------------
# CLI entry‑point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    if not argv or argv[0] in ("-h", "--help"):
        print(HELP); sys.exit(0)

    op, *args = argv
    op = op.lower()

    try:
        if op == "createhalf":
            if not 2 <= len(args) < 3:    # 1 <= len() <= 2
                raise ValueError("createhalf expects: <source file> ri|ma|db")
            
            src = Path(args[0])
            dst = src.with_stem(src.stem + "_half")
            val_value = args[1] if len(args) == 2 else 'ri'
            create_half_network(src, dst, val_value)
            
        # ------------------------------------------------------------------
        # cascade
        # ------------------------------------------------------------------
        elif op == "cascade":
            if not 2 <= len(args) <= 3:
                raise ValueError(f"cascade expects: <fileA.s4p> <fileB.s4p> ri|ma|db")
            
            a, b = map(Path, args[:2])
            default_name = f"{a.stem}_{b.stem}_cascade.s4p"
            dst = app_dir / default_name
            val_value = args[2] if len(args) == 3 else 'ri'
            cascade_networks(a, b, dst, val_value)
        # ------------------------------------------------------------------
        # diff
        # ------------------------------------------------------------------
        elif op == "diff":
            if not 3 <= len(args) < 4:
                raise ValueError("diff expects: <fileA.s4p> <fileB.s4p> ri|ma|db")

            a, b = map(Path, args[:2])
            default_name = f"{a.stem}_{b.stem}_diff.s4p"
            dst = app_dir / default_name
            val_value = args[2] if len(args) == 3 else 'ri'
            subtract_networks(a, b, dst, val_value)

        else:
            raise ValueError(f"Unknown operation: {op}")
        
        inkey = input("Press enter to close the plotting window...")

    except (FileNotFoundError, ValueError) as err:
        print(err)
        print(HELP)
        sys.exit(1)    


    print("CLOSING PROGRAM")


if __name__ == '__main__':
    main(sys.argv[1:])

    