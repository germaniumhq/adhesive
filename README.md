# adhesive

A CI/CD system build around BPMN and Python. Basically a BPMN runner with
pyhton step implementations targeted for builds. Built to run in the console.

## Installation

```sh
pip install adhesive
```

## User Tasks

In order to create user interactions, you can create UserTasks. These will
define form elements that will be populated in the `context.data`, and
available in subsequent tasks.

User tasks support the following API, available on the `ui` parameter, the
parameter sent after the context.

```py
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
```

When a UserTask is encountered in the process flow, the user will be prompted
to fill in the various parameters. Note that all the other tasks will continue
running, proceeding forward with the build.

## Configuration

Adhesive supports configuration via its config files, or environment variables.
The values are read in the following order:

1. environment variables: `ADHESIVE_XYZ`, then
2. values that are in the project config yml file: `.adhesive/config.yml`, then
3. values configured in the global config yml file:
   `$HOME/.adhesive/config.yml`.

Currently the following values are defined for configuration:

### `temp_folder`

default value `/tmp/adhesive`, environment var: `ADHESIVE_TEMP_FOLDER`.

Is where all the build files will be stored.

### `plugins`

default value `[]`, environment var: `ADHESIVE_PLUGINS_LIST`.

This contains a list of folders, that will be added to the `sys.path`. So to
create a reusable plugin that will be reused by multiple builds, you need to
simply create a folder with python files, then point to it in the
`~/.adhesive/config.yml`:

```yml
plugins:
- /path/to/folder
```

Then in the python path you can simply do regular imports.

