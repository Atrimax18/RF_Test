"""SnP_Utils.py - CLI helper for .SnP network manipulation

Operations
----------
bisect 	- takes SnP file and create its half
cascade - takes two SnP files and cascade them (in series)
deembed - take the overall SnP file and a partial SnP to get the reminder SnP of this netwrok

"""

import skrf as rf

import matplotlib.pyplot as plt
from pathlib import Path
import sys

app_dir = Path(__file__).resolve().parent

HELP = f"""
Description: SnP_Utils.py takes SnP network file(s) to perform several manipulation:

Supported Operation:
bisect 	- takes SnP file and create its half
cascade - takes two SnP files and cascade them (in series)
deembed - take the overall SnP file and a partial SnP to get the reminder SnP of this netwrok
	
SnP Output format can be set as below:
ri	- Real/ Image		(Default if not parameter set)
ma	- Mag and Angle
db	- dB and angle

Usage:
bisect 	<input.SnP> 			ri|ma|db
cascade <file1.SnP>  <file2.SnP> 	ri|ma|db
deembed <file1.SnP>  <file2.SnP> 	ri|ma|db
"""
# -----------------------------------------------------------------------------
# Utility helpers
# -----------------------------------------------------------------------------

def _same_freq(ntw_a: rf.Network, ntw_b: rf.Network) -> tuple[rf.Network, rf.Network]:
	"""Ensure *ntw_b* is on *ntw_a*'s frequency grid."""
	if ntw_a.frequency != ntw_b.frequency:
		ntw_b = ntw_b.interpolate(ntw_a.frequency)
	return ntw_a, ntw_b



# Function takes a SnP network file and creates its half
def create_bisect_network(input_file: Path, SnP_format) -> Path:
	"""Create a new SnP file as half-value copy of the input file."""
	# Load the input SnP file

	ntw1 = rf.Network(input_file)
	ntw2 = ntw1.copy()
	if (ntw2.nports == 4): # for s4p - change to diff (sdd)
		ntw2.se2gmm(p=2)
		fig_lable_21 = 'SDD21'
		fig_lable_11 = 'SDD11'
	else: # s2p
		fig_lable_21 = 'S21'
		fig_lable_11 = 'S11'

	# plot differential Insertion Loss and Return loss
	plt.figure(figsize=(10, 5)) 
	plt.suptitle(input_file.name)
	ntw2.frequency.unit = 'mhz'
	
	plt.subplot(1, 2, 1)
	ntw2.s21.plot_s_db(label = fig_lable_21)
	MaskFreq = ntw2.frequency.f
	MaskVal = [-15]*len(MaskFreq)
	plt.plot(MaskFreq, MaskVal, '--', label='IEEE370 FER1 Mask (Min)')
	plt.legend()
	plt.grid()

	plt.subplot(1, 2, 2)
	ntw2.s11.plot_s_db(label = fig_lable_11)
	MaskFreq = ntw2.frequency.f
	MaskVal = [-10]*len(MaskFreq)
	plt.plot(MaskFreq, MaskVal, '--', label='IEEE370 FER2 Mask (Max)')
	plt.legend()    
	plt.grid()
	
	plt.savefig(Path(input_file.name).stem + ".png") # The ".stem" remove initial and file extention and leave only file name

	
	# *********************************************************************************************************************************************************
	# Mixed mode S-parameters quality checking
	# This input Network is a Fixture-DUT-Fixture - Need to check it complies with the IEEE370 before we do the bisect
	print ("==============================================================")
	print ("Checking Input Network: causality, passivity, reciprocity")
	fd_qm = rf.IEEEP370_FD_QM()
	print("Net Name: " + ntw2.name)
	
	MM_Pass_Criteria = 95
	if (ntw2.nports == 4): # for s4p - change to diff (sdd)
		qm_fdf = fd_qm.check_mm_quality(ntw2)
		fd_qm.print_qm(qm_fdf)
		dd_causality 	= float(qm_fdf['dd']['causality']['value'])
		dd_passivity 	= float(qm_fdf['dd']['passivity']['value'])
		dd_reciprocity 	= float(qm_fdf['dd']['reciprocity']['value'])
		cc_causality 	= float(qm_fdf['cc']['causality']['value'])
		cc_passivity 	= float(qm_fdf['cc']['passivity']['value'])
		cc_reciprocity 	= float(qm_fdf['cc']['reciprocity']['value'])
		check_result    = (dd_causality >= MM_Pass_Criteria) and (dd_passivity >= MM_Pass_Criteria) and (dd_reciprocity >= MM_Pass_Criteria) and (cc_causality >= MM_Pass_Criteria) and (cc_passivity >= MM_Pass_Criteria) and (cc_reciprocity >= MM_Pass_Criteria)
	else: # s2p
		qm_fdf = fd_qm.check_se_quality(ntw2)
		fd_qm.print_qm(qm_fdf)
		cc_causality 	= float(qm_fdf['causality']['value'])
		cc_passivity 	= float(qm_fdf['passivity']['value'])
		cc_reciprocity 	= float(qm_fdf['reciprocity']['value'])
		check_result    = (cc_causality >= MM_Pass_Criteria) and (cc_passivity >= MM_Pass_Criteria) and (cc_reciprocity >= MM_Pass_Criteria)
	
	print ("==============================================================")
	if check_result == False:
		print ("Result are Not OK - Bisect action may not be valid !")
	else:
		print ("Result are OK - Bisect action is valid !")
	print ("==============================================================")
	
	#fer = rf.IEEEP370_FER()
	#fig = fer.plot_fd_mm_fer(ntw2)
	# *********************************************************************************************************************************************************


	# Create a new network with half values (bisection algorithm)
	if (ntw1.nports == 4): # s4p
		dm = rf.IEEEP370_MM_NZC_2xThru(dummy_2xthru = ntw1, z0 = 50, name = '2xthru')
	else: # s2p
		dm = rf.IEEEP370_SE_NZC_2xThru(dummy_2xthru = ntw1, z0 = 50, name = '2xthru')
		
	fix1 = dm.se_side1
	fix1.name = 'thru'
	
	mm_side1 = fix1.copy()
	if (mm_side1.nports == 4): # for s4p - change to diff (sdd)
		mm_side1.se2gmm(p=2)
		fig_lable_21 = 'SDD21'
		fig_lable_11 = 'SDD11'
	else: # s2p
		fig_lable_21 = 'S21'
		fig_lable_11 = 'S11'


	dst_file = input_file.with_stem(input_file.stem + "_bisect")

	# plot differential Insertion Loss and Return loss of half #1
	plt.figure(figsize=(10, 5)) 
	plt.suptitle(dst_file.name + " (After Bisect)")
	mm_side1.frequency.unit = 'mhz'

	plt.subplot(1, 2, 1)
	mm_side1.s21.plot_s_db(label = fig_lable_21)
	plt.legend()
	plt.grid()
	
	plt.subplot(1, 2, 2)
	mm_side1.s11.plot_s_db(label = fig_lable_11)	
	plt.legend()
	plt.grid()
	
	plt.savefig(Path(dst_file.name).stem + ".png") # The ".stem" remove initial and file extention and leave only file name
	
	plt.show()
	
	# save 4-port S-parameters of one half
	fix1.write_touchstone(dst_file, form=SnP_format)



# Function takes two snp network cascade them together to perform an overall SnP network
def create_cascade_network(Net_file1: Path, Net_file2: Path, SnP_format) -> None:
	ntw_a, ntw_b = map(rf.Network, (str(Net_file1), str(Net_file2)))
	if (ntw_a.nports != ntw_b.nports):
		print ("The 2 files doesn't have the same number of ports - existing")
		return
	
	if (ntw_a.nports == 4): # for s4p - change to diff (sdd)
		dst = app_dir / f"{Net_file1.stem}_{Net_file2.stem}_cascade.s4p"
	else: #2sp
		dst = app_dir / f"{Net_file1.stem}_{Net_file2.stem}_cascade.s2p"
		
	ntw_a, ntw_b = _same_freq(ntw_a, ntw_b)
	ntw_cascade = ntw_a ** ntw_b
	ntw_cascade.write_touchstone(str(dst), form=SnP_format)

	ntw_cascade2 = ntw_cascade.copy()
	if (ntw_a.nports == 4): # for s4p - change to diff (sdd)
		ntw_cascade2.se2gmm(p=2)
		fig_lable_21 = 'SDD21'
		fig_lable_11 = 'SDD11'
	else: # s2p
		fig_lable_21 = 'S21'
		fig_lable_11 = 'S11'

	# plot differential Insertion Loss and Return loss
	plt.figure(figsize=(10, 5)) 
	plt.suptitle(dst.name + " (After Cascading)")
	ntw_cascade2.frequency.unit = 'mhz'
	
	plt.subplot(1, 2, 1)
	ntw_cascade2.s21.plot_s_db(label = fig_lable_21)
	plt.legend()
	plt.grid()

	# plot differential insertion loss of one half
	plt.subplot(1, 2, 2)
	ntw_cascade2.s11.plot_s_db(label = fig_lable_11)	
	plt.legend()
	plt.grid()

	plt.savefig(Path(str(dst)).stem + ".png") # The ".stem" remove initial and file extention and leave only file name
	
	plt.show()



# Function takes the overall SnP network and partial SnP network get the reminder SnP of this netwrok
def create_deembeded_network(Total_Net_file: Path, Partial_Net_file: Path, SnP_format) -> None:
	ntw_a, ntw_b = map(rf.Network, (str(Total_Net_file), str(Partial_Net_file)))
	if (ntw_a.nports != ntw_b.nports):
		print ("The 2 files doesn't have the same number of ports - existing")
		return
		
	if (ntw_a.nports == 4): # for s4p - change to diff (sdd)
		dst = app_dir / f"{Total_Net_file.stem}_{Partial_Net_file.stem}_deembed.s4p"
	else: #2sp
		dst = app_dir / f"{Total_Net_file.stem}_{Partial_Net_file.stem}_deembed.s2p"


	ntw_a, ntw_b = _same_freq(ntw_a, ntw_b)
	ntw_deembed = ntw_a ** ntw_b.inv
	ntw_deembed.write_touchstone(str(dst), form=SnP_format)

	ntw_deembed2 = ntw_deembed.copy()
	if (ntw_a.nports == 4): # for s4p - change to diff (sdd)
		ntw_deembed2.se2gmm(p=2)
		fig_lable_21 = 'SDD21'
		fig_lable_11 = 'SDD11'
	else: # s2p
		fig_lable_21 = 'S21'
		fig_lable_11 = 'S11'

	# plot differential Insertion Loss and Return loss
	plt.figure(figsize=(10, 5)) 
	plt.suptitle(dst.name + " (After De-Embedding)")
	ntw_deembed2.frequency.unit = 'mhz'
	
	plt.subplot(1, 2, 1)
	ntw_deembed2.s21.plot_s_db(label = fig_lable_21)
	plt.legend()
	plt.grid()

	plt.subplot(1, 2, 2)
	ntw_deembed2.s11.plot_s_db(label = fig_lable_11)	
	plt.legend()
	plt.grid()

	plt.savefig(Path(str(dst)).stem + ".png") # The ".stem" remove initial and file extention and leave only file name
	
	plt.show()


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
			SnP_format = args[1] if len(args) == 2 else 'ri'
			create_bisect_network(src, SnP_format)
			
		# ------------------------------------------------------------------
		# cascade
		# ------------------------------------------------------------------
		elif op == "cascade":
			if not 2 <= len(args) <= 3:
				raise ValueError(f"cascade expects: <fileA.SnP> <fileB.SnP> ri|ma|db")
			
			Net_file1, Net_file2 = map(Path, args[:2])
			SnP_format = args[2] if len(args) == 3 else 'ri'
			create_cascade_network(Net_file1, Net_file2, SnP_format)
			
			
		# ------------------------------------------------------------------
		# deembed
		# ------------------------------------------------------------------
		elif op == "deembed":
			if not 2 <= len(args) <= 3:
				raise ValueError("deembed expects: <fileA.SnP> <fileB.SnP> ri|ma|db")

			Total_Net_file, Partial_Net_file = map(Path, args[:2])
			SnP_format = args[2] if len(args) == 3 else 'ri'
			create_deembeded_network(Total_Net_file, Partial_Net_file, SnP_format)

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

	