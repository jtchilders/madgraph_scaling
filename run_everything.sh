#!/bin/bash
if [ -z "${PROJ_PATH+xxx}" ]; then echo "PROJ_PATH is not set at all"; fi
if [ -z "${JOBDIR+xxx}" ]; then echo "JOBDIR is not set at all"; fi


RAND_SEED=12345
export SCRIPTSDIR=$PROJ_PATH/madgraph_scaling
RAMDISK=/dev/shm

RANK_STR=$($MEPYTHON $SCRIPTSDIR/get_mpi_info.py -n $GPUS_PER_NODE -r $RANKS_PER_GPU)
#echo [$SECONDS] RANK_STR = $RANK_STR
RANK_STR_ARRAY=($RANK_STR)

RANK=${RANK_STR_ARRAY[0]}
NRANKS=${RANK_STR_ARRAY[1]}
LOCAL_RANK=${RANK_STR_ARRAY[2]}
LOCAL_NRANKS=${RANK_STR_ARRAY[3]}
export ZE_AFFINITY_MASK=${RANK_STR_ARRAY[4]}
#echo [$SECONDS][$RANK] ZE_AFFINITY_MASK=$ZE_AFFINITY_MASK

IS_RANK0=`expr $RANK == 0`

RANK_RAND_SEED=`expr $RANK + $RAND_SEED`
HOSTNAME=`hostname`

#echo [$SECONDS][$RANK] RANK=$RANK  NRANKS=$NRANKS  LOCAL_RANK=$LOCAL_RANK   LOCAL_NRANKS=$LOCAL_NRANKS   HOSTNAME=$HOSTNAME  RANK_RAND_SEED = $RANK_RAND_SEED

if [[ "$IS_RANK0" == 1 ]]; then
   echo [$SECONDS][$RANK] run move_files
fi

mkdir -p $RAMDISK/$LOCAL_RANK

# distribute files to ranks
$MEPYTHON $SCRIPTSDIR/move_files.py -d $RAMDISK \
   -f $MG_PROC_DIR/SubProcesses/P1_gg_ttxgg/dname.mg \
   -f $MG_PROC_DIR/SubProcesses/P1_gg_ttxgg/iproc.dat \
   -f $MG_PROC_DIR/Cards/param_card.dat \
   -f $MG_PROC_DIR/lib/Pdfdata/NNPDF23_lo_as_0130_qed_mem0.grid \
   -j $JOBDIR/combined_stats.json

cd $RAMDISK/$LOCAL_RANK

$MEPYTHON  -c "import mpi4py.MPI as mpi;comm=mpi.COMM_WORLD;comm.barrier()"
if [[ "$IS_RANK0" == 1 ]]; then
   echo [$SECONDS][$RANK] run madevent
fi
# run madevent
$SCRIPTSDIR/run_madevent.sh $RANK $LOCAL_RANK $MG_PROC_DIR/SubProcesses/P1_gg_ttxgg/build.d_inl0_hrd0/madevent_sycl $RANK_RAND_SEED

if [ ! -d $JOBDIR ]; then
   mkdir -p $JOBDIR
fi

$MEPYTHON  -c "import mpi4py.MPI as mpi;comm=mpi.COMM_WORLD;comm.barrier()"
# parse stdout and dump json data
if [[ "$IS_RANK0" == 1 ]]; then
   echo [$SECONDS][$RANK] run parse_madevent_output
fi
$MEPYTHON $SCRIPTSDIR/parse_madevent_output.py -i madevent_$RANK.stdout -o $JOBDIR/combined_stats.json


$MEPYTHON  -c "import mpi4py.MPI as mpi;comm=mpi.COMM_WORLD;comm.barrier()"
# combine LHE files
if [[ "$IS_RANK0" == 1 ]]; then
   echo [$SECONDS][$RANK] run write_lhe
fi
$MEPYTHON $SCRIPTSDIR/write_lhe.py -i events.lhe -o $JOBDIR/combined_events.lhe -j $JOBDIR/combined_stats.json

$MEPYTHON  -c "import mpi4py.MPI as mpi;comm=mpi.COMM_WORLD;comm.barrier()"
# combine LHE files
if [[ "$IS_RANK0" == 1 ]]; then
   echo [$SECONDS][$RANK] done
fi
# only keep this during debugging
if [[ "$IS_RANK0" == 1 ]]; then
   mkdir $JOBDIR/ramdisk_rank0/
   cp -r $RAMDISK/?? $JOBDIR/ramdisk_rank0/
fi

