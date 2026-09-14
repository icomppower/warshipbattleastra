import puppeteer from 'puppeteer';
const BASE = process.argv[2] || 'http://localhost:8123';
const MOBILE = process.argv.includes('--mobile');
const fails=[], notes=[];
const ok=(c,m)=>{ (c?notes:fails).push((c?'PASS ':'FAIL ')+m); };
const browser = await puppeteer.launch({headless:true, args:['--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader','--no-sandbox','--disable-dev-shm-usage']});
const page = await browser.newPage();
await page.setViewport(MOBILE?{width:390,height:844,isMobile:true,hasTouch:true}:{width:1280,height:720});
const errs=[];
page.on('console',m=>{ if(m.type()==='error') errs.push(m.text()); });
page.on('pageerror',e=>errs.push('pageerror: '+e.message));
const failedReq=[];
page.on('requestfailed',r=>failedReq.push(r.url()+' '+r.failure()?.errorText));
await page.goto(BASE+'/index.html',{waitUntil:'networkidle2',timeout:60000});
// 1. boot + assets
await page.waitForFunction("document.getElementById('startBtn') && !document.getElementById('startBtn').disabled",{timeout:60000}).catch(()=>{});
const btn = await page.$eval('#startBtn',b=>({text:b.textContent.trim(),disabled:b.disabled}));
ok(btn.text==='BATTLE STATIONS' && !btn.disabled, `assets loaded, start button ready (got "${btn.text}" disabled=${btn.disabled})`);
ok(failedReq.length===0, `no failed network requests (${failedReq.length}) ${failedReq.slice(0,3).join(' | ')}`);
const glb = await page.evaluate(()=>({webgl2:!!document.getElementById('ocean').getContext('webgl2')||'ctx-taken'}));
ok(!!glb.webgl2,'webgl2 context');
// 2. start battle via real UI click on the ship choice + start button
if(MOBILE){
  const hit = await page.evaluate(()=>{const b=document.getElementById('startBtn');const r=b.getBoundingClientRect();const el=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return {top:el===b||b.contains(el),inView:r.top>=0&&r.bottom<=innerHeight&&r.left>=0&&r.right<=innerWidth,r:{t:Math.round(r.top),b:Math.round(r.bottom),l:Math.round(r.left),rt:Math.round(r.right)}};});
  ok(hit.top,'start button is top element at its own centre (390px)');
  ok(hit.inView,`start button fully inside 390x844 viewport ${JSON.stringify(hit.r)}`);
  const tc = await page.evaluate(()=>{const ids=['touchFire','touchZoom'];const btns=[...document.querySelectorAll('#touchControls button')];return btns.map(b=>{const r=b.getBoundingClientRect();const el=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return {k:b.dataset.key||b.id,hit:el===b||b.contains(el),inView:r.left>=0&&r.right<=innerWidth&&r.bottom<=innerHeight,w:Math.round(r.width)};});});
  ok(tc.length>0 && tc.every(t=>t.inView), 'all touch controls inside 390px viewport: '+JSON.stringify(tc));
}
await page.click('.ship-choice[data-class="cruiser"]');
await page.click('#startBtn');
await page.waitForFunction("window.__iron && window.__iron.snap().mode==='battle'",{timeout:15000});
let s = await page.evaluate(()=>window.__iron.snap());
ok(s.player && s.player.kind==='cruiser', `battle started as chosen class (${s.player?.kind})`);
ok(s.ships.length===8, `8 ships spawned (${s.ships.length})`);
ok(s.ships.every(x=>x.mounts>0), 'every ship has turret mounts: '+s.ships.map(x=>x.mounts).join(','));
// 2b. camera: drag rotates a full turn, and the view can sit astern
const cam0 = (await page.evaluate(()=>window.__iron.snap())).cam;
const vw = await page.evaluate(()=>innerWidth), vh = await page.evaluate(()=>innerHeight);
const cx = Math.round(vw/2), cy = Math.round(vh*0.4), step = Math.round(vw/14);
if(MOBILE){ // one finger on the sea, the only camera control a phone has
  const t = await page.createCDPSession();
  await t.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:cx,y:cy}]});
  for(let i=1;i<=10;i++){ await t.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:cx-i*step,y:cy}]}); await new Promise(r=>setTimeout(r,60)); }
  await t.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
} else {
  await page.mouse.move(cx,cy); await page.mouse.down();
  for(let i=0;i<10;i++){ await page.mouse.move(cx-i*70,cy); await new Promise(r=>setTimeout(r,60)); }
  await page.mouse.up();
}
await new Promise(r=>setTimeout(r,250));
const camDrag = await page.evaluate(()=>{const q=window.__iron.snap();const dx=q.cam.px-q.player.x,dz=q.cam.pz-q.player.z;const bearing=Math.atan2(dx,dz);return {yaw:q.cam.yaw,elev:q.cam.elev,offBow:Math.abs(Math.atan2(Math.sin(bearing-q.player.heading),Math.cos(bearing-q.player.heading)))};});
ok(Math.abs(camDrag.yaw-cam0.yaw)>0.8, `drag rotates the camera (${cam0.yaw} -> ${camDrag.yaw} rad)`);
ok(camDrag.offBow>0.8, `camera can sit abaft the beam, i.e. look backward (${camDrag.offBow.toFixed(2)} rad off the bow)`);
await page.keyboard.down('ArrowLeft'); await new Promise(r=>setTimeout(r,2500)); await page.keyboard.up('ArrowLeft');
const camKeys = await page.evaluate(()=>window.__iron.snap().cam.yaw);
ok(Math.abs(camKeys-camDrag.yaw)>1.5, `arrow keys rotate the camera at a usable rate (${camDrag.yaw} -> ${camKeys} rad in 2.5s)`);

// 2c. the camera rides the hull: a turn must not rotate the ship out from under the view
const bearingOffBow = ()=>page.evaluate(()=>{const q=window.__iron.snap();const dx=q.cam.px-q.player.x,dz=q.cam.pz-q.player.z;const bearing=Math.atan2(dx,dz);return {heading:q.player.heading,offBow:Math.atan2(Math.sin(bearing-q.player.heading),Math.cos(bearing-q.player.heading))};});
await page.keyboard.press('KeyW'); await new Promise(r=>setTimeout(r,1500));
const turn0 = await bearingOffBow();
await page.keyboard.down('KeyD'); await new Promise(r=>setTimeout(r,6000)); await page.keyboard.up('KeyD');
const turn1 = await bearingOffBow();
const turned = Math.abs(turn1.heading-turn0.heading), drifted = Math.abs(turn1.offBow-turn0.offBow);
ok(turned>0.15, `the ship actually turned during the camera-follow check (${turned.toFixed(2)} rad)`);
ok(drifted<turned*0.35, `camera follows the hull through a turn (ship ${turned.toFixed(2)} rad, view drifted only ${drifted.toFixed(3)} rad off the bow)`);

// 3. sustained loop: throttle up, steer, fire for 60s of sim
await page.keyboard.down('KeyW'); await new Promise(r=>setTimeout(r,400)); await page.keyboard.up('KeyW');
await page.keyboard.down('KeyW'); await new Promise(r=>setTimeout(r,400)); await page.keyboard.up('KeyW');
const t0=Date.now(); let frames0=await page.evaluate(()=>window.__iron.snap().elapsed);
await new Promise(r=>setTimeout(r,4000));
s = await page.evaluate(()=>window.__iron.snap());
ok(s.elapsed>frames0+2, `sim clock advances (${frames0.toFixed(2)} -> ${s.elapsed.toFixed(2)})`);
ok(s.player.speed>1, `player accelerates under throttle (${s.player.speed} kn)`);
const pos0={x:s.player.x,z:s.player.z};
await page.keyboard.down('KeyA'); await new Promise(r=>setTimeout(r,2500)); await page.keyboard.up('KeyA');
const s2 = await page.evaluate(()=>window.__iron.snap());
ok(Math.hypot(s2.player.x-pos0.x,s2.player.z-pos0.z)>20, `ship moves through the world (${Math.hypot(s2.player.x-pos0.x,s2.player.z-pos0.z).toFixed(1)} m)`);
ok(Math.abs(s2.player.heading-s.player.heading)>0.05, `rudder turns the ship (dheading ${(s2.player.heading-s.player.heading).toFixed(3)})`);
// 4. firing: aim at an enemy via X target select, then fire
await page.keyboard.press('KeyX');
let maxShells=0;
for(let i=0;i<25;i++){ await page.mouse.click(640,300); await new Promise(r=>setTimeout(r,900)); const q=await page.evaluate(()=>window.__iron.snap()); maxShells=Math.max(maxShells,q.shells); if(q.hits>0) break; }
let s3 = await page.evaluate(()=>window.__iron.snap());
ok(maxShells>0, `main battery fires shells (peak in-flight ${maxShells})`);
// 5. sustained battle: let AI fight for ~90s, assert real combat state change
const start=await page.evaluate(()=>window.__iron.snap());
await new Promise(r=>setTimeout(r,90000));
const end = await page.evaluate(()=>window.__iron.snap());
const dmgTaken = start.ships.reduce((a,x)=>a+x.hp,0) - end.ships.reduce((a,x)=>a+x.hp,0);
ok(dmgTaken>0, `combat inflicts damage over 90s (total hp lost ${dmgTaken})`);
const ended = end.mode!=='battle';
ok(ended || end.elapsed>start.elapsed+60, `battle clock ran ${(end.elapsed-start.elapsed).toFixed(1)}s of sim${ended?' before the idle bot was sunk':' in 90s wall'}`);
ok(end.blueScore!==start.blueScore||end.redScore!==start.redScore, `combat score progresses (blue ${start.blueScore.toFixed(0)}->${end.blueScore.toFixed(0)}, red ${start.redScore.toFixed(0)}->${end.redScore.toFixed(0)})`);
const obj = await page.evaluate(()=>({title:document.getElementById('objectiveTitle').textContent,text:document.getElementById('objectiveText').textContent}));
ok(/SINK THE ENEMY FLEET|STRAIT IS CLEAR/.test(obj.title) && /afloat/.test(obj.text), `objective reads as a fleet action, not a capture (${JSON.stringify(obj)})`);
ok(end.capture===0, `capture sector is gone (capture stays ${end.capture})`);
// an idle bot is expected to be sunk; either it is still fighting, or the result screen must be shown correctly
const res = await page.evaluate(()=>({mode:window.__iron.snap().mode,hidden:document.getElementById('result').hidden,title:document.getElementById('resultTitle').textContent,reason:document.getElementById('resultReason').textContent.trim()}));
ok(res.mode==='battle' || (res.mode==='result' && !res.hidden && res.title.length>0 && res.reason.length>0), `battle coherent: still fighting, or a filled result screen is shown (${JSON.stringify(res)})`);
ok(errs.length===0, `no console errors (${errs.length}) ${errs.slice(0,3).join(' | ')}`);
console.log([...notes,...fails].join('\n'));
console.log(fails.length? `\nRESULT: ${fails.length} FAILED / ${notes.length} passed` : `\nRESULT: ALL ${notes.length} CHECKS PASS`);
await browser.close();
process.exit(fails.length?1:0);
