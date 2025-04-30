Feature: Loops support

Scenario: Regular loops should iterate collections in parallel
  Given I run adhesive on 'processes/loop/loop-default'
  Then the adhesive process has passed

Scenario: Parallel loops should iterate collections in parallel
  Given I run adhesive on 'processes/loop/loop-parallel'
  Then the adhesive process has passed

@manualtest
Scenario: Serial loops should iterate collections serially
  Given I run adhesive on 'processes/loop/loop-serial'
  Then the adhesive process has passed

@manualtest
Scenario: Parallel loops should iterate conditions serially with a warning
  Given I run adhesive on 'processes/loop/loop-parallel-condition'
  Then the adhesive process has passed
  And there is in the stdout the text 'CONDITION check detected'

@manualtest
Scenario: Serial loops should iterate collections serially using the condition,
    not the collection
  Given I run adhesive on 'processes/loop/loop-serial-condition'
  Then the adhesive process has passed

Scenario: An empty collection loop should continue to the next task without
        executing the looped task
  Given I run adhesive on 'processes/loop/loop-default-empty'
  Then the adhesive process has passed

Scenario: An empty condition loop should continue to the next task without
        executing the looped task
  Given I run adhesive on 'processes/loop/loop-condition-empty'
  Then the adhesive process has passed

Scenario: Nested loops should execute correctly
  Given I run adhesive on 'processes/loop/loop-nested'
  Then the adhesive process has passed

Scenario: Expressions should be accessible from the loop in the step implementation
  Given I run adhesive on 'processes/loop/loop-expression'
  Then the adhesive process has passed
