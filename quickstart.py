import argparse
import os
import socket
import subprocess
import sys
import textwrap
import venv

from logger_setup import setup_custom_logger
from templates import (
    DEFAULT_YAML,
    COMPONENTS,
    GRAFANA,
    INFLUXDB,
    CROSSBAR,
    SCRIPTS,
)


logger = setup_custom_logger(__name__)


def clone_repository(repo_url: str, clone_directory: str) -> None:
    logger.info("Starting repository cloning...")
    if not os.path.exists(clone_directory):
        subprocess.run(["git", "clone", repo_url, clone_directory], check=True)
        logger.info("Repository cloned to %s", clone_directory)
    else:
        logger.info("Repository directory %s already exists.", clone_directory)


def handle_requirements_file(
    requirements_file: str, reverse: bool = False
) -> None:
    logger.info("Handling requirements file...")
    if not os.path.exists(requirements_file):
        logger.error("File does not exist.")
        return

    with open(requirements_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    with open(requirements_file, "w", encoding="utf-8") as file:
        for line in lines:
            stripped_line = line.strip()
            if not reverse and stripped_line == "-r requirements/testing.txt":
                file.write(f"# {line}")
            elif reverse and stripped_line == "# -r requirements/testing.txt":
                file.write(line[2:])
            else:
                file.write(line)


def setup_virtual_environment(environment_directory: str) -> str:
    logger.info("Setting up virtual environment...")
    if not os.path.exists(environment_directory):
        venv.create(environment_directory, with_pip=True)
        logger.info("Virtual environment created at %s", environment_directory)
    else:
        logger.info(
            "Virtual environment already exists at %s", environment_directory
        )

    python_executable = (
        os.path.join(environment_directory, "Scripts", "python.exe")
        if sys.platform == "win32"
        else os.path.join(environment_directory, "bin", "python")
    )

    subprocess.run(
        [python_executable, "-m", "pip", "install", "--upgrade", "pip"],
        check=True,
    )
    logger.info("pip has been upgraded to the latest version.")
    return python_executable


def install_requirements(
    python_executable: str, requirements_file: str, clone_directory: str
) -> None:
    logger.info("Installing requirements...")
    if os.path.exists(requirements_file):
        subprocess.run(
            [
                python_executable,
                "-m",
                "pip",
                "install",
                "-r",
                requirements_file,
                f"{clone_directory}/.",
            ],
            check=True,
        )
        logger.info("Requirements installed.")
    else:
        logger.error("Requirements file '%s' not found.", requirements_file)


def setup_configurations(
    config_directory: str, hostname: str, grafana_image: str
) -> None:
    """
    Sets up the required directories and creates YAML configuration files for each component.

    Args:
        config_directory (str): The base directory for configuration files.
        hostname (str): The hostname to be used in the configuration files.
        grafana_image (str): The Grafana Docker image to use.
    """
    paths = (
        config_directory,
        os.path.join(config_directory, "grafana"),
        os.path.join(config_directory, "influxdb"),
        os.path.join(config_directory, "crossbar"),
    )
    filenames = ("default.yaml", "docker-compose.yaml")
    # Generate iteratively? meh
    configurations = (
        (paths[0], filenames[0], DEFAULT_YAML),
        (
            paths[0],
            filenames[1],
            COMPONENTS,
        ),
        (
            paths[1],
            filenames[1],
            GRAFANA,
        ),
        (
            paths[2],
            filenames[1],
            INFLUXDB,
        ),
        (
            paths[3],
            filenames[1],
            CROSSBAR,
        ),
    )

    # Create directories and YAML configuration files for each component
    for [path, filename, template] in configurations:
        os.makedirs(path, exist_ok=True)
        create_yaml_configuration(
            path, hostname, filename, template, grafana_image
        )


def create_yaml_configuration(
    directory_name: str,
    hostname: str,
    file_name: str,
    content_template: str,
    grafana_image: str,
) -> None:
    content = textwrap.dedent(
        content_template.format(
            hostname=hostname,
            config_directory=os.path.abspath(directory_name),
            user=hostname,
            grafana_image=grafana_image,
        )
    )
    with open(
        os.path.join(directory_name, file_name), "w", encoding="utf-8"
    ) as file:
        file.write(content)
    logger.info(
        "YAML file %s created in %s.", file_name, os.path.join(directory_name)
    )


def setup_bridge_network(network_name: str = "ocs-net"):
    logger.info("Setting up Docker network...")
    try:
        existing_networks = (
            subprocess.check_output(
                ["docker", "network", "ls", "--format", "{{.Name}}"]
            )
            .decode()
            .splitlines()
        )
        if network_name not in existing_networks:
            subprocess.run(
                [
                    "docker",
                    "network",
                    "create",
                    "--driver",
                    "bridge",
                    network_name,
                ],
                check=True,
            )
            logger.info(
                "Docker network '%s' successfully created.", network_name
            )
        else:
            logger.info("Docker network '%s' already exists.", network_name)
    except subprocess.CalledProcessError as e:
        error_message = (
            e.output.decode().strip() if e.output else "Is Docker running?"
        )
        logger.error(
            "Failed to list or create Docker network. Error: %s", error_message
        )


def create_up_down_scripts(directory_name: str) -> None:
    logger.info("Creating up/down scripts...")
    for script_name, script_content in SCRIPTS.items():
        file_path = os.path.join(directory_name, script_name)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(script_content)
            logger.info("Script %s created at %s", script_name, file_path)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Set up OCS configuration")
    parser.add_argument(
        "--grafana-image",
        default="grafana/grafana:latest",
        help="Grafana Docker image to use (default: grafana/grafana:latest)",
    )
    return parser.parse_args()


def main():
    args = parse_arguments()

    repo_url = "https://github.com/simonsobs/ocs.git"
    clone_directory = "ocs"
    requirements_file = os.path.join(clone_directory, "requirements.txt")
    environment_directory = ".venv"
    config_directory = "ocs-site-configs"
    hostname = socket.gethostname()

    clone_repository(repo_url, clone_directory)
    handle_requirements_file(requirements_file, False)
    python_executable = setup_virtual_environment(environment_directory)
    install_requirements(python_executable, requirements_file, clone_directory)
    handle_requirements_file(requirements_file, True)
    setup_configurations(config_directory, hostname, args.grafana_image)
    setup_bridge_network()
    create_up_down_scripts(config_directory)


if __name__ == "__main__":
    main()
