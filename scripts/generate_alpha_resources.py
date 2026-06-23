#!/usr/bin/env python3
"""Generate the playable-alpha data pack resources from spec/*.json."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "spec"
RESOURCES = ROOT / "src" / "main" / "resources"
DATA = RESOURCES / "data"
MOD_ID = "immersive_bop_harvest"


def load(name: str):
    return json.loads((SPEC / name).read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def clean_generated() -> None:
    targets = [
        DATA / MOD_ID / "recipe" / "cutting",
        DATA / MOD_ID / "recipe" / "sawmill",
        DATA / MOD_ID / "loot_modifiers" / "direct_harvest",
        DATA / MOD_ID / "loot_table" / "direct_harvest",
        DATA / "neoforge" / "loot_modifiers",
    ]
    for target in targets:
        if target.exists():
            shutil.rmtree(target)
    for tag in [
        DATA / "c" / "tags" / "item" / "crops" / "grain.json",
        DATA / "c" / "tags" / "item" / "mushrooms.json",
    ]:
        if tag.exists():
            tag.unlink()


def path_name(identifier: str) -> str:
    return identifier.split(":", 1)[1].replace("/", "_")


def item_result(item: str, count: int = 1) -> dict:
    return {"item": {"count": count, "id": item}}


def cutting_recipe(source: str, outputs: list[dict], tool: list[dict], sound: str | None = None) -> dict:
    recipe = {
        "type": "farmersdelight:cutting",
        "ingredients": [{"item": source}],
        "result": outputs,
        "tool": tool,
    }
    if sound:
        recipe["sound"] = {"sound_id": sound}
    return recipe


KNIFE_TOOL = [
    {"type": "farmersdelight:item_ability", "action": "knife_dig"},
    {"tag": "c:tools/knife"},
]

AXE_STRIP_TOOL = [
    {"type": "farmersdelight:item_ability", "action": "axe_strip"},
    {"tag": "minecraft:axes"},
]


def generate_cutting_recipes() -> int:
    count = 0
    for recipe in load("flower_cutting_recipes.json")["recipes"]:
        source = recipe["source"]
        out = [item_result(recipe["output"], recipe.get("count", 1))]
        write_json(DATA / MOD_ID / "recipe" / "cutting" / f"{path_name(source)}.json", cutting_recipe(source, out, KNIFE_TOOL))
        count += 1

    for recipe in load("plant_cutting_recipes.json")["recipes"]:
        source = recipe["source"]
        out = [item_result(row["item"], row.get("count", 1)) for row in recipe["outputs"]]
        write_json(DATA / MOD_ID / "recipe" / "cutting" / f"{path_name(source)}.json", cutting_recipe(source, out, KNIFE_TOOL))
        count += 1

    for family in load("wood_families.json")["families"]:
        for key, stripped_key in (("log", "stripped_log"), ("wood", "stripped_wood")):
            source = family[key]
            out = [item_result(family[stripped_key]), item_result("farmersdelight:tree_bark")]
            write_json(
                DATA / MOD_ID / "recipe" / "cutting" / f"{path_name(source)}.json",
                cutting_recipe(source, out, AXE_STRIP_TOOL, "minecraft:item.axe.strip"),
            )
            count += 1
    return count


def generate_sawmill_recipes() -> int:
    count = 0
    for family in load("wood_families.json")["families"]:
        for key, stripped_key in (("log", "stripped_log"), ("wood", "stripped_wood")):
            source = family[key]
            recipe = {
                "type": "immersiveengineering:sawmill",
                "energy": 1600,
                "input": {"item": source},
                "result": {"count": 6, "id": family["planks"]},
                "secondaryOutputs": [{"tag": "c:dusts/wood"}],
                "stripped": {"id": family[stripped_key]},
                "strippingSecondaries": [{"tag": "c:dusts/wood"}],
            }
            write_json(DATA / MOD_ID / "recipe" / "sawmill" / f"{path_name(source)}.json", recipe)
            count += 1

        recipe = {
            "type": "immersiveengineering:sawmill",
            "energy": 800,
            "input": [{"item": family["stripped_log"]}, {"item": family["stripped_wood"]}],
            "result": {"count": 6, "id": family["planks"]},
            "secondaryOutputs": [{"tag": "c:dusts/wood"}],
            "strippingSecondaries": [],
        }
        write_json(DATA / MOD_ID / "recipe" / "sawmill" / f"stripped_{family['family']}.json", recipe)
        count += 1
    return count


def match_tool(tag: str) -> dict:
    return {"condition": "minecraft:match_tool", "predicate": {"items": tag}}


def tool_condition(tools: list[str]) -> dict:
    terms = [match_tool(tool) for tool in tools]
    if len(terms) == 1:
        return terms[0]
    return {"condition": "minecraft:any_of", "terms": terms}


def not_condition(term: dict) -> dict:
    return {"condition": "minecraft:inverted", "term": term}


def silk_touch_condition() -> dict:
    return {
        "condition": "minecraft:match_tool",
        "predicate": {
            "predicates": {
                "minecraft:enchantments": [
                    {
                        "enchantments": "minecraft:silk_touch",
                        "levels": {"min": 1},
                    }
                ]
            }
        },
    }


def loot_table(output: str, count: int) -> dict:
    entry = {"type": "minecraft:item", "name": output}
    if count != 1:
        entry["functions"] = [{"function": "minecraft:set_count", "count": count}]
    return {"type": "minecraft:block", "pools": [{"rolls": 1, "entries": [entry]}]}


def generate_direct_harvest() -> int:
    entries: list[str] = []
    count = 0
    for rule in load("direct_harvest_rules.json")["rules"]:
        for block in rule["blocks"]:
            name = path_name(block)
            table_id = f"{MOD_ID}:direct_harvest/{name}"
            modifier_id = f"{MOD_ID}:direct_harvest/{name}"
            conditions = []
            if rule["chance"] < 1.0:
                conditions.append({"condition": "minecraft:random_chance", "chance": rule["chance"]})
            conditions.extend(
                [
                    tool_condition(rule["tools_any"]),
                    not_condition(match_tool("#c:tools/shear")),
                    not_condition(silk_touch_condition()),
                    {"condition": "minecraft:block_state_property", "block": block},
                ]
            )
            state_condition = rule.get("state_condition")
            if state_condition:
                conditions[-1]["properties"] = {k: str(v) for k, v in state_condition.items()}

            write_json(
                DATA / MOD_ID / "loot_modifiers" / "direct_harvest" / f"{name}.json",
                {"type": "neoforge:add_table", "conditions": conditions, "table": table_id},
            )
            write_json(DATA / MOD_ID / "loot_table" / "direct_harvest" / f"{name}.json", loot_table(rule["output"], rule["count"]))
            entries.append(modifier_id)
            count += 1

    write_json(DATA / "neoforge" / "loot_modifiers" / "global_loot_modifiers.json", {"replace": False, "entries": entries})
    return count


def generate_tags() -> int:
    tag_count = 0
    for integration in load("tag_integrations.json")["integrations"]:
        namespace, path = integration["tag"].split(":", 1)
        write_json(DATA / namespace / "tags" / "item" / f"{path}.json", {"replace": False, "values": integration["values"]})
        tag_count += 1
    return tag_count


def main() -> int:
    clean_generated()
    counts = {
        "cutting_recipes": generate_cutting_recipes(),
        "sawmill_recipes": generate_sawmill_recipes(),
        "direct_harvest_modifiers": generate_direct_harvest(),
        "item_tags": generate_tags(),
    }
    for key, value in counts.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
