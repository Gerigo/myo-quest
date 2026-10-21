import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {lessons,lessonFor} from '../dist/anatomy-data.js';
const root=new URL('../dist/',import.meta.url),atlas=JSON.parse(readFileSync(new URL('assets/atlas.json',root))),seen=[];
let triangles=0;
for(const file of atlas.models){const buf=readFileSync(new URL(file.url,root));assert.equal(buf.toString('utf8',0,4),'glTF');assert.equal(buf.readUInt32LE(8),buf.length);const jsonLength=buf.readUInt32LE(12),g=JSON.parse(buf.subarray(20,20+jsonLength));const binary=buf.subarray(28+jsonLength);
for(const node of g.nodes){const id=node.extras.anatomyId,s=atlas.structures.find(s=>s.id===id);assert(s,`Mesh without metadata: ${id}`);seen.push(id);const p=g.meshes[node.mesh].primitives[0],pos=g.accessors[p.attributes.POSITION],norm=g.accessors[p.attributes.NORMAL],idx=g.accessors[p.indices];assert.equal(pos.count,s.sourceVertices,`${id}: no vertex decimation`);assert.equal(norm.count,pos.count);assert.equal(idx.count,s.triangles*3);assert(s.triangles>=s.sourcePolygons);triangles+=s.triangles;const iv=g.bufferViews[idx.bufferView];for(let i=0;i<idx.count;i++)assert(binary.readUInt32LE(iv.byteOffset+i*4)<pos.count,`${id}: valid triangle index`);const pv=g.bufferViews[pos.bufferView];for(let i=0;i<pos.count*3;i++)assert(Number.isFinite(binary.readFloatLE(pv.byteOffset+i*4)),`${id}: finite geometry`);assert.deepEqual([pos.min,pos.max],s.bounds);}}
assert.equal(new Set(seen).size,seen.length);assert.deepEqual(seen.sort(),atlas.structures.map(s=>s.id).sort());assert(triangles>2_000_000);
for(const s of atlas.structures){assert(s.labelFr);assert(['head','trunk','upper','hands','lower','feet'].includes(s.region));assert(!/\.[ijg]$/.test(s.sourceName),'Annotation objects excluded');if(s.side==='left')assert(s.bounds[1][0]>0,`${s.id}: left orientation`);if(s.side==='right')assert(s.bounds[0][0]<0,`${s.id}: right orientation`);}
for(const region of ['feet','hands']){assert(atlas.structures.filter(s=>s.region===region&&s.category==='muscle').length>=20);assert(atlas.structures.filter(s=>s.region===region&&s.category==='bone').length>=40);}
for(const l of lessons){assert(atlas.structures.some(s=>s.category==='muscle'&&lessonFor(s.key)?.id===l.id),`No model for lesson ${l.id}`);for(const field of ['name','latin','action','origin','insertion','nerve','question','source'])assert(l[field]?.length>5);assert.equal(new URL(l.source).protocol,'https:');}
assert.equal(lessonFor('extensor_digitorum_longus').id,'extensor_digitorum_longus');assert.equal(lessonFor('extensor_digitorum_brevis').id,'extensor_digitorum_brevis');assert.equal(lessonFor('flexor_hallucis_brevis_medial').id,'flexor_hallucis_brevis');
assert(atlas.structures.filter(s=>s.key==='tensor_fasciae_latae').every(s=>s.category==='muscle'));assert(atlas.structures.filter(s=>s.key==='calcaneal_tendon').every(s=>s.category==='tendon'));
console.log(`PASS: ${seen.length} structures, ${triangles.toLocaleString('fr')} triangles, ${lessons.length} documented lessons; geometry, laterality, foot/hand coverage and quiz mappings verified.`);
const {coachProfiles,coachFor}=await import('../dist/coach-data.js');
assert.equal(Object.keys(coachProfiles).length,40);
for(const [id,profile] of Object.entries(coachProfiles)){const l=lessons.find(l=>l.id===id);assert(l,`Coach profile with no lesson: ${id}`);for(const f of ['plain','exercise','gym','remember','originSimple','insertionSimple'])assert(profile[f]?.length>5);assert.equal(coachFor(l),profile);}
for(const l of lessons)assert(coachFor(l).plain.length>5);
console.log('PASS: 40 coach profiles matched to the 3D lesson catalogue; all 116 lessons have a study explanation.');
