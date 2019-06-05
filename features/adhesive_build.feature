Feature: adhesive.build support
  Processes that do a simple `adhesive.build` should work as expected.

@1
Scenario: An adhesive.build workflow that runs a task in parallel
  Given I run adhesive on 'processes/programmatic/adhesive_build_loop'
  Then the adhesive process has passed


@2
Scenario: A programmatic workflow that runs a task after an empty loop
  Given I run adhesive on 'processes/programmatic/adhesive_build_loop_task_after'
  Then the adhesive process has passed
