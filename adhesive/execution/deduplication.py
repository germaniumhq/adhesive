from typing import Optional, cast

import addict
import logging

from adhesive.execution.token_utils import get_eval_data
from adhesive.graph.ProcessTask import ProcessTask
from adhesive.model.ActiveEvent import ActiveEvent


LOG = logging.getLogger(__name__)


def get_deduplication_id(
    event: ActiveEvent,
) -> Optional[str]:
    expression = cast(ProcessTask, event.task).deduplicate

    if expression is None:
        return None

    eval_data = addict.Dict(get_eval_data(event.context))
    deduplication_id = eval(
        expression,
        {},
        eval_data)

    if not deduplication_id:
        LOG.warning(f"Deduplication returned a falsy object for {expression}. "
                    f"The return was {deduplication_id}.")

    return deduplication_id
