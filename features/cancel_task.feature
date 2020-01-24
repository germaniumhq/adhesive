Feature: cancel task support
    When a task is cancelled it should be stopped immediately

@1
Scenario: A task that cancels the current task in a timer
  Given I run adhesive on 'processes/cancel_boundary'
  Then the adhesive process has passed

