Feature: Programmatic support
  Adhesive should allow creating workflows with simple
  commands, without having to always read a BPMN file.

@1
Scenario: A programmatic workflow that runs a task in parallel
  Given I run adhesive on 'processes/programmatic/parallel_tasks'
  Then the adhesive process has passed
