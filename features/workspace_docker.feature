Feature: SSH workspaces can be executed

@1
Scenario: Running a failing command in docker throws exception
  When I run adhesive on 'processes/docker/failing_command'
  Then the adhesive process has failed
