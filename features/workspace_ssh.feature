Feature: SSH workspaces can be executed

@1 @noprocess
Scenario: Running some task via SSH should work
  When I run adhesive on 'processes/ssh/workspace_ssh'
  Then the adhesive process has passed

@2 @noprocess
Scenario: Running some task via SSH in a lane should work
  When I run adhesive on 'processes/ssh/lane_workspace_ssh'
  Then the adhesive process has passed
