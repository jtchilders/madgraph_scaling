import mpi4py.MPI as mpi
import argparse

parser = argparse.ArgumentParser(description='')
parser.add_argument('-n','--n-gpus',help='number of gpus per node',required=True,type=int)
parser.add_argument('-r','--n-ranks',help='number of ranks per gpu',required=True,type=int)
args = parser.parse_args()

comm=mpi.COMM_WORLD
rank = comm.Get_rank()
nranks = comm.Get_size()

local_comm=comm.Split_type(mpi.COMM_TYPE_SHARED,0)
lrank = local_comm.Get_rank()
lnranks = local_comm.Get_size()


gpu_half = int(lrank / args.n_gpus)
gpu_num = lrank % args.n_gpus

if args.n_ranks == 1:
   ze_affinity_mask = '%d' % gpu_num
elif args.n_ranks == 2:
   ze_affinity_mask = '%d.%d' % (gpu_num,gpu_half)


print(rank,nranks,'%02d' % lrank,lnranks,ze_affinity_mask)
