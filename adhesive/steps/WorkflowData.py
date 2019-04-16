from typing import Optional, Dict


def merge_dict(dict1: Dict, dict2: Dict) -> None:
    for k2, v2 in dict2.items():
        if k2 not in dict1:
            dict1[k2] = v2
            continue

        v1 = dict1[k2]

        if isinstance(v1, list) and isinstance(v2, list):
            v1.extend(v2)
            continue

        if isinstance(v1, set) and isinstance(v2, set):
            v1.update(v2)
            continue

        if isinstance(v1, dict) and isinstance(v2, dict):
            merge_dict(v1, v2)
            continue

        raise Exception(f"Unable to merge '{k2}' with different types.")


class WorkflowData:
    def __init__(self,
                 initial_data: Optional[Dict] = None):
        self._data = dict(initial_data) if initial_data else dict()

    def as_dict(self) -> Dict:
        return self._data

    def __getattr__(self, item: str):
        if item.startswith("__") or item == '_data':
            return super(WorkflowData, self).__getattribute__(item)

        if item not in self._data:
            return None

        return self._data[item]

    def __setattr__(self, key, value):
        if key == "_data":
            super(WorkflowData, self).__setattr__(key, value)
            return

        self._data[key] = value

    @staticmethod
    def merge(*data_items: 'WorkflowData') -> 'WorkflowData':
        result = WorkflowData()

        for data in data_items:
            merge_dict(result._data, data._data)

        return result
