Feature: cancel task support
    When a task is cancelled it should be stopped immediately

@1
Scenario: A task that cancels the current task in a timer
  Given I run adhesive on 'processes/cancel_boundary/simple'
  Then the adhesive process has passed

@2
Scenario: A task that cancels a subprocess in a timer
  Given I run adhesive on 'processes/cancel_boundary/subprocess'
  Then the adhesive process has passed

@3
Scenario: A task that cancels a nested subprocess in a timer
  Given I run adhesive on 'processes/cancel_boundary/nested-subprocess'
  Then the adhesive process has passed

