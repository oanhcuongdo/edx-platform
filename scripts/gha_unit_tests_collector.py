import sys
import os
import yaml
import argparse
import json


def get_all_unit_test_shards():
    unit_tests_json = f'{os.getcwd()}/.github/workflows/unit-test-shards.json'
    with open(unit_tests_json) as file:
        unit_test_workflow_shards = json.loads(file.read())

    return unit_test_workflow_shards


def get_unit_test_modules(module_name="lms"):
    unit_test_modules = set()
    all_unit_test_shards = get_all_unit_test_shards()
    for shard_name, shard_confing in all_unit_test_shards.items():
        if shard_confing.get('path')[0].startswith('cms') and module_name == "cms":
            unit_test_modules.update(shard_confing.get('path'))
        elif not shard_confing.get('path')[0].startswith("cms") and module_name != "cms":
            unit_test_modules.update(shard_confing.get('path'))
    return unit_test_modules


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cms-only", action="store_true", default="")
    parser.add_argument("--lms-only", action="store_true", default="")
    argument = parser.parse_args()

    if not argument.cms_only and not argument.lms_only:
        print("Please specify --cms-only or --lms-only")
        sys.exit(1)

    modules = get_unit_test_modules("cms") if argument.cms_only else get_unit_test_modules("lms")
    paths_output = ' '.join(modules)
    sys.stdout.write(paths_output)
