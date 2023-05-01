import mpi4py.MPI as mpi
import argparse

parser = argparse.ArgumentParser(description='')
parser.add_argument('-n','--n-gpus',help='number of gpus per node',required=True,type=int)
parser.add_argument('-r','--n-ranks',help='number of ranks per tile',required=True,type=int)
parser.add_argument('-t','--n-tiles',help='number of tiles per gpu',required=True,type=int)
parser.add_argument('-m','--machine',help='name of the machine',required=True)
args = parser.parse_args()

comm=mpi.COMM_WORLD
rank = comm.Get_rank()
nranks = comm.Get_size()

local_comm=comm.Split_type(mpi.COMM_TYPE_SHARED,0)
lrank = local_comm.Get_rank()
lnranks = local_comm.Get_size()

gpus_per_node = args.n_gpus
tiles_per_gpu = args.n_tiles
ranks_per_tile = args.n_ranks
machine = str(args.machine).lower()


if 'sunspot' in machine:
   # gpu_num should be 0 to (n_gpus - 1)
   gpu_num = int(lrank / (tiles_per_gpu * ranks_per_tile))
   # tile_num (0 or 1)
   tile_num = int((lrank - (gpu_num * tiles_per_gpu * ranks_per_tile) ) / ranks_per_tile)

   if tiles_per_gpu*ranks_per_tile == 1:
      ze_affinity_mask = '%d' % gpu_num
   else:
      ze_affinity_mask = '%d.%d' % (gpu_num,tile_num)
elif 'polaris' in machine:
   gpu_num = int(lrank / (tiles_per_gpu * ranks_per_tile))
   ze_affinity_mask= '%d' % gpu_num

print(rank,nranks,'%02d' % lrank,lnranks,ze_affinity_mask)
