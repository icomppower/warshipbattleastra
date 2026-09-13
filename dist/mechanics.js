export const CLASSES={
 battleship:{name:'Vanguard',tag:'BB',hp:68000,speed:25,turn:.14,length:86,beam:13.6,reload:9,range:1650,damage:2500,barrels:3,torps:0,torpReload:0,armor:1,accel:1.9},
 cruiser:{name:'Resolute',tag:'CA',hp:42000,speed:33,turn:.22,length:70,beam:10.5,reload:5,range:1400,damage:1800,barrels:2,torps:4,torpReload:32,armor:.7,accel:2.9},
 destroyer:{name:'Tempest',tag:'DD',hp:23500,speed:41,turn:.34,length:55,beam:7.8,reload:2.6,range:1150,damage:1400,barrels:1,torps:6,torpReload:22,armor:.3,accel:4.2}
};
export const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export const angleDelta=(a,b)=>Math.atan2(Math.sin(a-b),Math.cos(a-b));
export const headingTo=(a,b)=>Math.atan2(a.x-b.x,a.z-b.z);
export const forward=h=>({x:-Math.sin(h),z:-Math.cos(h)});
export const dist=(a,b)=>Math.hypot(a.x-b.x,a.z-b.z);
export const travelTime=distance=>clamp(distance/230, .35, 7);
export function leadPoint(target,from){const t=travelTime(dist(target,from));const f=forward(target.heading);return {x:target.x+f.x*target.speed*t,z:target.z+f.z*target.speed*t};}
export function shellPosition(from,to,t,total){const u=clamp(t/total,0,1);return {x:from.x+(to.x-from.x)*u,z:from.z+(to.z-from.z)*u,y:from.y*(1-u)+4*(16+total*11)*u*(1-u)};}
export function segmentHitsShip(a,b,s,padding=1.5){
 // Slab test in ship-local coordinates: fast shells cannot tunnel through hulls.
 const cs=Math.cos(s.heading),sn=Math.sin(s.heading);
 const local=p=>({x:(p.x-s.x)*cs-(p.z-s.z)*sn,z:(p.x-s.x)*sn+(p.z-s.z)*cs,y:p.y||0});
 const p=local(a),q=local(b);let lo=0,hi=1;
 for(const [axis,mn,mx] of [['x',-s.spec.beam/2-padding,s.spec.beam/2+padding],['z',-s.spec.length/2-padding,s.spec.length/2+padding],['y',-2,12]]){
  const d=q[axis]-p[axis];if(Math.abs(d)<1e-7){if(p[axis]<mn||p[axis]>mx)return false;continue;}
  let t0=(mn-p[axis])/d,t1=(mx-p[axis])/d;if(t0>t1)[t0,t1]=[t1,t0];lo=Math.max(lo,t0);hi=Math.min(hi,t1);if(lo>hi)return false;
 }return true;
}
export function damageRoll(ammo,base,source,target,random=Math.random){
 const incidence=Math.abs(Math.cos(headingTo(target,source)-target.heading)); // 1 bow/stern, 0 broadside
 if(ammo==='torpedo')return {amount:base*(.85+random()*.3),kind:'TORPEDO HIT',fire:false,flood:true};
 if(ammo==='he')return {amount:base*.58*(1-target.spec.armor*.2),kind:'HIGH EXPLOSIVE HIT',fire:random()<.22,flood:false};
 if(incidence>.85&&target.spec.armor>.6&&random()<.55)return {amount:base*.16,kind:'RICOCHET',fire:false,flood:false};
 const citadel=incidence<.5&&random()<.22;return {amount:base*(citadel?1.8:1)*(1-incidence*target.spec.armor*.6),kind:citadel?'CITADEL HIT':'PENETRATION',fire:false,flood:false};
}
export function canMountFire(index,relative,mountCount){const a=Math.abs(angleDelta(relative,0));return index===mountCount-1?a>.55:a<2.55;}
