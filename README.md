# Iron Tide — Naval Warfare

An original single-player browser naval combat game inspired by fleet-action games. It does not use World of Warships code, artwork, branding, or ship assets.

## Play

Play now: https://icomppower.github.io/warshipbattleastra/ (GitHub Pages, published from `dist/` by `.github/workflows/pages.yml`).
Serve `dist/` with any static HTTP server. For example, from this directory:

```sh
python -m http.server 8080 --directory dist
```

Open http://localhost:8080. WebGL2 is required. All runtime assets, including Three.js, are self-hosted. No API keys, paid services, or external game assets are required.

## Game
- Three original playable classes: Vanguard battleship, Resolute heavy cruiser, Tempest destroyer.
- Three allied ships against five AI opponents in a 10-minute island battle.
- Win by sinking all enemies, reaching 1,000 points, or leading when time expires. Losing your own ship ends the battle.
- Three-dimensional Blender ship assets with articulated main gun turrets, barbette armor, barrels and muzzles, detailed bridges, glazing, tripod masts, radar grids, rigging, funnels, AA mounts, secondary gun fittings, safety railings, lifeboats, davits, bollards, capstans, anchor fittings and teak decks.
- Main guns use independent turret traverse, firing arcs and reload timers. Secondary/AA fittings are visual detail, not additional simulated weapon systems.
- AP penetration, broadside citadel hits, armor-angle ricochets, HE fires, torpedo spreads and flooding.
- Repair party, damage control immunity, momentum, rudder response, grounding and map boundaries.
- AI navigation, lead aiming, target selection, repairs, gunfire and torpedo attacks.
- Ballistic shells with swept hull collision checks; island obstruction; no friendly fire.
- Animated ocean shader, sky clouds, sun glint, archipelago terrain, trees, smoke, muzzle flashes, splashes, wakes, sinking animations, procedural audio, and dawn/storm settings.
- Camera orbit, optical zoom, mouse aiming, target lead marker, minimap, combat HUD, pause and battle results. Touch controls are available; desktop mouse and keyboard provide the best experience.

## Controls
W/S changes throttle in quarter steps; A/D controls rudder. Left-click or Space fires at the mouse's water-surface aim point. Right-drag or left/right arrows turns the camera. Wheel adjusts camera distance. Shift toggles binoculars. X cycles a selected target and turns the camera toward it. C recenters the camera. 1/2/3 selects AP/HE/torpedoes. R activates repair and T activates damage control. Escape pauses.

Use the lead marker to estimate where moving targets will be when shells arrive. Turning your broadside toward a target lets more turrets fire but exposes your armor. Torpedoes travel much slower than shells. Hold sector A to accumulate points.

## Blender source
`blender/build_fleet.py` builds the original fleet using Blender's actual bpy API. `blender/Iron_Tide_Fleet.blend` is the editable master project, with the three ship classes laid out side by side. Each `MainTurret_*` is a separate pivot hierarchy. The generated GLB files in `dist/assets` are loaded directly by the game.

Rebuild with Blender 4.3:

```sh
blender --background --python blender/build_fleet.py
```

The script also renders `blender/fleet-preview.png`. Terrain, shaders, particles, audio and gameplay are implemented by the browser engine; Blender creates the ship meshes.

## Source map
- `dist/game.js`: renderer, ocean and sky shaders, environment, visual/audio effects, AI, interaction and UI.
- `dist/mechanics.js`: pure gameplay calculations for classes, aiming, projectile flight, swept collisions, damage and gun arcs.
- `dist/index.html`, `dist/style.css`: game interface and controls.
- `blender/build_fleet.py`: reproducible asset authoring.
- `verify.mjs`: targeted mechanics checks; run `node verify.mjs`.
- `playtest.mjs`: headless browser playtest; serve `dist/` then `node playtest.mjs http://localhost:8123` (add `--mobile` for a 390x844 reachability pass). Requires `npm i puppeteer`.
- `window.__iron.snap()`: read-only runtime state snapshot used by the playtest for numeric assertions.
- `dist/vendor/three/LICENSE`: Three.js MIT license.

This is an arcade prototype with compressed range and time scales, simplified armor and damage models, and fictional ships. It is not a historically accurate naval simulator or the commercial World of Warships game. No multiplayer, aircraft simulation, progression economy, or server persistence is included.

## Validation performed
The mechanics checks pass. All three GLBs were parsed with the same GLTFLoader used by the game, and their turret counts, exact mesh dimensions and HTML control references were checked. The fleet was rendered in Blender and visually inspected.

Headless browser playtesting (`playtest.mjs`, Chrome/SwiftShader) now covers: asset load with no failed requests and no console errors, WebGL2 context, ship selection and battle start, eight ships spawned with turret mounts, throttle and rudder moving the ship through the world, main battery shells in flight, damage accumulating across a sustained battle, capture and score progression, the defeat path with its result screen, and a 390x844 pass that hit-tests the start button and every touch control. WebMCP runtime validation was not exercised.

Balance note: the battle is unforgiving. A player who does not fight back loses their ship in roughly 60-70 seconds against the five-ship enemy division, and the two allied AI ships are usually sunk in that same window.

The fleet for this version was generated through Blender 4.3.0's `bpy` Python package using Python 3.11 and NumPy 1.26.4. The standalone Blender command above is the normal local rebuild path.
