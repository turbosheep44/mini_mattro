
# based on
#   https://gist.github.com/econchick/4666413
# but modified because we need every edge to have an 'owner'

from collections import defaultdict
from math import inf


class Graph:
    def __init__(self):
        self.nodes = set()
        self.edges = defaultdict(set)
        self.distances = {}
        self.owners = {}

    def add_node(self, value: int):
        self.nodes.add(value)

    def add_edge(self, src: int, dst: int, distance: float = inf, owner=None):
        """
            add an edge to the graph, only if it is shorter than the current edge distance
        """
        self.edges[src].add(dst)

        key = (src, dst)
        # do nothing if the current distance is shorter than this
        if key in self.distances and self.distances[key] < distance:
            return

        # set distance and owner
        self.distances[key] = distance
        self.owners[key] = owner

    def dijsktra(self, initial):
        """
            SSSP (single source shortest path) from `initial`
        """

        # inisialise
        visited = {initial: 0}
        path = {}
        path_owners = {}
        nodes = set(self.nodes)  # duplicate nodes which will be destroyed

        while nodes:
            min_node = None
            for node in nodes:
                if node in visited:
                    if min_node is None:
                        min_node = node
                    elif visited[node] < visited[min_node]:
                        min_node = node

            if min_node is None:
                break

            nodes.remove(min_node)
            current_weight = visited[min_node]

            for edge in self.edges[min_node]:
                weight = current_weight + self.distances[(min_node, edge)]
                if edge not in visited or weight < visited[edge]:
                    visited[edge] = weight
                    path[edge] = min_node
                    path_owners[edge] = self.owners[(min_node, edge)]

        return visited, path, path_owners

    def shortest(self, src: int, dst_list: 'list[int]'):
        """
            finds the shortest path between `src` and any element of `dst_list`

            returns `dst: int`, `total_cost: float`, `path: list[int]`, `owners: list[int]`

            returns `None` if there is no path between `src` and any element of `dst_list`
        """

        # SSSP on src
        reachable, path, edge_owners = self.dijsktra(src)

        # if none reachable, then return None
        if all(dst not in reachable for dst in dst_list):
            return None

        # find which is the closest destination
        dst_list = [dst for dst in dst_list if dst in reachable]  # filter unreachable
        distances = [reachable[dst] for dst in dst_list]  # get cost of each reachable

        closest_dst, cost = dst_list[0], distances[0]
        for i in range(1, len(dst_list)):
            if distances[i] < cost:
                cost = distances[i]
                closest_dst = dst_list[i]

        path_stations = [closest_dst]
        owners = []
        current = closest_dst
        while current in path:
            path_stations.insert(0, path[current])
            owners.insert(0, edge_owners[current])
            current = path[current]

        return closest_dst, cost, path_stations, owners
