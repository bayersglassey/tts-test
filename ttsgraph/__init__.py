from typing import NamedTuple, Callable, Union, Optional


Node = Union['StaticNode', 'DynamicNode', 'ActionNode']

# Maps option names to node IDs or nodes
Options = dict[str, str | Node]

TextAndOptions = tuple[Optional[str], Options]
DynamicNodeFunc = Callable[['DynamicNode', 'Graph'], Optional[TextAndOptions]]

ActionNodeFunc = Callable[['ActionNode', 'Graph'], None]


class Graph:

    def __init__(self):
        self.nodes: dict[str, Node] = {}

    def static(self, id: str, name: str, *, text: str = None, options: Options):
        if id in self.nodes:
            raise Exception(f"Duplicate node id: {id!r}")
        self.nodes[id] = StaticNode(name, text, options)

    def dynamic(self, id: str, name: str):
        def decorator(func: DynamicNodeFunc) -> 'DynamicNode':
            if id in self.nodes:
                raise Exception(f"Duplicate node id: {id!r}")
            node = DynamicNode(name, func)
            self.nodes[id] = node
            return node
        return decorator

    def action(self, id: str, name: str):
        def decorator(func: ActionNodeFunc) -> 'ActionNode':
            if id in self.nodes:
                raise Exception(f"Duplicate node id: {id!r}")
            node = ActionNode(name, func)
            self.nodes[id] = node
            return node
        return decorator

    def message(self, id: str, name: str, text: str) -> 'ActionNode':
        @self.action(id, name)
        def node(self, graph):
            graph.say(text)
        return node

    def confirm(self, message: str = "Are you sure?") -> bool:
        """Helper method, e.g. for use by dynamic and action nodes"""
        self.say(message)
        response = self.listen()
        return response in ('yes', 'yeah', 'okay', 'ok')

    def say(self, msg: str):
        # TODO: add an audio interface
        print(msg)

    def listen(self) -> str:
        # TODO: add an audio interface
        return input('> ')

    def say_okay(self):
        self.say("Okay.")

    def loop(self, start: Union[str, 'Node']):
        node = self.nodes[start] if isinstance(start, str) else start
        node = node.resolve(self)
        try:
            self._loop(node)
        except KeyboardInterrupt:
            pass

    def _loop(self, node: 'Node'):
        while True:

            # Display node's name and text (if any)
            self.say(f"This is {node.name}.")
            if node.text is not None:
                self.say(node.text)

            # HACK: convert node's options' keys to strings...
            # In particular we allow nodes' options' keys to be ints.
            # Really we should do this conversion when creating nodes, or
            # something.
            options = {str(k): self.nodes[v] if isinstance(v, str) else v
                for k, v in node.options.items()}

            # Tell user about the options
            self.say("The options here are:")
            for option, next_node in options.items():
                self.say(f"{option} is {next_node.name}.")

            # Get an option from user
            option = self.listen()

            # Try to map the option onto a node
            next_node = None
            if option in options:
                next_node = options[option]
            else:
                for maybe_next_node in options.values():
                    if option == maybe_next_node.name:
                        next_node = maybe_next_node
                        break

            # Maybe go to the node user selected?..
            if next_node is not None:
                # Resolve the node, i.e. allow it to perform side effects,
                # and potentially return a different node, or None if we
                # should stay on the current node.
                next_node = next_node.resolve(self)
                if next_node is not None:
                    # Resolving the node may have only had a
                    # side effect (see ActionNode), in which
                    # case we stay at the same node
                    node = next_node
            else:
                self.say("Not an option.")


class StaticNode(NamedTuple):
    """Simplest kind of node"""

    name: str
    text: Optional[str]
    options: Options

    def resolve(self, graph: Graph) -> Optional['StaticNode']:
        return self


class DynamicNode(NamedTuple):
    """Node which dynamically generates its text and options"""

    name: str
    func: DynamicNodeFunc

    def resolve(self, graph: Graph) -> Optional['StaticNode']:
        text_and_options = self.func(self, graph)
        if text_and_options is None:
            return None
        text, options = text_and_options
        return StaticNode(self.name, text, options)


class ActionNode(NamedTuple):
    """Node which only has a side effect, you can't "be at" it"""

    name: str
    func: ActionNodeFunc

    def resolve(self, graph: Graph) -> Optional['StaticNode']:
        node = self.func(self, graph)
        if node is not None:
            node = graph.nodes[node] if isinstance(node, str) else node
            node = node.resolve(graph)
        return node
