Feature: build support
    In order to create processes without a definition, just having the
    definitions of the tasks should assemble a very simple linear process.

@1
Scenario: A build process that runs a task in parallel
  Given I run adhesive on 'processes/build/build_loop'
  Then the adhesive process has passed

@2
Scenario: A build process that runs a task after a loop
  Given I run adhesive on 'processes/programmatic/build_loop_task_after'
  Then the adhesive process has passed

@3
Scenario: A build process that runs a loop inside a lane
  Gven I run adhesive on 'processes/programmatic/build_loop_lane'
  Then the adhesive process has passed

