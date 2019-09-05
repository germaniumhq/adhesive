Feature: SSH workspaces can be executed

Scenario: Running some task via SSH should work
  When I run adhesive on 'processes/workspace_ssh'
  Then the adhesive process has passed

