from adhesive import config


is_enabled = not config.current.stdout and config.current.parallel_processing == 'process'

