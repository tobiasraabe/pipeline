from pipeline.dag import create_dag
from pipeline.database import create_database
from pipeline.execution import execute_dag_parallelly
from pipeline.execution import execute_dag_serially
from pipeline.tasks import process_tasks
from pipeline.tasks import replace_missing_templates_with_correct_paths
from pipeline.templates import collect_templates


def build_project(config):
    create_database(config)

    tasks = process_tasks(config)
    env, missing_templates = collect_templates(config["custom_templates"], tasks)
    tasks = replace_missing_templates_with_correct_paths(tasks, missing_templates)

    dag = create_dag(tasks, config)

    if config["n_jobs"] == 1:
        execute_dag_serially(dag, env, config)
    else:
        execute_dag_parallelly(dag, env, config)

    return dag
