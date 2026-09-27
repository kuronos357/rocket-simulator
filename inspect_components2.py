import trimesh
import numpy as np
from scipy.sparse import csgraph

m12 = trimesh.load("export/つくば＿ロケット v12.stl")

# face adjacency graph
edges = m12.face_adjacency
n_faces = len(m12.faces)
matrix = csgraph.csgraph_from_dense(np.zeros((1, 1))) # dummy
from scipy.sparse import coo_matrix
row = edges[:, 0]
col = edges[:, 1]
data = np.ones(len(edges), dtype=bool)
adj = coo_matrix((data, (row, col)), shape=(n_faces, n_faces))
n_comp, labels = csgraph.connected_components(adj, directed=False)

print(f"Total connected components in v12 STL: {n_comp}")
for i in range(n_comp):
    faces_i = m12.faces[labels == i]
    verts_idx = np.unique(faces_i)
    verts_i = m12.vertices[verts_idx]
    y_min, y_max = verts_i[:, 1].min(), verts_i[:, 1].max()
    x_min, x_max = verts_i[:, 0].min(), verts_i[:, 0].max()
    z_min, z_max = verts_i[:, 2].min(), verts_i[:, 2].max()
    print(f"Comp {i}: {len(faces_i)} faces, Y=[{y_min:.1f}, {y_max:.1f}], X=[{x_min:.1f}, {x_max:.1f}], Z=[{z_min:.1f}, {z_max:.1f}]")
