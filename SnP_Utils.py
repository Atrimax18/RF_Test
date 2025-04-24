"""SnP_Utils.py - CLI helper for .s4p network manipulation

Operations
----------
bisect 	- takes s4p file and create its half
cascade - takes two s4p files and cascade them (in series)
deembed - take the overall s4p file and a partial s4p to get the reminder s4p of this netwrok

"""

import skrf as rf

import matplotlib.pyplot as plt
from pathlib import Path
import sys

app_dir = Path(__file__).resolve().parent

HELP = f"""
Description: SnP_Utils.py takes s4p network file(s) to perform several manipulation:

Supported Operation:
bisect 	- takes s4p file and create its half
cascade - takes two s4p files and cascade them (in series)
deembed - take the overall s4p file and a partial s4p to get the reminder s4p of this netwrok
	
s4p Output format can be set as below:
ri	- Real/ Image		(Default if not parameter set)
ma	- Mag and Angle
db	- dB and angle

Usage:
bisect 	<input.s4p> 			ri|ma|db
cascade <file1.s4p>  <file2.s4p> 	ri|ma|db
deembed <file1.s4p>  <file2.s4p> 	ri|ma|db
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


# Function takes a s4p network file and creates its half
def create_bisect_network(input_file: Path, bisect_file: Path, s4p_format) -> Path:
	"""Create a new S4P file as half-value copy of the input file."""
	# Load the input S4P file

	ntw1 = rf.Network(input_file)
	ntw1diff = ntw1.copy()
	ntw1diff.se2gmm(p=2)

	# plot differential return loss
	plt.figure(figsize=(10, 5)) 
	plt.subplot(1, 2, 1)
	plt.suptitle(input_file.name)
	ntw1diff.s11.plot_s_db(label = 'sdd11')
	plt.legend()

	# plot differential insertion loss
	plt.subplot(1, 2, 2)
	ntw1diff.s21.plot_s_db(label = 'sdd21')
	plt.legend()    
	
	# Create a new network with half values
	mm_dm = rf.IEEEP370_MM_NZC_2xThru(dummy_2xthru = ntw1, z0 = 50, name = '2xthru')

	fix1 = mm_dm.se_side1
	fix1.name = 'thru'
	mm_side1 = fix1.copy()
	mm_side1.se2gmm(p = 2)

	# plot differential return loss of one half
	plt.figure(figsize=(10, 5)) 
	plt.suptitle(bisect_file.name + " (After Bisect)")
	plt.subplot(1, 2, 1)
	mm_side1.s11.plot_s_db(label = 'sdd11')
	plt.legend()

	# plot differential insertion loss of one half
	plt.subplot(1, 2, 2)
	mm_side1.s21.plot_s_db(label = 'sdd21')
	plt.legend()
	plt.show()
	
	# save 4-port S-parameters of one half
	fix1.write_touchstone(bisect_file, form=s4p_format)


# Function takes two s4p network cascade them together to perform an overall s4p network
def create_cascade_network(Net_file1: Path, Net_file2: Path, dst: Path, s4p_format) -> None:
	ntw_a, ntw_b = map(rf.Network, (str(Net_file1), str(Net_file2)))
	ntw_a, ntw_b = _same_freq(ntw_a, ntw_b)
	ntw_cascade = ntw_a ** ntw_b
	ntw_cascade.write_touchstone(str(dst), form=s4p_format)

	ntw_cascade2 = ntw_cascade.copy()
	ntw_cascade2.se2gmm(p=2)

	# plot differential return loss of one half
	plt.figure(figsize=(10, 5)) 
	plt.suptitle(dst.name + " (After Cascading)")
	plt.subplot(1, 2, 1)
	ntw_cascade2.s11.plot_s_db(label = 'sdd11')
	plt.legend()

	# plot differential insertion loss of one half
	plt.subplot(1, 2, 2)
	ntw_cascade2.s21.plot_s_db(label = 'sdd21')
	plt.legend()
	
	plt.show()
	print(f"[OK] {Net_file1.name} + {Net_file2.name} → {dst}")    


# Function takes the overall s4p network and partial s4p network get the reminder s4p of this netwrok
def create_deembeded_network(Total_Net_file: Path, Partial_Net_file: Path, dst: Path, s4p_format) -> None:
	ntw_a, ntw_b = map(rf.Network, (str(Total_Net_file), str(Partial_Net_file)))
	ntw_a, ntw_b = _same_freq(ntw_a, ntw_b)
	ntw_deembed = ntw_a ** ntw_b.inv
	ntw_deembed.write_touchstone(str(dst), form=s4p_format)

	ntw_deembed2 = ntw_deembed.copy()
	ntw_deembed2.se2gmm(p=2)

	# plot differential return loss of one half
	plt.figure(figsize=(10, 5)) 
	plt.suptitle(dst.name + " (After De-Embedding)")
	plt.subplot(1, 2, 1)
	ntw_deembed2.s11.plot_s_db(label = 'sdd11')
	plt.legend()

	# plot differential insertion loss of one half
	plt.subplot(1, 2, 2)
	ntw_deembed2.s21.plot_s_db(label = 'sdd21')
	plt.legend()
	plt.show()
	print(f"[OK] {Total_Net_file.name} - {Partial_Net_file.name} → {dst}")
# ---------------------------------------------------------------------------
# CLI entry‑point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
	if not argv or argv[0] in ("-h", "--help"):
		print(HELP); sys.exit(0)

	op, *args = argv
	op = op.lower()

	try:
		if op == "bisect":
			if not 1 <= len(args) <= 2:
				raise ValueError("bisect expects: <source file> ri|ma|db")
			
			src = Path(args[0])
			dst = src.with_stem(src.stem + "_bisect")
			s4p_format = args[1] if len(args) == 2 else 'ri'
			create_bisect_network(src, dst, s4p_format)
			
		# ------------------------------------------------------------------
		# cascade
		# ------------------------------------------------------------------
		elif op == "cascade":
			if not 2 <= len(args) <= 3:
				raise ValueError(f"cascade expects: <fileA.s4p> <fileB.s4p> ri|ma|db")
			
			Net_file1, Net_file2 = map(Path, args[:2])
			default_name = f"{Net_file1.stem}_{Net_file2.stem}_cascade.s4p"
			dst = app_dir / default_name
			s4p_format = args[2] if len(args) == 3 else 'ri'
			create_cascade_network(Net_file1, Net_file2, dst, s4p_format)
			
			
		# ------------------------------------------------------------------
		# deembed
		# ------------------------------------------------------------------
		elif op == "deembed":
			if not 2 <= len(args) <= 3:
				raise ValueError("deembed expects: <fileA.s4p> <fileB.s4p> ri|ma|db")

			Total_Net_file, Partial_Net_file = map(Path, args[:2])
			default_name = f"{Total_Net_file.stem}_{Partial_Net_file.stem}_deembed.s4p"
			dst = app_dir / default_name
			s4p_format = args[2] if len(args) == 3 else 'ri'
			create_deembeded_network(Total_Net_file, Partial_Net_file, dst, s4p_format)

		else:
			raise ValueError(f"Unknown operation: {op}")
		
		#inkey = input("Press enter to close the plotting window...")

	except (FileNotFoundError, ValueError) as err:
		print(err)
		print(HELP)
		sys.exit(1)    


	print("CLOSING PROGRAM")


if __name__ == '__main__':
	main(sys.argv[1:])

	