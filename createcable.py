import numpy as np
import skrf as rf

# 1) Load the DUT (replica) once – scikit‑rf parses the file correctly
dut = rf.Network('Replica_S4P_HTG_FMC_X6QSFP28.s4p')
freq = dut.frequency            # <-- this is the authoritative grid

# 2) Build a zero‑valued 2‑port on exactly that grid
zeros = np.zeros((freq.npoints, 2, 2))       # shape: (f, nports, nports)
cable = rf.Network(frequency=freq, s=zeros, name='cable')

# 3) Save it
cable.write_touchstone('cable_new.s2p')