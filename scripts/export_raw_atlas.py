"""Read source .blend data, without running its scripts or a graphics backend.
Export original vertex positions transformed by saved world matrices. No decimation.
"""
from blender_asset_tracer import blendfile
from pathlib import Path
import numpy as np, json, re, struct, hashlib
root=Path('myo-quest/dist/assets');inv=json.loads(Path('work/raw-inventory.json').read_text());old=json.loads(Path('myo-quest/scripts/muscle-aliases.json').read_text())['muscles']
normal=lambda n:re.sub(r'[^a-z0-9]','',n.lower())
oldmap={normal(s['sourceName']):s for s in old}
b=blendfile.BlendFile(Path('work/source-anatomy/Z-Anatomy/Startup.blend'));objects={o.id_name.decode()[2:].strip():o for o in b.find_blocks_from_code(b'OB')}
structures=[];exported=[];skipped=[]
addresses={}
for block in b.blocks:addresses.setdefault(block.addr_old,[]).append(block)
def scoped(m,address):
 candidates=addresses.get(address,[])
 return next((x for x in candidates if x.file_offset>m.file_offset),candidates[0] if candidates else None)
def region(o,cat):
 cs=o['collections'];n=o['name'].lower()
 if any('of foot' in c or c in ['Tarsal bones','Metatarsal bones'] for c in cs) or 'of foot' in n or any(t in n for t in ['talus','calcaneus','cuneiform','cuboid','navicular']):return 'feet'
 if any('of hand' in c or c in ['Carpal bones','Metacarpal bones'] for c in cs) or 'of hand' in n or 'carpal bone' in n:return 'hands'
 if any(t in ' '.join(cs) for t in ['Muscles of head','Muscles of neck','Bones of cranium','Bones of head']) or any(t in n for t in ['vertebra c','atlas (','axis (','hyoid','tooth','incisor','premolar','canine','cartilage']) and 'costal' not in n:return 'head'
 if any(t in ' '.join(cs) for t in ['Muscles of lower limb','Bones of lower limb','Left lower limb','Right lower limb']):return 'lower'
 if any(t in ' '.join(cs) for t in ['Muscles of upper limb','Bones of upper limb','Left upper limb','Right upper limb']):return 'upper'
 return 'trunk'
alias={'abductor_digiti_minimi_of_foot':'abductor_digiti_minimi_foot','flexor_digiti_minimi_of_foot':'flexor_digiti_minimi_brevis_foot','quadratus_plantae_muscle':'quadratus_plantae','medial_head_of_flexor_hallucis_brevis':'flexor_hallucis_brevis_medial','lateral_head_of_flexor_hallucis_brevis':'flexor_hallucis_brevis_lateral','oblique_head_of_adductor_hallucis':'adductor_hallucis_oblique','transverse_head_of_adductor_hallucis':'adductor_hallucis_transverse'}
for o in inv['objects']:
 n=o['name'];cs=o['collections']
 if n.endswith(('.i','.j','.g')):continue
 cat=None
 if 'Muscles' in cs and not any(t in n.lower() for t in ['retinaculum','ligament','aponeurosis','trochlea','tarsus']) and ('fascia' not in n.lower() or n.startswith('Tensor fasciae')):cat='tendon' if any(t in n.lower() for t in ['tendon','tendinous','iliotibial tract','linea alba']) else 'muscle'
 elif '1: Skeletal system' in cs and not any(t in n.lower() for t in ['cells of','sinus of']):cat='cartilage' if 'cartilage' in n.lower() else 'tooth' if any(t in n.lower() for t in ['incisor','molar','canine']) else 'bone'
 elif n.startswith('Calcaneal tendon'):cat='tendon'
 if not cat or not o['polygons']:continue
 prior=oldmap.get(normal(n));base=re.sub(r'\.[lr]$','',n).strip('()');key=re.sub('[^a-z0-9]+','_',base.lower()).strip('_');key=alias.get(key,key)
 if prior:key=prior['key']
 side='left' if n.endswith('.l') else 'right' if n.endswith('.r') else 'midline';id=prior['id'] if prior else key+'_'+side
 s={'id':id,'key':key,'label':base,'sourceName':n,'side':side,'region':region(o,cat),'category':cat,'layer':'superficial' if 'Superficial muscles' in cs else 'deep','sourceVertices':o['vertices'],'sourcePolygons':o['polygons'],'sourceModifiers':o['modifiers']}
 if prior:s['layer']=prior['layer']
 structures.append(s);exported.append((o,s))
def field_array(block,field,typ,count,components=1):
 f,offset=block.dna_type.field_from_path(b.header.pointer_size,field)
 return np.ndarray((count,components),dtype=typ,buffer=block.raw_data(),offset=offset,strides=(block.dna_type.size,np.dtype(typ).itemsize)).copy()
def data_layer(m,k,typ):
 layers=scoped(m,m.get((k,b'layers')))
 for i in range(m.get((k,b'totlayer'))):
  if layers.get(b'type',array_index=i)==typ:return scoped(m,layers.get(b'data',array_index=i))
 raise ValueError('Missing custom data layer')
def mesh_arrays(o):
 ob=objects[o['name']];m=ob.get_pointer(b'data');nv=m.get(b'totvert');np_=m.get(b'totpoly');nl=m.get(b'totloop')
 verts=field_array(data_layer(m,b'vdata',0),b'co','<f4',nv,3).astype('float64');loops=field_array(data_layer(m,b'ldata',26),b'v','<u4',nl).ravel();poly=data_layer(m,b'pdata',25);starts=field_array(poly,b'loopstart','<i4',np_).ravel();counts=field_array(poly,b'totloop','<i4',np_).ravel()
 # Original meshes are predominantly triangulated. Split convex quads/ngons without deleting any vertex.
 tris=[]
 for start,count in zip(starts,counts):
  vs=loops[start:start+count]
  for i in range(1,int(count)-1):tris.append([vs[0],vs[i],vs[i+1]])
 tri=np.array(tris,dtype='<u4');mat=np.array(o['matrix']).reshape(4,4).T
 verts=verts@mat[:3,:3].T+mat[:3,3]
 # Blender world Z-up -> glTF Y-up, anterior +Z.
 verts=verts[:,[0,2,1]];verts[:,2]*=-1
 if np.linalg.det(mat[:3,:3])<0:tri=tri[:,[0,2,1]]
 norms=np.zeros_like(verts);p=verts[tri];face=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]);
 for col in range(3):np.add.at(norms,tri[:,col],face)
 lens=np.linalg.norm(norms,axis=1);norms/=np.maximum(lens[:,None],1e-12)
 return verts.astype('<f4'),norms.astype('<f4'),tri
models=[]
for bundle,cats in [('skeleton',{'bone','cartilage','tooth'}),('muscles',{'muscle','tendon'})]:
 gltf={'asset':{'version':'2.0','generator':'MYO Quest source-preserving Z-Anatomy converter'},'scene':0,'scenes':[{'nodes':[]}],'nodes':[],'meshes':[],'buffers':[{}],'bufferViews':[],'accessors':[]};bin=bytearray()
 def accessor(arr,type,ct,target,bounds=False):
  while len(bin)%4:bin.append(0)
  view=len(gltf['bufferViews']);gltf['bufferViews'].append({'buffer':0,'byteOffset':len(bin),'byteLength':arr.nbytes,'target':target});bin.extend(arr.tobytes());a={'bufferView':view,'componentType':ct,'count':len(arr),'type':type}
  if bounds:a.update(min=arr.min(axis=0).tolist(),max=arr.max(axis=0).tolist())
  idx=len(gltf['accessors']);gltf['accessors'].append(a);return idx
 for o,s in exported:
  if s['category'] not in cats:continue
  v,n,t=mesh_arrays(o);s['triangles']=len(t);s['bounds']=[v.min(axis=0).tolist(),v.max(axis=0).tolist()]
  pos=accessor(v,'VEC3',5126,34962,True);nor=accessor(n,'VEC3',5126,34962);idx=accessor(t.ravel(),'SCALAR',5125,34963)
  mi=len(gltf['meshes']);gltf['meshes'].append({'name':s['sourceName'],'primitives':[{'attributes':{'POSITION':pos,'NORMAL':nor},'indices':idx}]});ni=len(gltf['nodes']);gltf['nodes'].append({'name':s['sourceName'],'mesh':mi,'extras':{'anatomyId':s['id']}});gltf['scenes'][0]['nodes'].append(ni)
 gltf['buffers'][0]['byteLength']=len(bin);js=json.dumps(gltf,separators=(',',':'),ensure_ascii=False).encode();js+=b' '*((-len(js))%4);bin+=b'\0'*((-len(bin))%4)
 data=struct.pack('<4sII',b'glTF',2,28+len(js)+len(bin))+struct.pack('<I4s',len(js),b'JSON')+js+struct.pack('<I4s',len(bin),b'BIN\0')+bin
 (root/(bundle+'.glb')).write_bytes(data);models.append({'url':'assets/'+bundle+'.glb','bytes':len(data)});print(bundle,len(gltf['nodes']),len(data),flush=True)
atlas={'source':'Z-Anatomy / BodyParts3D','sourceUrl':'https://github.com/Z-Anatomy/Models-of-human-anatomy','license':'CC-BY-SA-4.0','sourceBlendSHA256':hashlib.sha256(Path('work/source-anatomy/Z-Anatomy/Startup.blend').read_bytes()).hexdigest(),'units':'metres','coordinates':'Y up; anterior +Z; anatomical left +X','conversion':'Original base meshes and saved world transforms. No decimation; polygon triangulation; recomputed smooth normals. Source display modifiers not evaluated.','models':models,'structures':structures}
(root/'atlas.json').write_text(json.dumps(atlas,ensure_ascii=False,separators=(',',':')))
print('TOTAL',len(structures),sum(s['triangles'] for s in structures));print('OLD MATCHES',sum(s['id'] in [m['id'] for m in old] for s in structures))
