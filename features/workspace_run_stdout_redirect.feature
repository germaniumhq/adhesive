Feature: STDOUT can be captured when running tasks

Scenario: Capturing the stdout should work in a taks
  When I run adhesive on 'processes/workspace_run_stdout_capture'
  Then the adhesive process has passed
