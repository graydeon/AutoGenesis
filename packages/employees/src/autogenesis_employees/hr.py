"""HR operations — hire, fire, train employees."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import structlog
import yaml

from autogenesis_employees.project import slugify

logger = structlog.get_logger()


def hire(
    title: str,
    based_on: str | None = None,
    template_dir: Path | None = None,
    target_dir: Path | None = None,
) -> Path:
    new_id = slugify(title)
    target_dir = target_dir or Path.cwd()
    target_path = target_dir / f"{new_id}.yaml"

    if target_path.exists():
        msg = f"Employee config already exists: {target_path}"
        raise FileExistsError(msg)

    if based_on and template_dir:
        base_path = template_dir / f"{based_on}.yaml"
        if base_path.exists():
            with base_path.open() as f:
                config = yaml.safe_load(f)
        else:
            config = {}
    else:
        config = {}

    config["id"] = new_id
    config["title"] = title
    config["status"] = "active"
    config["hired_at"] = datetime.now(UTC).strftime("%Y-%m-%d")
    config.setdefault("persona", f"You are a {title} at a tech startup.")
    config.setdefault("tools", [])
    config.setdefault("training_directives", [])
    config.setdefault("env", {"ROLE": new_id})

    target_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))
    logger.info("employee_hired", id=new_id, title=title)
    return target_path


def fire(employee_id: str, config_dir: Path | None = None) -> None:
    config_dir = config_dir or Path.cwd()
    path = config_dir / f"{employee_id}.yaml"
    if not path.exists():
        msg = f"Employee config not found: {path}"
        raise FileNotFoundError(msg)
    with path.open() as f:
        config = yaml.safe_load(f)
    config["status"] = "archived"
    path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))
    logger.info("employee_fired", id=employee_id)


def train(employee_id: str, directive: str, config_dir: Path | None = None) -> None:
    config_dir = config_dir or Path.cwd()
    path = config_dir / f"{employee_id}.yaml"
    if not path.exists():
        msg = f"Employee config not found: {path}"
        raise FileNotFoundError(msg)
    with path.open() as f:
        config = yaml.safe_load(f)
    directives = config.get("training_directives", [])
    directives.append(directive)
    config["training_directives"] = directives
    path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))
    logger.info("employee_trained", id=employee_id, directive=directive[:50])
