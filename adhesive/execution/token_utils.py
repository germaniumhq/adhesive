from typing import List, Dict, Optional

import traceback
import logging

from .ExecutionToken import ExecutionToken

LOG = logging.getLogger(__name__)

# contains utility functions that deal with execution tokens routing providing:
# 1. an eval context for functions executions,
# 2. a naming resolving function
# 3. a name matching

def parse_name(context: ExecutionToken,
               name: str) -> str:
    """
    Parse the name of a task, or a lane depending on the
    current event token.
    """
    try:
        eval_data = get_eval_data(context)
        return name.format(**eval_data)
    except Exception as e:
        # LOG.warn(f"Failed to parse name {e}")
        return name


def get_eval_data(context: ExecutionToken) -> Dict:
    """
    Obtain a dict that can be passed into the local of an
    eval/exec statement from an execution token.
    """
    evaldata = dict(context.data._data)
    context = context.as_mapping()

    evaldata.update(context)

    return evaldata


def matches(re_expressions: List,
            resolved_name: str) -> Optional[List[str]]:
    """
    Checks if this implementation matches any of the expressions bounded to
    this resolved name. If yes, it returns the potential variables extracted
    from the expression.
    :param context:
    :return:
    """
    for re_expression in re_expressions:
        m = re_expression.match(resolved_name)

        if m:
            return list(m.groups())

    return None

