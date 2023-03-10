#/bin/bash
#PBS -l select=2
#PBS -A atlas_aesp
#PBS -q debug-scaling
#PBS -l walltime=0:30:00
#PBS -l filesystems=eagle:home
#PBS -o /eagle/atlas_aesp/madgraph/jobs/
#PBS -e /eagle/atlas_aesp/madgraph/jobs/

NODES=`cat $PBS_NODEFILE | wc -l`
export GPUS_PER_NODE=4
export RANKS_PER_GPU=1
RANKS_PER_NODE=$(( GPUS_PER_NODE * RANKS_PER_GPU ))
RANKS=$((NODES * GPUS_PER_NODE * RANKS_PER_GPU))
echo [$SECONDS] NODES=$NODES GPUS_PER_NODE=$GPUS_PER_NODE RANKS_PER_GPU=$RANKS_PER_GPU  RANKS=$RANKS

export PROJ_PATH=/eagle/atlas_aesp/madgraph
export MEPYTHON=/eagle/atlas_aesp/madgraph/balsam_env/bin/python
export MG_PROC_DIR=/eagle/atlas_aesp/madgraph/madgraph4gpu-sycl_vector/epochX/sycl/gg_ttgg.mad
export SYCL_SETUP=setup_sycl_polaris.sh

export JOBDIR=$PROJ_PATH/jobs/$PBS_JOBID
mkdir -p $JOBDIR
cd $JOBDIR
echo [$SECONDS] starting mpiexec from path: $PWD
mpiexec -n $RANKS -ppn $RANKS_PER_NODE $PROJ_PATH/madgraph_scaling/run_everything.sh 1> $JOBDIR/run_stdout.txt 2> $JOBDIR/run_stderr.txt

echo [$SECONDS] Completed Everything
