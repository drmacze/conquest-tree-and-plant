# DLavie Conquest Nature

A Minecraft Bedrock nature add-on focused on organic, realistic trees and plants reconstructed from high-detail OBJ source art.

> Current version: **v0.3.2 — OBJ Source-Atlas Visual Pass**  
> Required game version: **Minecraft Bedrock 1.26.45+**

## v0.3.2 highlights

- Seven mobile-optimized tree silhouettes reconstructed from the supplied high-detail OBJ pack.
- Runtime library: Oak, Walnut, Mossy Tree, Small Bark Tree, Sonnerat, Tall Bark Tree and Giant Tree.
- Every tree now has its own bark and foliage material generated from the corresponding supplied source texture atlas.
- OBJ tree worldgen no longer falls back to the old vanilla-looking procedural oak variants.
- Custom non-full-block branch geometry replaces vanilla log silhouettes on the OBJ tree library.
- Foliage uses a denser eight-card 3D cluster instead of cubic vanilla leaf blocks.
- Species-specific PBR roughness and foliage subsurface values are retained for Vibrant Visuals.
- Structures are rotated randomly during world generation and remain optimized for Android/iOS.
- Build validation checks all seven OBJ structures, species-specific palettes, textures and Bedrock 1.26.45 minimum targeting.

## Runtime approach

The original OBJ meshes are source art, not direct runtime models. They are too dense for practical mobile Bedrock world generation, so the build pipeline measures/reconstructs their silhouettes into custom branch nodes, foliage cards and `.mcstructure` templates. This preserves the recognizable tree form while keeping the pack usable on mobile devices.

## Compatibility

- Minecraft Bedrock **1.26.45+** only.
- Android and iOS are primary targets.
- Resource Pack enables Bedrock's `pbr` capability for Vibrant Visuals.
- No experimental toggle is intentionally required by the current v0.3.2 content.

## Roadmap

- **v0.3.3 — Tree Form Pass:** stronger roots, more irregular trunk thickness, extra branch-node geometry and per-tree foliage density tuning.
- **v0.4 — Plant Library:** dry grass, reeds, cattails, ivy, moss, bramble, wildflowers, mushrooms and additional forest-floor vegetation.
- **v0.5 — Survival & Optimization:** saplings, growth logic, loot, leaf behavior, biome density presets and mobile performance profiles.
- **v1.0 — Full Nature Release:** polished worldgen, complete nature library, compatibility testing and release packaging.

## Namespace

All custom content uses the `dlavie:` namespace.
