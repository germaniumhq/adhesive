import adhesive
import unittest

test = unittest.TestCase()


@adhesive.task('Hello .*?')
def hello_loop_value_(context):
	pass


@adhesive.lane('server\: .*?')
def lane_server_loop_value_(context):
	context.data.lane_names = set()
	context.data.lane_names.add(context.lane.name)

	yield context.workspace.clone()


data = adhesive.bpmn_build("parametrized-loop-workspace.bpmn",
	initial_data={
		"items": ["a", "b", "c"],
	})

test.assertEqual(data.lane_names, {
	"server: a",
	"server: b",
	"server: c",
}, "the lane was not created correctly for all the iterations")
