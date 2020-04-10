from adhesive import config


@property
def is_enabled():
    return not config.current.boolean.stdout
