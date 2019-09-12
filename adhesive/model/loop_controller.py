from .ActiveEvent import ActiveEvent


def is_top_loop_event(event: ActiveEvent):
    return event.task.loop and (not event.context.loop or event.context.loop.task != event.task)

