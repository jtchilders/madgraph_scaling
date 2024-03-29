#/bin/bash
#PBS -l select=2
#PBS -A atlas_aesp
#PBS -q debug-scaling
#PBS -l walltime=0:15:00
#PBS -l filesystems=eagle:home
#PBS -o /eagle/atlas_aesp/madgraph/jobs/
#PBS -e /eagle/atlas_aesp/madgraph/jobs/

NODES=`cat $PBS_NODEFILE | wc -l`
export GPUS_PER_NODE=4
export TILES_PER_GPU=1
export RANKS_PER_TILE=2
RANKS_PER_NODE=$(( GPUS_PER_NODE * TILES_PER_GPU * RANKS_PER_TILE ))
RANKS=$((NODES * RANKS_PER_NODE))
echo [$SECONDS] NODES=$NODES GPUS_PER_NODE=$GPUS_PER_NODE TILES_PER_GPU=$TILES_PER_GPU RANKS_PER_TILE=$RANKS_PER_TILE  RANKS=$RANKS


export PROJ_PATH=/eagle/atlas_aesp/madgraph
export MEPYTHON=/soft/datascience/conda/2022-09-08/mconda3/bin/python
export MG_PROC_DIR=/eagle/atlas_aesp/madgraph/madgraph4gpu-sycl_vector/epochX/sycl/gg_ttgg.mad
export SYCL_SETUP=setup_sycl_polaris.sh
export MACHINE=polaris

export JOBDIR=$PROJ_PATH/jobs/$PBS_JOBID
mkdir -p $JOBDIR
cd $JOBDIR

echo [$SECONDS] starting mpiexec from path: $PWD
mpiexec -n $RANKS -ppn $RANKS_PER_NODE \
   $PROJ_PATH/madgraph_scaling/run_everything.sh \
      $GPUS_PER_NODE $TILES_PER_GPU $RANKS_PER_TILE \
      $PROJ_PATH $MEPYTHON $MG_PROC_DIR $SYCL_SETUP $MACHINE \
      1> $JOBDIR/run_stdout.txt 2> $JOBDIR/run_stderr.txt

echo [$SECONDS] Completed Everything
