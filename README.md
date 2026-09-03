# DLavie Conquest Nature

A Minecraft Bedrock nature add-on focused on organic, realistic trees and plants reconstructed from high-detail OBJ source art.

> Current version: **v0.3.3 — Tree Form Pass**  
> Required game version: **Minecraft Bedrock 1.26.45+**

## v0.3.3 highlights

- Corrected the OBJ runtime semantic mapping: woody/trunk voxels and canopy voxels are now assigned to the proper runtime materials.
- Seven mobile-optimized tree silhouettes remain in the runtime library: Oak, Walnut, Mossy Tree, Small Bark Tree, Sonnerat, Tall Bark Tree and Giant Tree.
- Added irregular custom trunk geometry instead of a full vanilla log silhouette.
- Added directional branch geometries for X, Z and both diagonal directions so branch chains read more naturally in 3D.
- Added visible buttress/root geometry around the base of every tree, with larger root spread on Giant, Mossy and Tall variants.
- Expanded every structure footprint with extra horizontal margin so roots and branch forms are not clipped by the original OBJ bounding box.
- Added three canopy profiles: sparse, medium and dense. Each species receives a different foliage-card count and deterministic canopy fill rate.
- Giant and Mossy trees use the densest foliage profile; Tall and Small Bark trees remain lighter and more open.
- Structure feature adjustment radius is increased for the new root footprint.
- Species-specific bark/foliage textures and Vibrant Visuals PBR settings from v0.3.2 are retained.
- Build validation now checks the new trunk/root/leaf palettes, form geometries, all seven structures and the Bedrock 1.26.45 minimum target.

## Runtime approach

The supplied OBJ meshes are treated as high-detail source art rather than direct runtime models. The build pipeline reconstructs their voxel silhouette into optimized `.mcstructure` templates and then applies a second form pass that identifies trunk paths, directional branches, roots and canopy regions.

This approach keeps the recognisable proportions of the source trees while avoiding the cost of shipping hundreds of thousands of OBJ faces into a mobile Bedrock world.

## Compatibility

- Minecraft Bedrock **1.26.45+** only.
- Android and iOS are primary targets.
- Resource Pack enables Bedrock's `pbr` capability for Vibrant Visuals.
- No experimental toggle is intentionally required by the current v0.3.3 content.

## Roadmap

- **v0.3.4 — Tree Polish:** improve branch classification from local topology, add bark/end-grain variation and tune worldgen spacing after in-game screenshots.
- **v0.4 — Plant Library:** dry grass, reeds, cattails, ivy, moss, bramble, wildflowers, mushrooms and additional forest-floor vegetation.
- **v0.5 — Survival & Optimization:** saplings, growth logic, loot, leaf behavior, biome density presets and mobile performance profiles.
- **v1.0 — Full Nature Release:** polished worldgen, complete nature library, compatibility testing and release packaging.

## Namespace

All custom content uses the `dlavie:` namespace.
