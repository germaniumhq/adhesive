from adhesive.graph.BaseTask import BaseTask


class ScriptTask(BaseTask):
    def __init__(self,
                 _id: str,
                 name: str,
                 language: str) -> None:
        super(ScriptTask, self).__init__(_id, name)
        self.language = language
