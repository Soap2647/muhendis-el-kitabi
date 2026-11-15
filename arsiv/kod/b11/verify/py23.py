u, v = u_of_edge, v_of_edge
# add nodes
if u not in self._node:
    if u is None:
        raise ValueError("None cannot be a node")
    self._adj[u] = self.adjlist_inner_dict_factory()
    self._node[u] = self.node_attr_dict_factory()
if v not in self._node:
    if v is None:
        raise ValueError("None cannot be a node")
    self._adj[v] = self.adjlist_inner_dict_factory()
    self._node[v] = self.node_attr_dict_factory()
# add the edge
datadict = self._adj[u].get(v, self.edge_attr_dict_factory())
datadict.update(attr)
self._adj[u][v] = datadict
self._adj[v][u] = datadict
