Feature: Groups that should use a single checkbox, should still be fine.


@manualtest
Scenario: Run a workflow with a single checkbox.
    When I run adhesive on a workflow with a UT with a single checkbox
    Then the user task renders just fine

