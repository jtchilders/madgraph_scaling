#/bin/bash
#PBS -l select=2
#PBS -A atlas_aesp_CNDA
#PBS -q workq
#PBS -l walltime=0:30:00
#PBS -o /lus/gila/projects/atlas_aesp_CNDA/madgraph_scaling/jobs/
#PBS -e /lus/gila/projects/atlas_aesp_CNDA/madgraph_scaling/jobs/

NODES=`cat $PBS_NODEFILE | wc -l`
export GPUS_PER_NODE=6
export RANKS_PER_GPU=1
RANKS_PER_NODE=$(( GPUS_PER_NODE * RANKS_PER_GPU ))
RANKS=$((NODES * GPUS_PER_NODE * RANKS_PER_GPU))
echo [$SECONDS] NODES=$NODES GPUS_PER_NODE=$GPUS_PER_NODE RANKS_PER_GPU=$RANKS_PER_GPU  RANKS=$RANKS

export PROJ_PATH=/lus/gila/projects/atlas_aesp_CNDA/madgraph_scaling

export JOBDIR=$PROJ_PATH/jobs/$PBS_JOBID
mkdir -p $JOBDIR
cd $JOBDIR
echo [$SECONDS] starting mpiexec from path: $PWD
mpiexec -n $RANKS -ppn $RANKS_PER_NODE $PROJ_PATH/scripts/run_everything.sh 1> $JOBDIR/run_stdout.txt 2> $JOBDIR/run_stderr.txt

echo [$SECONDS] Completed Everything
