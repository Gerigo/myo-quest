from blender_asset_tracer import blendfile
from pathlib import Path
from collections import Counter
import json
b=blendfile.BlendFile(Path('work/source-anatomy/Z-Anatomy/Startup.blend'))
def name(o):return o.id_name.decode()[2:].strip()
def linked(block,field):
 p=block.get_pointer((field,b'first'))
 while p:
  yield p
  p=p.get_pointer(b'next') if p.has_field(b'next') else p.get_pointer((b'modifier',b'next'))
cs=b.find_blocks_from_code(b'GR')
print('COLLECTION',len(cs))
for c in cs:
 if any(x in name(c).lower() for x in ['muscl','bone','skelet']):print(name(c))
print('FIELDS',list(cs[0].items()))
collectionObjects={};parents={}
for c in cs:
 collectionObjects[name(c)]=[name(x.get_pointer(b'ob')) for x in linked(c,b'gobject')]
 for child in linked(c,b'children'):
  cc=child.get_pointer(b'collection');parents.setdefault(name(cc),[]).append(name(c))
objs=[]
for o in b.find_blocks_from_code(b'OB'):
 if o.get(b'type')!=1:continue
 m=o.get_pointer(b'data')
 if not m or m.code!=b'ME':continue
 cols=[c for c,ns in collectionObjects.items() if name(o) in ns]
 objs.append({'name':name(o),'collections':cols,'vertices':m.get(b'totvert'),'polygons':m.get(b'totpoly'),'matrix':o.get(b'obmat'),'modifiers':[x.dna_type_name for x in linked(o,b'modifiers')]})
Path('work/raw-inventory.json').write_text(json.dumps({'collections':collectionObjects,'parents':parents,'objects':objs},ensure_ascii=False))
for q in ['Femur.l','Clavicular part of deltoid muscle.l','Abductor hallucis muscle.l']:
 print([o for o in objs if q in o['name']])
