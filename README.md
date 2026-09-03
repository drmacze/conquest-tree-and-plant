# DLavie Conquest Nature

A Bedrock Edition nature add-on focused on **organic, Conquest-inspired trees and plants** without redistributing Conquest Reforged assets.

> Status: early development / v0.1 foundation.
> Required game version: **Minecraft Bedrock 1.26.45 or newer**.

## Current prototype

The first implementation contains:
- Behavior Pack + Resource Pack manifests locked to `min_engine_version: [1, 26, 45]`
- Custom `forest_fern` and `meadow_grass` vegetation blocks
- A custom three-plane `leaf_cluster` geometry for less cubic foliage
- A custom `branch_log` block
- Woodland and ancient oak world-generation features
- Weighted tree selection
- Modern 1.21.20+ scatter/distribution schema for forest-floor generation
- Forest biome feature rules
- Build validation that rejects manifests targeting anything other than Bedrock 1.26.45

This is intentionally a functional foundation. The current texture atlas points at vanilla Bedrock textures so the pack can be tested before the original DLavie art pass is added.

## Repository layout

```text
behavior_pack/
  blocks/
  features/
  feature_rules/
  manifest.json

resource_pack/
  models/blocks/
  textures/
  manifest.json

docs/
  ROADMAP.md
```

## Target

- Minecraft Bedrock **1.26.45+**
- Android and iOS
- Survival-friendly trees
- Dense but optimized forests
- Original DLavie visual assets
- Vibrant Visuals / PBR-ready art direction
- No dependency on experimental toggles unless a future feature explicitly requires one

## Compatibility policy

Both pack manifests use `min_engine_version: [1, 26, 45]`. The build script validates this target and also requires custom block definitions to use the 1.26-era block schema so accidental compatibility regressions are caught before a package is produced.

## Namespace

All custom content uses the `dlavie:` namespace.

## Development note

The project is inspired by the visual language of realistic Minecraft foliage. It is not a redistribution or direct port of Conquest Reforged's copyrighted models or textures.
