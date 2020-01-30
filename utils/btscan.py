#!/usr/bin/env python3

from bluetooth import discover_devices as discover

def scan_devices():
    device = discover(duration=5, lookup_names=False)
    print(device)
    
scan_devices()

