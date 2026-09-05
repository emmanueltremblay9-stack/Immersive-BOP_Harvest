# Dependency classification — 2026-09-05

Evidence: `gradle.properties`, `src/main/templates/META-INF/neoforge.mods.toml`,
`spec/coverage_inventory.json`; official CurseForge file pages linked below.
Classification uses the actual target loader contract, not only origin in BOP's
dependency graph. All five are explicitly required/BOTH in this target's TOML.

| Mod | Pinned version | Classification | CF ID / slug | Intended upload / public type |
|---|---|---|---|---|
| Biomes O' Plenty | 21.1.0.14 | DIRECT_RUNTIME_DEPENDENCY | 220318 / biomes-o-plenty | requiredDependency / RequiredDependency |
| GlitchCore | 2.1.0.2 | DIRECT_RUNTIME_DEPENDENCY (also transitive through BOP) | 955399 / glitchcore | requiredDependency / RequiredDependency |
| TerraBlender | 4.1.0.8 | DIRECT_RUNTIME_DEPENDENCY (also transitive through BOP) | 940057 / terrablender-neoforge | requiredDependency / RequiredDependency |
| Farmer's Delight | 1.3.2 | DIRECT_RUNTIME_DEPENDENCY | 398521 / farmers-delight | requiredDependency / RequiredDependency |
| Immersive Engineering | 12.4.2-194 | DIRECT_RUNTIME_DEPENDENCY | 231951 / immersive-engineering | requiredDependency / RequiredDependency |

None of these five is merely provenance or optional under current metadata.
Minecraft/NeoForge are platform/game-version labels, not uploaded mod relations.
The reference publisher's incorporated source projects are PROVENANCE_ONLY for
that separate project and must not leak into this target's active configuration.

Official file/project identity sources (read 2026-09-05):
- https://www.curseforge.com/minecraft/mc-mods/biomes-o-plenty/files/8288121
- https://www.curseforge.com/minecraft/mc-mods/glitchcore/files/8109792
- https://www.curseforge.com/minecraft/mc-mods/terrablender-neoforge/files/6054947
- https://www.curseforge.com/minecraft/mc-mods/farmers-delight/files/8083481
- https://www.curseforge.com/minecraft/mc-mods/immersive-engineering/files/6733669

The TerraBlender project is specifically the NeoForge project, not the distinct
Forge project. File IDs here identify dependencies, not the target publication.
No exact-name target project configuration was established; absence of a search
result is not proof that no private/unindexed target project can exist.
