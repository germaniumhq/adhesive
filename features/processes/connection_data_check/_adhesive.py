import adhesive


@adhesive.task('Prepare data')
def prepare_data(context):
    context.data.data_is_set = True


@adhesive.task('Run if data is set')
def run_if_data_is_set(context):
    context.data.was_executed = True


data = adhesive.process_start()\
    .task("Prepare data")\
    .task("Run if data is set",
          when="data_is_set")\
    .process_end()\
    .build()


assert data.was_executed
