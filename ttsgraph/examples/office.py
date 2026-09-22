from typing import Optional
from ttsgraph import Graph, ActionNode


def main():

    # TODO: fancier schedule structure...
    schedule: list[str] = [
        "lunch today",
        "2pm tomorrow",
        "next week",
    ]
    current_appointment: Optional[str] = None

    graph = Graph()

    graph.static('root', "Main menu",
        options={1: 'hours', 2: 'schedule'})

    graph.message('hours', "Office hours",
        "The office is open between 8AM and 12PM.")

    @graph.dynamic('schedule', "Schedule of appointments")
    def _(self, graph):
        options = {'back': 'root'}
        options[1] = 'schedule_choose'
        if current_appointment is not None:
            text = f"Currently scheduled for: {current_appointment}."
            options[2] = 'schedule_unselect'
        else:
            text = "No appointment currently scheduled."
        return (text, options)

    @graph.dynamic('schedule_choose', "Choose appointment")
    def _(self, graph):
        options = {'back': 'schedule'}
        for i, appointment in enumerate(schedule, 1):
            def func(node, graph):
                nonlocal current_appointment
                current_appointment = node.name
                graph.say_okay()
                return 'schedule'
            options[i] = ActionNode(appointment, func)
        return (None, options)

    @graph.action('schedule_unselect', "Cancel appointment")
    def _(self, graph):
        nonlocal current_appointment
        current_appointment = None
        graph.say_okay()
        return 'schedule'

    graph.loop('root')


if __name__ == '__main__':
    main()
