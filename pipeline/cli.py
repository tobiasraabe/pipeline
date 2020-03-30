"""This module comprises all CLI capabilities of pipeline."""
import pprint
import shutil

import click

from pipeline.config import load_config
from pipeline.main import build_project
from pipeline.tasks import process_tasks
from pipeline.templates import collect_templates

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
@click.version_option()
def cli(ctx):
    """Command-line interface for pipeline."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config()


@cli.command()
@click.option("--config", is_flag=True)
@click.option("--tasks", is_flag=True)
@click.option("--templates", is_flag=True)
@click.pass_context
def collect(ctx, config, tasks, templates):
    if config:
        pprint.pprint(ctx.obj["config"])
    if tasks:
        click.echo(process_tasks(ctx.obj["config"]))
    if templates:
        custom_templates = ctx.obj["config"].get("custom_templates", None)
        pprint.pprint(collect_templates(custom_templates)[0].list_templates())


@cli.command()
@click.pass_context
@click.option("--debug", is_flag=True)
@click.option("-n", "--n-jobs", default=1, type=int, help="Number of parallel jobs.")
def build(ctx, debug, n_jobs):
    """Build the project."""
    click.echo("### Build Project")
    ctx.obj["config"]["is_debug"] = debug
    ctx.obj["config"]["n_jobs"] = n_jobs
    build_project(ctx.obj["config"])
    click.echo("### Finished")


@cli.command()
@click.pass_context
def clean(ctx):
    """Clean the project."""
    shutil.rmtree(ctx.obj["config"]["build_directory"], ignore_errors=True)
