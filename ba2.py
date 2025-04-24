import skrf as rf
import matplotlib.pyplot as plt


##### Convert 2 port S-parameters to 4 port #####

p12 = rf.Network('S21.s2p')
p13 = rf.Network('S31.s2p')
p14 = rf.Network('S41.s2p')
p23 = rf.Network('S32.s2p')
p24 = rf.Network('S42.s2p')
p34 = rf.Network('S43.s2p')

ntw_list = [p12, p13, p14, p23, p24, p34]
ntw1 = rf.n_twoports_2_nport(ntw_list, nports=4)
ntw1diff = ntw1.copy()
ntw1diff.se2gmm(p=2)

# plot differential return loss
plt.figure(figsize=(10, 5))                   
plt.subplot(1, 2, 1)
ntw1diff.s11.plot_s_db(label = 'sdd11')
plt.legend()

# plot differential insertion loss
plt.subplot(1, 2, 2)
ntw1diff.s21.plot_s_db(label = 'sdd21')
plt.legend()

# save 4-port S-parameters
ntw1.write_touchstone('2xthru.s4p')

##### Split into 2 halves #####

mm_dm = rf.IEEEP370_MM_NZC_2xThru(dummy_2xthru = ntw1, z0 = 50, name = '2xthru')

fix1 = mm_dm.se_side1
fix1.name = 'thru'
mm_side1 = fix1.copy()
mm_side1.se2gmm(p = 2)

# plot differential return loss of one half
plt.figure(figsize=(10, 5))                   
plt.subplot(1, 2, 1)
mm_side1.s11.plot_s_db(label = 'sdd11')
plt.legend()

# plot differential insertion loss of one half
plt.subplot(1, 2, 2)
mm_side1.s21.plot_s_db(label = 'sdd21')
plt.legend()

# save 4-port S-parameters of one half
fix1.write_touchstone('thru.s4p')

##### Add cable to port 1 and port2 #####

freq = fix1.frequency
p1 = rf.Circuit.Port(freq, name='port1', z0=50)
p2 = rf.Circuit.Port(freq, name='port2', z0=50)
p3 = rf.Circuit.Port(freq, name='port3', z0=50)
p4 = rf.Circuit.Port(freq, name='port4', z0=50)

cable1 = rf.Network('cable.s2p',name='cable1')
cable2 = rf.Network('cable.s2p',name='cable2')

fixture = rf.Circuit([[(p1,0),(cable1,0)],[(cable1,1),(fix1,0)],
                  [(p2,0),(cable2,0)],[(cable2,1),(fix1,1)],
                  [(p3,0),(fix1,2)],[(p4,0),(fix1,3)]
                  ]).network

mm_fixture = fixture.copy()
mm_fixture.se2gmm(p = 2)

# plot differential return loss of final fixture
plt.figure(figsize=(10, 5))                   
plt.subplot(1, 2, 1)
mm_fixture.s11.plot_s_db(label = 'sdd11')
plt.legend()

# plot differential insertion loss of final fixture
plt.subplot(1, 2, 2)
mm_fixture.s21.plot_s_db(label = 'sdd21')
plt.legend()

# save 4-port S-parameters of final fixture
fixture.write_touchstone('fixture.s4p')
