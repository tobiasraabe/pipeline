from pony import orm


db = orm.Database()


class Hash(db.Entity):
    task = orm.Required(str)
    dependency = orm.Required(str)
    hash_ = orm.Required(str)

    orm.PrimaryKey(task, dependency)


def create_database(config):
    try:
        db.bind(**config["db"])
        db.generate_mapping(create_tables=True)
    except orm.BindingError:
        pass
