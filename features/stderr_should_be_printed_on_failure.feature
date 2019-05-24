Feature: If a task throws an exception I don't need to drill into the logs folder.


Scenario: Run a workflow that fails with an exception
    When I run adhesive on 'processes/stderror_handling'
    Then the adhesive process has failed
    And there is in the stderr the text 'Custom exception was thrown'
    And there is in the stderr the text 'throw_some_exception'

