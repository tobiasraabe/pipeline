from pony import orm


db = orm.Database()


class Hash(db.Entity):
    task = orm.Required(str)
    dependency = orm.Required(str)
    hash_ = orm.Required(str)

    orm.PrimaryKey(task, dependency)


class TaskOutput(db.Entity):
    task = orm.Required(str)
    target = orm.Required(str)
    data = orm.Required(orm.buffer)

    orm.PrimaryKey(task, target)


def create_database(config):
    db.bind(**config["db"])
    db.generate_mapping(create_tables=True)
