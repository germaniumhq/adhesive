import adhesive


@adhesive.task('Prepare data')
def prepare_data(context):
    context.data.data_is_set = True


@adhesive.task('Run if data is set via attribute name')
def run_if_data_is_set_via_attribute_name(context):
    context.data.was_executed1 = True


@adhesive.task('Run if data is set via data.attribute')
def run_if_data_is_set_via_data_attribute(context):
    context.data.was_executed2 = True


@adhesive.task('Run if data is set via context.data.attribute')
def run_if_data_is_set_via_context_data_attribute(context):
    context.data.was_executed3 = True


data = adhesive.process_start()\
    .task("Prepare data")\
    .task("Run if data is set via attribute name", when="data_is_set")\
    .task("Run if data is set via data.attribute", when="data.data_is_set")\
    .task("Run if data is set via context.data.attribute", when="context.data.data_is_set")\
    .process_end()\
    .build()


assert data.was_executed1
assert data.was_executed2
assert data.was_executed3
