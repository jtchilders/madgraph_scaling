#/bin/bash
#PBS -l select=2
#PBS -A atlas_aesp_CNDA
#PBS -q workq
#PBS -l walltime=0:30:00
#PBS -o /lus/gila/projects/atlas_aesp_CNDA/madgraph_scaling/jobs/
#PBS -e /lus/gila/projects/atlas_aesp_CNDA/madgraph_scaling/jobs/

NODES=`cat $PBS_NODEFILE | wc -l`
export GPUS_PER_NODE=6
export TILES_PER_GPU=1
export RANKS_PER_TILE=1
RANKS_PER_NODE=$(( GPUS_PER_NODE * TILES_PER_GPU * RANKS_PER_TILE ))
RANKS=$((NODES * RANKS_PER_NODE ))
echo [$SECONDS] NODES=$NODES GPUS_PER_NODE=$GPUS_PER_NODE TILES_PER_GPU=$TILES_PER_GPU RANKS_PER_TILE=$RANKS_PER_TILE  RANKS=$RANKS

export FI_CXI_DEFAULT_CQ_SIZE=131072
export FI_CXI_CQ_FILL_PERCENT=20

export PROJ_PATH=/lus/gila/projects/atlas_aesp_CNDA/madgraph_scaling
export MEPYTHON=/lus/gila/projects/atlas_aesp_CNDA/conda/2023-02-22/bin/python
export MG_PROC_DIR=$PROJ_PATH/madgraph4gpu-sycl_vector/epochX/sycl/gg_ttgg.mad
export SYCL_SETUP=setup_sycl_sunspot.sh
export MACHINE=sunspot

export JOBDIR=$PROJ_PATH/jobs/$PBS_JOBID
mkdir -p $JOBDIR
cd $JOBDIR
echo [$SECONDS] starting mpiexec from path: $PWD
mpiexec -n $RANKS -ppn $RANKS_PER_NODE $PROJ_PATH/madgraph_scaling/run_everything.sh 1> $JOBDIR/run_stdout.txt 2> $JOBDIR/run_stderr.txt

echo [$SECONDS] Completed Everything
