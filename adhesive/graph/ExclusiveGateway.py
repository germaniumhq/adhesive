from adhesive.graph.Gateway import Gateway


class ExclusiveGateway(Gateway):
    def __init__(self,
                 _id: str,
                 name: str) -> None:
        super(ExclusiveGateway, self).__init__(_id, name)
