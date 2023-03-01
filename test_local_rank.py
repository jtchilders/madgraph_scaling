import mpi4py.MPI as MPI


comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nranks = comm.Get_size()

local_comm = comm.Split_type(MPI.COMM_TYPE_SHARED,0)

local_rank = local_comm.Get_rank()
local_nranks = local_comm.Get_size()

color = MPI.UNDEFINED
if local_rank == 0:
   color = 0
one_per_node_comm = comm.Split(color,rank)
one_rank = -1
if one_per_node_comm != MPI.COMM_NULL:
   one_rank = one_per_node_comm.Get_rank()
one_nranks = -1
if one_per_node_comm != MPI.COMM_NULL:
   one_nranks = one_per_node_comm.Get_size()


print('%d of %d   local: %d of %d  one: %d of %d' % (rank,nranks,local_rank,local_nranks,one_rank,one_nranks))

