import skrf as rf

import matplotlib.pyplot as plt
from pathlib import Path
import sys

ntw = rf.Network('thru.s4p')         # reads RI just fine
ntw.write_touchstone('thru_ma', form='ma')    # => thru_ma.s4p (|S|∠θ)
ntw.write_touchstone('thru_db', form='db') 