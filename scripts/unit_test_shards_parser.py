import sys
import os
import argparse
import json


def load_unit_test_shards(shard_name):
    unit_tests_json = f'{os.getcwd()}/.github/workflows/unit-test-shards.json'
    with open(unit_tests_json) as file:
        unit_test_workflow_shards = json.loads(file.read())
    if shard_name not in unit_test_workflow_shards:
        sys.stdout.write("Error, invalid shard name provided. please provide a valid shard name as specified in unit-test-shards.json")
    return unit_test_workflow_shards


def get_test_paths_for_shard(shard_name):
    return load_unit_test_shards(shard_name).get(shard_name).get("path")


def get_settings_for_shard(shard_name):
    return load_unit_test_shards(shard_name).get(shard_name).get("settings")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-name", action="store", default="")
    parser.add_argument("--output", action="store", default="path", choices=["path", "settings"])
    argument = parser.parse_args()

    if not argument.shard_name:
        sys.exit("Error, no shard name provided. please provide a valid shard name as specified in unit-test-shards.json")

    output = get_settings_for_shard(argument.shard_name) if argument.output == "settings" \
        else " ".join(get_test_paths_for_shard(argument.shard_name))
    sys.stdout.write(output)
