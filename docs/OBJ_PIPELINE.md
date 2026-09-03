# v0.3 OBJ Tree Pipeline

Minecraft Bedrock does not consume arbitrary `.obj` files as ordinary block geometry. v0.3 therefore treats OBJ files as **source art**, not runtime assets.

## Pipeline

1. Import the local ZIP with `tools/import_obj_tree_pack.py`.
2. Split every `o` object into an individual standalone OBJ while preserving UVs and material references.
3. Measure bounds and topology for each tree.
4. Build an optimized Bedrock representation per tree:
   - woody silhouette -> branch/trunk segments and multi-block structure parts;
   - foliage -> clustered card geometry with alpha-tested textures;
   - textures -> Bedrock PNG/PBR texture sets;
   - worldgen -> structure/feature placement, not vanilla tree silhouettes.
5. Keep the original source OBJ outside the public repository unless its redistribution license explicitly permits publication.

## Performance policy

The source art can be much denser than a mobile Bedrock runtime asset. Each tree must therefore be reduced before shipping. The importer reports face/vertex counts and bounding boxes so a later optimization step can choose per-tree budgets.

The target remains **Minecraft Bedrock 1.26.45+ on Android and iOS**.

## Current source pack observation

The first provided OBJ pack is a combined Blender export with multiple tree objects, one MTL file, and texture atlases. It is suitable as a high-detail visual reference/source, but is far too dense to ship unchanged on mobile.
