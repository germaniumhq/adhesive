Feature: Messages in the task title should use the context variable
    interpolation.

Scenario: Run a workflow that interpolates messages on the task execution
    When I run adhesive on 'processes/bugs/message_interpolation'
    Then the adhesive process has passed
    And there is in the stdout the text 'Resolved Value'


