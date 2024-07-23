from pathlib import Path

import yaml

repositories = set()


def add_repository_from_update_yaml(update: dict):
    if 'github' not in update:
        return
    github = update['github']
    if 'identifier' not in github:
        return
    identifier = github['identifier']
    repositories.add(identifier)


def add_repository_from_pipeline_yaml(pipeline: dict):
    if 'steps' not in pipeline:
        return
    pipeline_steps = pipeline['steps']
    for step in pipeline_steps:
        if 'uses' not in step:
            continue
        uses = step['uses']
        if 'git-checkout' != uses:
            continue
        if 'with' not in step:
            continue
        with_ = step['with']
        if 'repository' not in with_:
            continue
        repository = with_['repository']
        # Remove the https://github.com prefix
        repository = repository.replace('https://github.com/', '')
        repositories.add(repository)


def main():
    wolf_path = Path("../../wolfi-dev-os").absolute()
    # List all YAML files in this directory
    for file in wolf_path.glob('*.yaml'):
        with open(file) as package_descriptor_file:
            package_descriptor = yaml.safe_load(package_descriptor_file)
            if 'update' in package_descriptor:
                update = package_descriptor['update']
                add_repository_from_update_yaml(update)

            if 'pipeline' in package_descriptor:
                pipeline = package_descriptor['pipeline']
                add_repository_from_pipeline_yaml(pipeline)

    sorted_repositories = sorted(repositories)

    for repo in sorted_repositories:
        print(repo)


if __name__ == '__main__':
    main()
