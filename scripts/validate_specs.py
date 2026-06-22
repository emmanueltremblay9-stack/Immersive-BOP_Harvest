#!/usr/bin/env python3
"""Validate the Immersive BOP_Harvest machine-readable specification."""

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "spec"

ALLOWED_OUTPUT_NAMESPACES = {"minecraft", "farmersdelight", "immersiveengineering"}
FORBIDDEN = set(json.loads((SPEC / "forbidden_outputs.json").read_text(encoding="utf-8"))["forbidden"])

errors = []
warnings = []

def load(name):
    try:
        return json.loads((SPEC / name).read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{name}: cannot parse JSON: {exc}")
        return {}

def namespace(identifier):
    if ":" not in identifier:
        return None
    return identifier.split(":", 1)[0]

def check_identifier(identifier, where):
    if not isinstance(identifier, str) or ":" not in identifier:
        errors.append(f"{where}: invalid namespaced ID {identifier!r}")

wood = load("wood_families.json")
flowers = load("flower_cutting_recipes.json")
plants = load("plant_cutting_recipes.json")
harvest = load("direct_harvest_rules.json")
tags = load("tag_integrations.json")
coverage = load("coverage_inventory.json")

families = wood.get("families", [])
if len(families) != 13:
    errors.append(f"wood_families.json: expected 13 families, found {len(families)}")

family_names = [f.get("family") for f in families]
if len(family_names) != len(set(family_names)):
    errors.append("wood_families.json: duplicate family name")

required_wood_fields = {
    "family", "saplings", "leaves", "log", "stripped_log", "wood",
    "stripped_wood", "planks", "stairs", "slab", "fence", "fence_gate",
    "door", "trapdoor", "pressure_plate", "button", "sign", "wall_sign",
    "hanging_sign", "wall_hanging_sign"
}
for idx, fam in enumerate(families):
    missing = required_wood_fields - set(fam)
    if missing:
        errors.append(f"wood family #{idx}: missing {sorted(missing)}")
    for key, value in fam.items():
        if key == "family":
            continue
        if isinstance(value, str):
            check_identifier(value, f"wood family {fam.get('family')}:{key}")
        elif isinstance(value, list):
            for item in value:
                check_identifier(item, f"wood family {fam.get('family')}:{key}")

cutting_sources = set()
for section_name, recipes in (
    ("flower_cutting_recipes.json", flowers.get("recipes", [])),
    ("plant_cutting_recipes.json", plants.get("recipes", []))
):
    for recipe in recipes:
        src = recipe.get("source")
        check_identifier(src, f"{section_name}:source")
        if src in cutting_sources:
            errors.append(f"duplicate Cutting Board source: {src}")
        cutting_sources.add(src)
        if "output" in recipe:
            outputs = [{"item": recipe["output"], "count": recipe.get("count", 1)}]
        else:
            outputs = recipe.get("outputs", [])
        for out in outputs:
            item = out.get("item")
            check_identifier(item, f"{section_name}:{src}:output")
            if namespace(item) not in ALLOWED_OUTPUT_NAMESPACES:
                errors.append(f"{section_name}:{src}: disallowed output namespace: {item}")
            if item in FORBIDDEN:
                errors.append(f"{section_name}:{src}: forbidden output: {item}")
            if not isinstance(out.get("count", 1), int) or out.get("count", 1) < 1:
                errors.append(f"{section_name}:{src}: invalid output count")

direct_blocks = set()
for rule in harvest.get("rules", []):
    chance = rule.get("chance")
    if not isinstance(chance, (int, float)) or not (0 <= chance <= 1):
        errors.append(f"direct harvest rule has invalid chance: {chance}")
    output = rule.get("output")
    check_identifier(output, "direct harvest output")
    if namespace(output) not in ALLOWED_OUTPUT_NAMESPACES:
        errors.append(f"direct harvest: disallowed namespace: {output}")
    if output in FORBIDDEN:
        errors.append(f"direct harvest: forbidden output: {output}")
    if not rule.get("tools_any"):
        errors.append(f"direct harvest rule for {rule.get('blocks')} has no tool condition")
    if not isinstance(rule.get("count"), int) or rule.get("count") < 1:
        errors.append(f"direct harvest rule for {rule.get('blocks')} has invalid count")
    for block in rule.get("blocks", []):
        check_identifier(block, "direct harvest block")
        if block in direct_blocks:
            errors.append(f"duplicate direct-harvest block: {block}")
        direct_blocks.add(block)
        if ":potted_" in block:
            errors.append(f"potted block targeted by direct harvest: {block}")

barley = [
    r for r in harvest.get("rules", [])
    if "biomesoplenty:barley" in r.get("blocks", [])
]
if len(barley) != 1 or barley[0].get("state_condition") != {"half": "lower"}:
    errors.append("barley must have exactly one lower-half-only direct-harvest rule")

webbing = [
    r for r in harvest.get("rules", [])
    if "biomesoplenty:webbing" in r.get("blocks", [])
]
if len(webbing) != 1 or webbing[0].get("output") != "minecraft:string" or webbing[0].get("count") != 1:
    errors.append("webbing must yield exactly one string")

# Build coverage ID set.
coverage_ids = set()
for key, rows in coverage.items():
    if not isinstance(rows, list):
        continue
    for row in rows:
        ident = row.get("id")
        if ident:
            check_identifier(ident, f"coverage:{key}")
            if ident in coverage_ids:
                warnings.append(f"coverage ID appears more than once: {ident}")
            coverage_ids.add(ident)

for source in cutting_sources:
    if source not in coverage_ids and source != "biomesoplenty:dead_branch":
        errors.append(f"Cutting source is not in coverage inventory: {source}")

for block in direct_blocks:
    if block not in coverage_ids:
        errors.append(f"Direct-harvest block is not in coverage inventory: {block}")

for integ in tags.get("integrations", []):
    tag = integ.get("tag")
    if not isinstance(tag, str) or ":" not in tag:
        errors.append(f"invalid tag ID: {tag}")
    for value in integ.get("values", []):
        check_identifier(value, f"tag {tag}")

if errors:
    print("SPEC VALIDATION: FAILED")
    for err in errors:
        print(f"ERROR: {err}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    sys.exit(1)

print("SPEC VALIDATION: PASSED")
print(f"Wood families: {len(families)}")
print(f"Flower/dye Cutting Board recipes: {len(flowers.get('recipes', []))}")
print(f"Plant/material Cutting Board recipes: {len(plants.get('recipes', []))}")
print(f"Direct-harvest rules: {len(harvest.get('rules', []))}")
print(f"Direct-harvest block IDs: {len(direct_blocks)}")
print(f"Coverage IDs: {len(coverage_ids)}")
if warnings:
    for warning in warnings:
        print(f"WARNING: {warning}")
