#!/usr/bin/env python3
"""Build docker image
    less BASH more Python

    ©2024, Ovais Quraishi
"""

import logging
from pathlib import Path

import docker

from shared.config import read_config, CaseSensitiveConfigParser, CONFIG_FILE

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_config():
    """Returns the parsed configuration object as a dictionary."""
    config = read_config(CONFIG_FILE)
    return config.raw_config if config.raw_config else {}


def get_ver():
    """Get version from ver.txt file."""
    with open('ver.txt', 'r') as file:
        content = file.read()
    return content.strip()


def create_docker_client(engine, remote_host=None, remote_port=22):
    """Create Docker client for local or remote engine.

    Args:
        engine: 'local' or 'remote'
        remote_host: SSH host string (e.g., 'user@1.2.3.4')
        remote_port: SSH port number

    Returns:
        Docker client instance
    """
    if engine == "remote":
        if not remote_host:
            raise ValueError("remote_host must be specified when engine is 'remote'")
        docker_host_str = f"ssh://{remote_host}:{remote_port}"
        logger.info("Connecting to remote Docker engine at %s", docker_host_str)
        client = docker.DockerClient(base_url=docker_host_str)
    else:
        logger.info("Connecting to local Docker engine")
        client = docker.from_env()
    return client


def build_docker_container(client, dockerfile_path, image_name, tag="latest", build_args=None):
    """Build docker container.

    Args:
        client: Docker client instance
        dockerfile_path: Path to Dockerfile directory
        image_name: Name for the Docker image
        tag: Tag for the Docker image
        build_args: Build arguments dictionary
    """
    try:
        logger.info("Building Docker image %s:%s from %s...", image_name, tag, dockerfile_path)
        _, logs = client.images.build(
            path=dockerfile_path,
            tag=f"{image_name}:{tag}",
            rm=True,
            buildargs=build_args,
            quiet=True
        )

        for log in logs:
            if 'stream' in log:
                logger.info(log['stream'].strip())

        logger.info("Docker image %s:%s built successfully!", image_name, tag)
        get_this_image = client.images.get(f"{image_name}:{tag}")
        get_this_image.tag(f"{image_name}:latest")

    except docker.errors.BuildError as e:
        logger.error("Failed to build Docker image %s:%s: %s", image_name, tag, e)

    except docker.errors.APIError as e:
        logger.error("Docker API error while building image %s:%s: %s", image_name, tag, e)


if __name__ == "__main__":
    dockerfile_path = str(Path().absolute())
    image_name = "rollama"
    tag = get_ver()
    build_args = get_config()

    # === Engine selection ===
    # Set these values as needed:
    engine = "remote"  # or "local"
    remote_host = "<user>@<ip-or-fqdn>"  # e.g. ec2-user@1.2.3.4
    remote_port = 22  # default SSH port, change if needed

    client = create_docker_client(engine, remote_host, remote_port)
    build_docker_container(client, dockerfile_path, image_name, tag, build_args)
