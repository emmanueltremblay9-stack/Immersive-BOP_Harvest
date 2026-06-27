#!/usr/bin/env python3
"""Validate generated alpha resources against the project QA gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "spec"
RESOURCES = ROOT / "src" / "main" / "resources"
DATA = RESOURCES / "data"
MOD_ID = "immersive_bop_harvest"
BOP_SHEARS_TAG = "#biomesoplenty:shears"

errors: list[str] = []


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
        return None


def load_spec(name: str):
    return load_json(SPEC / name) or {}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def path_name(identifier: str) -> str:
    return identifier.split(":", 1)[1].replace("/", "_")


def item_result(item: str, count: int = 1) -> dict:
    return {"item": {"count": count, "id": item}}


def expect(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def read_generated(path: Path):
    expect(path.exists(), f"missing generated file: {rel(path)}")
    if not path.exists():
        return {}
    value = load_json(path)
    return value if isinstance(value, dict) else {}


def normalize_values(values: list[dict]) -> list[dict]:
    return sorted(values, key=lambda row: json.dumps(row, sort_keys=True))


def has_tool_tag(recipe: dict, tag: str) -> bool:
    return any(entry.get("tag") == tag for entry in recipe.get("tool", []))


def has_tool_ability(recipe: dict, action: str) -> bool:
    return any(entry.get("type") == "farmersdelight:item_ability" and entry.get("action") == action for entry in recipe.get("tool", []))


def condition_contains(value, needle: str) -> bool:
    if isinstance(value, str):
        return value == needle
    if isinstance(value, list):
        return any(condition_contains(item, needle) for item in value)
    if isinstance(value, dict):
        return any(condition_contains(item, needle) for item in value.values())
    return False


def collect_json_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.json") if path.is_file())


def validate_cutting_recipes(wood: dict, flowers: dict, plants: dict) -> int:
    cutting_dir = DATA / MOD_ID / "recipe" / "cutting"
    generated = collect_json_files(cutting_dir)

    expected_count = len(flowers.get("recipes", [])) + len(plants.get("recipes", [])) + (2 * len(wood.get("families", [])))
    expect(len(generated) == expected_count, f"cutting recipe count mismatch: expected {expected_count}, found {len(generated)}")

    seen_sources: set[str] = set()
    for row in flowers.get("recipes", []):
        source = row["source"]
        expect(source not in seen_sources, f"duplicate cutting source: {source}")
        seen_sources.add(source)
        recipe = read_generated(cutting_dir / f"{path_name(source)}.json")
        expected = [item_result(row["output"], row.get("count", 1))]
        expect(recipe.get("type") == "farmersdelight:cutting", f"{source}: wrong cutting recipe type")
        expect(recipe.get("ingredients") == [{"item": source}], f"{source}: ingredient does not match spec source")
        expect(normalize_values(recipe.get("result", [])) == normalize_values(expected), f"{source}: flower dye output does not match spec")
        expect(has_tool_tag(recipe, "c:tools/knife"), f"{source}: missing knife tag")
        expect(has_tool_ability(recipe, "knife_dig"), f"{source}: missing knife_dig ability")

    for row in plants.get("recipes", []):
        source = row["source"]
        expect(source not in seen_sources, f"duplicate cutting source: {source}")
        seen_sources.add(source)
        recipe = read_generated(cutting_dir / f"{path_name(source)}.json")
        expected = [item_result(item["item"], item.get("count", 1)) for item in row["outputs"]]
        expect(recipe.get("type") == "farmersdelight:cutting", f"{source}: wrong cutting recipe type")
        expect(recipe.get("ingredients") == [{"item": source}], f"{source}: ingredient does not match spec source")
        expect(normalize_values(recipe.get("result", [])) == normalize_values(expected), f"{source}: plant output does not match spec")
        expect(has_tool_tag(recipe, "c:tools/knife"), f"{source}: missing knife tag")
        expect(has_tool_ability(recipe, "knife_dig"), f"{source}: missing knife_dig ability")

    for family in wood.get("families", []):
        for key, stripped_key in (("log", "stripped_log"), ("wood", "stripped_wood")):
            source = family[key]
            recipe = read_generated(cutting_dir / f"{path_name(source)}.json")
            expected = [item_result(family[stripped_key]), item_result("farmersdelight:tree_bark")]
            expect(recipe.get("type") == "farmersdelight:cutting", f"{source}: wrong wood cutting recipe type")
            expect(recipe.get("ingredients") == [{"item": source}], f"{source}: ingredient does not match wood source")
            expect(normalize_values(recipe.get("result", [])) == normalize_values(expected), f"{source}: wood stripping output mismatch")
            expect(recipe.get("sound") == {"sound_id": "minecraft:item.axe.strip"}, f"{source}: missing axe strip sound")
            expect(has_tool_tag(recipe, "minecraft:axes"), f"{source}: missing axes tag")
            expect(has_tool_ability(recipe, "axe_strip"), f"{source}: missing axe_strip ability")

    return len(generated)


def validate_sawmill_recipes(wood: dict) -> int:
    sawmill_dir = DATA / MOD_ID / "recipe" / "sawmill"
    generated = collect_json_files(sawmill_dir)
    expected_count = 3 * len(wood.get("families", []))
    expect(len(generated) == expected_count, f"sawmill recipe count mismatch: expected {expected_count}, found {len(generated)}")

    for recipe_path in generated:
        recipe = load_json(recipe_path) or {}
        expect(recipe.get("type") == "immersiveengineering:sawmill", f"{rel(recipe_path)}: unexpected recipe type")

    for family in wood.get("families", []):
        for key, stripped_key in (("log", "stripped_log"), ("wood", "stripped_wood")):
            source = family[key]
            recipe = read_generated(sawmill_dir / f"{path_name(source)}.json")
            expect(recipe.get("energy") == 1600, f"{source}: unstripped sawmill energy must be 1600")
            expect(recipe.get("input") == {"item": source}, f"{source}: sawmill input mismatch")
            expect(recipe.get("result") == {"count": 6, "id": family["planks"]}, f"{source}: sawmill result mismatch")
            expect(recipe.get("secondaryOutputs") == [{"tag": "c:dusts/wood"}], f"{source}: missing wood dust secondary")
            expect(recipe.get("stripped") == {"id": family[stripped_key]}, f"{source}: stripped output mismatch")
            expect(recipe.get("strippingSecondaries") == [{"tag": "c:dusts/wood"}], f"{source}: missing stripping secondary")

        stripped = read_generated(sawmill_dir / f"stripped_{family['family']}.json")
        expected_inputs = [{"item": family["stripped_log"]}, {"item": family["stripped_wood"]}]
        expect(stripped.get("energy") == 800, f"{family['family']}: stripped sawmill energy must be 800")
        expect(normalize_values(stripped.get("input", [])) == normalize_values(expected_inputs), f"{family['family']}: stripped sawmill inputs mismatch")
        expect(stripped.get("result") == {"count": 6, "id": family["planks"]}, f"{family['family']}: stripped sawmill result mismatch")
        expect(stripped.get("secondaryOutputs") == [{"tag": "c:dusts/wood"}], f"{family['family']}: missing stripped wood dust secondary")
        expect("stripped" not in stripped, f"{family['family']}: stripped recipe must not strip again")
        expect(stripped.get("strippingSecondaries") == [], f"{family['family']}: stripped recipe must not have stripping secondaries")

    return len(generated)


def validate_direct_harvest(harvest: dict) -> tuple[int, int]:
    modifier_dir = DATA / MOD_ID / "loot_modifiers" / "direct_harvest"
    table_dir = DATA / MOD_ID / "loot_table" / "direct_harvest"
    index = read_generated(DATA / "neoforge" / "loot_modifiers" / "global_loot_modifiers.json")
    expected_entries: list[str] = []
    expected_blocks: set[str] = set()

    expect(index.get("replace") is False, "global loot modifier index must use replace=false")

    for rule in harvest.get("rules", []):
        for block in rule.get("blocks", []):
            expected_blocks.add(block)
            name = path_name(block)
            modifier_id = f"{MOD_ID}:direct_harvest/{name}"
            table_id = f"{MOD_ID}:direct_harvest/{name}"
            expected_entries.append(modifier_id)

            modifier = read_generated(modifier_dir / f"{name}.json")
            table = read_generated(table_dir / f"{name}.json")
            conditions = modifier.get("conditions", [])
            serialized_conditions = json.dumps(conditions, sort_keys=True)

            expect(modifier.get("type") == "neoforge:add_table", f"{block}: modifier must use neoforge:add_table")
            expect(modifier.get("table") == table_id, f"{block}: modifier table id mismatch")
            expect(condition_contains(conditions, block), f"{block}: modifier missing block_state_property condition")
            expect(any(condition_contains(conditions, tool) for tool in rule["tools_any"]), f"{block}: modifier missing required tool condition")
            expect(condition_contains(conditions, BOP_SHEARS_TAG), f"{block}: modifier missing BOP shears exclusion")
            expect("#c:tools/shear" not in serialized_conditions, f"{block}: modifier must not rely on the unsupported c:tools/shear tag")
            expect("silk_touch" in serialized_conditions, f"{block}: modifier missing Silk Touch exclusion")
            expect("fortune" not in serialized_conditions.lower(), f"{block}: modifier must not include Fortune scaling")

            if rule["chance"] < 1.0:
                expect(any(entry.get("condition") == "minecraft:random_chance" and entry.get("chance") == rule["chance"] for entry in conditions), f"{block}: random chance mismatch")
            else:
                expect(not any(entry.get("condition") == "minecraft:random_chance" for entry in conditions), f"{block}: chance 1.0 should not add random_chance")

            block_state_conditions = [entry for entry in conditions if isinstance(entry, dict) and entry.get("condition") == "minecraft:block_state_property"]
            if rule.get("state_condition"):
                expected_state = {key: str(value) for key, value in rule["state_condition"].items()}
                expect(any(entry.get("properties") == expected_state for entry in block_state_conditions), f"{block}: state condition mismatch")

            pools = table.get("pools", [])
            entries = pools[0].get("entries", []) if pools else []
            expect(table.get("type") == "minecraft:block", f"{block}: loot table type mismatch")
            expect(len(pools) == 1 and pools[0].get("rolls") == 1, f"{block}: loot table must have one one-roll pool")
            expect(len(entries) == 1 and entries[0].get("name") == rule["output"], f"{block}: loot table output mismatch")
            functions = entries[0].get("functions", []) if entries else []
            if rule["count"] == 1:
                expect(functions == [], f"{block}: count 1 output must not add set_count")
            else:
                expect(functions == [{"function": "minecraft:set_count", "count": rule["count"]}], f"{block}: set_count mismatch")

    expect(index.get("entries") == expected_entries, "global loot modifier entries do not match generated modifier order")
    expect(len(collect_json_files(modifier_dir)) == len(expected_blocks), "direct-harvest modifier count mismatch")
    expect(len(collect_json_files(table_dir)) == len(expected_blocks), "direct-harvest loot table count mismatch")

    targeted = json.dumps(sorted(expected_blocks))
    expect("biomesoplenty:potted_" not in targeted, "potted blocks must not be targeted")
    expect("biomesoplenty:stringy_cobweb" not in expected_blocks, "stringy cobweb must remain unchanged")

    barley_name = path_name("biomesoplenty:barley")
    barley = read_generated(modifier_dir / f"{barley_name}.json")
    expect('"half": "lower"' in json.dumps(barley, sort_keys=True), "barley direct harvest must be lower-half only")

    webbing_table = read_generated(table_dir / f"{path_name('biomesoplenty:webbing')}.json")
    webbing_entry = webbing_table.get("pools", [{}])[0].get("entries", [{}])[0]
    expect(webbing_entry.get("name") == "minecraft:string", "webbing must output string")
    expect("functions" not in webbing_entry, "webbing must yield at most one string")

    return len(collect_json_files(modifier_dir)), len(collect_json_files(table_dir))


def validate_tags(tags: dict) -> int:
    count = 0
    for integration in tags.get("integrations", []):
        namespace, path = integration["tag"].split(":", 1)
        tag_path = DATA / namespace / "tags" / "item" / f"{path}.json"
        tag = read_generated(tag_path)
        expect(tag == {"replace": False, "values": integration["values"]}, f"{integration['tag']}: tag contents mismatch")
        count += 1
    return count


def validate_global_invariants(forbidden: dict) -> int:
    json_files = collect_json_files(RESOURCES)
    seen: set[str] = set()
    for path in json_files:
        load_json(path)
        rel_path = rel(path)
        expect(rel_path not in seen, f"duplicate generated path: {rel_path}")
        seen.add(rel_path)

    expect(not (DATA / "biomesoplenty").exists(), "generated files must not be written under data/biomesoplenty")

    all_resources = "\n".join(path.read_text(encoding="utf-8") for path in json_files)
    for forbidden_item in forbidden.get("forbidden", []):
        expect(forbidden_item not in all_resources, f"forbidden output appears in generated resources: {forbidden_item}")

    recipe_files = collect_json_files(DATA / MOD_ID / "recipe")
    recipe_types = {load_json(path).get("type") for path in recipe_files}
    expect(recipe_types <= {"farmersdelight:cutting", "immersiveengineering:sawmill"}, f"unexpected recipe types: {sorted(recipe_types)}")
    return len(json_files)


def main() -> int:
    wood = load_spec("wood_families.json")
    flowers = load_spec("flower_cutting_recipes.json")
    plants = load_spec("plant_cutting_recipes.json")
    harvest = load_spec("direct_harvest_rules.json")
    tags = load_spec("tag_integrations.json")
    forbidden = load_spec("forbidden_outputs.json")

    counts = {
        "generated_json_files": validate_global_invariants(forbidden),
        "cutting_recipes": validate_cutting_recipes(wood, flowers, plants),
        "sawmill_recipes": validate_sawmill_recipes(wood),
        "direct_harvest_modifiers": 0,
        "direct_harvest_loot_tables": 0,
        "item_tags": validate_tags(tags),
    }
    counts["direct_harvest_modifiers"], counts["direct_harvest_loot_tables"] = validate_direct_harvest(harvest)

    if errors:
        print("ALPHA RESOURCE QA: FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("ALPHA RESOURCE QA: PASSED")
    for key, value in counts.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
