import skrf as rf
import matplotlib.pyplot as plt
from pathlib import Path

# Absolute path of the folder that holds *this* file
APP_DIR = Path(__file__).resolve().parent

# File you want to load, e.g. "config.yaml" that sits next to your script
filename = "Replica_S4P_HTG_FMC_X6QSFP28.s4p"
filename1 = "file1source_thru_sum.s4p"
data_file = APP_DIR / filename1

ntw1 = rf.Network(data_file)

ntw1diff = ntw1.copy()
ntw1diff.se2gmm(p=2)

# plot differential return loss
plt.figure(figsize=(10, 5)) 
plt.subplot(1, 2, 1)
plt.suptitle(filename1)
ntw1diff.s11.plot_s_db(label = 'sdd11')
plt.legend()

# plot differential insertion loss
plt.subplot(1, 2, 2)
ntw1diff.s21.plot_s_db(label = 'sdd21')
plt.legend()

##### Split into 2 halves #####
mm_dm = rf.IEEEP370_MM_NZC_2xThru(dummy_2xthru = ntw1, z0 = 50, name = '2xthru')

fix1 = mm_dm.se_side1
fix1.name = 'thru'
mm_side1 = fix1.copy()
mm_side1.se2gmm(p = 2)



# plot differential return loss of one half
plt.figure(figsize=(10, 5)) 
plt.suptitle("AFTER SPLITTING")                 
plt.subplot(1, 2, 1)
mm_side1.s11.plot_s_db(label = 'sdd11')
plt.legend()


# plot differential insertion loss of one half
plt.subplot(1, 2, 2)
mm_side1.s21.plot_s_db(label = 'sdd21')
plt.legend()

plt.show()

# save 4-port S-parameters of one half
fix1.write_touchstone('newfile_add.s4p')
input("Press enter to close the plotting window...")

##### Add cable to port 1 and port2 #####
'''
freq = fix1.frequency
p1 = rf.Circuit.Port(freq, name='port1', z0=50)
p2 = rf.Circuit.Port(freq, name='port2', z0=50)
p3 = rf.Circuit.Port(freq, name='port3', z0=50)
p4 = rf.Circuit.Port(freq, name='port4', z0=50)

cable1 = rf.Network('cable_nearzero.s2p',name='cable1')
cable2 = rf.Network('cable_nearzero.s2p',name='cable2')

# cable1 = 0
# cable2 = 0

fixture = rf.Circuit([[(p1,0),(cable1,0)],[(cable1,1),(fix1,0)],
                      [(p2,0),(cable2,0)],[(cable2,1),(fix1,1)],
                      [(p3,0),(fix1,2)],[(p4,0),(fix1,3)]]).network

mm_fixture = fixture.copy()
mm_fixture.se2gmm(p = 2)

# plot differential return loss of final fixture
plt.figure(figsize=(10, 5))      
plt.suptitle("FINAL RESULT")             
plt.subplot(1, 2, 1)
mm_fixture.s11.plot_s_db(label = 'sdd11')
plt.legend()

# plot differential insertion loss of final fixture
plt.subplot(1, 2, 2)
mm_fixture.s21.plot_s_db(label = 'sdd21')
plt.legend()

finaldatafile = 'newfile.s4p'
fullpath = APP_DIR / finaldatafile
# save 4-port S-parameters of final fixture
fixture.write_touchstone(fullpath)
'''