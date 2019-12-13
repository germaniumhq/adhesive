Feature: Generating message events should trigger the tasks executions

@1
Scenario: Run a workflow that generates 10 messages
    When I run adhesive on 'processes/message/basic-read'
    Then the adhesive process has passed
    And there is in the stdout the text 'Run  Process Event'
    And there is in the stdout the text 'event data: 0'
    And there is in the stdout the text 'event data: 1'
    And there is in the stdout the text 'event data: 2'
    And there is in the stdout the text 'event data: 3'
    And there is in the stdout the text 'event data: 4'
    And there is in the stdout the text 'event data: 5'
    And there is in the stdout the text 'event data: 6'
    And there is in the stdout the text 'event data: 7'
    And there is in the stdout the text 'event data: 8'
    And there is in the stdout the text 'event data: 9'

@2
@noprocess
Scenario: Run the deduplication process sync
    When I run adhesive on 'processes/message/deduplication'
    Then the adhesive process has passed

@3
@noprocess
Scenario: Run the deduplication process async
    When I run adhesive on 'processes/message/deduplication-async'
    Then the adhesive process has passed
