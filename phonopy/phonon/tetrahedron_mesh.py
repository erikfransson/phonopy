# copyright (C) 2013 Atsushi Togo
# All rights reserved.
#
# This file is part of phonopy.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in
#   the documentation and/or other materials provided with the
#   distribution.
#
# * Neither the name of the phonopy project nor the names of its
#   contributors may be used to endorse or promote products derived
#   from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import numpy as np
from phonopy.phonon.mesh import shift2boolean, has_mesh_symmetry
from phonopy.structure.spglib import get_stabilized_reciprocal_mesh, relocate_BZ_grid_address
from phonopy.units import VaspToTHz

class TetrahedronMesh:
    def __init__(self,
                 dynamical_matrix,
                 mesh,
                 rotations, # Point group operations in real space
                 shift=None,
                 is_time_reversal=False,
                 is_symmetry=True,
                 is_eigenvectors=False,
                 is_gamma_center=False,
                 factor=VaspToTHz):
        self._dynamical_matrix = dynamical_matrix
        self._mesh = mesh
        self._rotations = rotations
        self._shift = shift
        self._is_time_reversal = is_time_reversal
        self._is_symmetry = is_symmetry
        self._is_gamma_center = is_gamma_center
        self._is_eigenvectors = is_eigenvectors
        self._factor = factor

        self._cell = dynamical_matrix.get_primitive()
        self._frequencies = None
        self._eigenvalues = None
        self._eigenvectors = None
        # self._set_eigenvalues()

        self._set_grid_points()

    def _set_grid_points(self):
        mesh = self._mesh
        
        if not self._is_symmetry:
            print "Disabling mesh symmetry is not supported."
        assert has_mesh_symmetry(mesh, self._rotations), \
            "Mesh numbers don't have proper symmetry."
            
        self._is_shift = shift2boolean(mesh,
                                       q_mesh_shift=self._shift,
                                       is_gamma_center=self._is_gamma_center)

        if not self._is_shift:
            print "Only mesh shift of 0 or 1/2 is allowed."
            print "Mesh shift is set [0, 0, 0]."

        self._gp_map, self._grid_address = get_stabilized_reciprocal_mesh(
            mesh,
            self._rotations,
            is_shift=self._is_shift,
            is_time_reversal=self._is_time_reversal)

        if self._grid_address[1][0] == 1:
            grid_order = [1, mesh[0], mesh[0] * mesh[1]]
        else:
            grid_order = [mesh[2] * mesh[1], mesh[2], 1]

        grid_address_with_boundary, bz_gp_map = relocate_BZ_grid_address(
            self._grid_address,
            mesh,
            np.linalg.inv(self._cell.get_cell()),
            is_shift=self._is_shift)

        shift = [s * 0.5 for s in self._is_shift]
        qpoints = (grid_address_with_boundary + shift) / mesh
        # for q in np.dot(qpoints, np.linalg.inv(self._cell.get_cell()).T):
        #     print q[0], q[1], q[2]
        
        multiplicities = np.zeros(len(grid_address_with_boundary), dtype='intc')
        gp_with_boundary = np.dot(grid_address_with_boundary % mesh, grid_order)
        for gp in gp_with_boundary:
            multiplicities[gp] += 1
        for i in range(np.prod(mesh), len(multiplicities)):
            multiplicities[i] = multiplicities[gp_with_boundary[i]]


        
        ## This is probably unnecessary.
        # bz_grid_address = get_stabilized_reciprocal_mesh(
        #     [m * 2 - 1 for m in mesh],
        #     [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        #     is_time_reversal=False)[0]
        
        # print self._gp_map
        # print bz_gp_map
