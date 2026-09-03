# DLavie Conquest Nature

A Bedrock Edition nature add-on focused on **organic, Conquest-inspired trees and plants** without redistributing Conquest Reforged assets.

> Status: early development / v0.1 foundation.

## Current prototype

The first implementation contains:
- Behavior Pack + Resource Pack manifests
- Custom `forest_fern` and `meadow_grass` vegetation blocks
- A custom three-plane `leaf_cluster` geometry for less cubic foliage
- A custom `branch_log` block
- Woodland and ancient oak world-generation features
- Weighted tree selection
- Forest-floor scattering
- Forest biome feature rules

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

- Minecraft Bedrock 1.26.x / 26.x generation
- Android and iOS
- Survival-friendly trees
- Dense but optimized forests
- Original DLavie visual assets
- Vibrant Visuals / PBR-ready art direction

## Namespace

All custom content uses the `dlavie:` namespace.

## Development note

The project is inspired by the visual language of realistic Minecraft foliage. It is not a redistribution or direct port of Conquest Reforged's copyrighted models or textures.
