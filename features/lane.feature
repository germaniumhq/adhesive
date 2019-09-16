Feature: BPMN lanes are supported, and allow creating workspaces
    whenever execution tokens are entering the lane. The workspaces are
    kept alive as long as there are tasks that still use them.

@1 @manualtest
Scenario: A lane can keep a docker container up for the required
    commands.
  Given I run adhesive on 'processes/lane/docker'
  Then the adhesive process has passed

@2
Scenario: A lane ran in a loop is not instantiated for the starting of the
    loop event.
  Given I run adhesive on 'processes/lane/parametrized_loop_workspace'
  Then the adhesive process has passed


