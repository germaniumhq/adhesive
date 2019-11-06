import adhesive


@adhesive.task('First task')
def first_task(context):
    pass


@adhesive.task('Second task')
def second_task(context):
    pass


@adhesive.task('Third task')
def third_task(context):
    pass


adhesive.process_start()\
    .task('First task')\
    .task('Second task', when="data.not_skip")\
    .task('Third task')\
    .process_end()\
    .build()
