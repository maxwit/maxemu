import os
import maxemu

base_dir = os.path.expanduser('~') + '/Downloads/'
for iso in os.listdir(base_dir):
    if iso.endswith('.iso'):
        iso = base_dir + iso
        result = maxemu.parse_iso(iso)
        print(f'{result}\n')