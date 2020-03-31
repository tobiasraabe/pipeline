"""This module comprises all CLI capabilities of pipeline."""
import shutil

import click

from pipeline.config import load_config
from pipeline.main import build_project
from pipeline.tasks import process_tasks
from pipeline.templates import collect_templates

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
def cli():
    """Command-line interface for pipeline."""
    pass


@cli.command()
@click.option("--configuration", is_flag=True)
@click.option("--tasks", is_flag=True)
@click.option("--templates", is_flag=True)
def collect(configuration, tasks, templates):
    config = load_config()
    if configuration:
        click.echo(config)
    if tasks:
        click.echo(process_tasks(config))
    if templates:
        custom_templates = config.get("custom_templates", None)
        click.echo(collect_templates(custom_templates)[0].list_templates())


@cli.command()
@click.option("--debug", is_flag=True, default=None)
@click.option("-n", "--n-jobs", default=None, type=int, help="Number of parallel jobs.")
@click.option("--priority", is_flag=True, help="Schedule tasks by priority.")
def build(debug, n_jobs, priority):
    """Build the project."""
    click.echo("### Build Project")
    config = load_config(debug, n_jobs, priority)
    build_project(config)
    click.echo("### Finished")


@cli.command()
def clean():
    """Clean the project."""
    config = load_config()
    shutil.rmtree(config["build_directory"], ignore_errors=True)
