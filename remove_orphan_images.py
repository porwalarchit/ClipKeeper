import json, os, glob

history_file = os.path.expanduser('~/.config/clipkeeper/history.json')
images_dir   = os.path.expanduser('~/.config/clipkeeper/images/')

with open(history_file) as f:
    data = json.load(f)

referenced = {e['image_file'] for e in data if e.get('type') == 'image' and e.get('image_file')}
all_files  = {os.path.basename(p) for p in glob.glob(os.path.join(images_dir, '*.png'))}
orphans    = all_files - referenced

for name in orphans:
    path = os.path.join(images_dir, name)
    print('removing', path)
    os.remove(path)

print(f'Done — removed {len(orphans)} orphaned file(s).')
