#!/usr/bin/env python3

import multiprocessing as mp
import time





def f1(tNum=0):
    print('Thread: %d, start time: %s' % (tNum, time.asctime()))
    time.sleep(2)
    print('Thread: %d, end time: %s' % (tNum, time.asctime()))


#==============
# Main Function
#==============
jobs = []

for i in range(5):
    p = mp.Process(target=f1, args=(i,))
    time.sleep(0.5)
    jobs.append(p)
    p.start()

