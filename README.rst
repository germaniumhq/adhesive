adhesive
========

A CI/CD system build around BPMN and Python. Basically a BPMN runner
with pyhton step implementations targeted for builds. Can run in the
console.

Installation
------------

.. code:: sh

    pip install adhesive

User Tasks
----------

In order to create user interactions, you can create UserTasks. These
will define form elements that will be populated in the
``context.data``, and available in subsequent tasks.

User tasks support the following API, available on the ``ui`` parameter,
the parameter sent after the context.

.. code:: py

    class UiBuilderApi(ABC):
        def add_input_text(self,
                           name: str,
                           title: Optional[str] = None,
                           value: str = '') -> None:

        def add_input_password(self,
                               name: str,
                               title: Optional[str] = None,
                               value: str = '') -> None:

        def add_combobox(self,
                         name: str,
                         title: Optional[str] = None,
                         value: Optional[str]=None,
                         values: Optional[Iterable[Union[Tuple[str, str], str]]]=None) -> None:

        def add_checkbox_group(
                self,
                name: str,
                title: Optional[str]=None,
                value: Optional[Iterable[str]]=None,
                values: Optional[Iterable[Union[Tuple[str, str], str]]]=None) -> None:

        def add_radio_group(self,
                            name: str,
                            title: Optional[str]=None,
                            value: Optional[str]=None,
                            values: Optional[List[Any]]=None) -> None:

        def add_default_button(self,
                               name: str,
                               title: Optional[str]=None) -> None:

When a UserTask is encountered in the process flow, the user will be
prompted to fill in the various parameters. Note that all the other
tasks will continue running, proceeding forward with the build.

Configuration
-------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

``ADHESIVE_TEMP_FOLDER`` - Implicitly points to ``/tmp/adhesive``. Is
where all the builds files will be stored.
