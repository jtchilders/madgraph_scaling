#!/bin/bash
if [ -z "${SCRIPTSDIR+xxx}" ]; then echo "SCRIPTSDIR is not set at all"; fi
RANK=$1
LOCAL_RANK=$2
EXECUTABLE=$3
RAND_SEED=$4
NB_PAGE_LOOP=16384
NUM_EVENTS=$(( 10 * $NB_PAGE_LOOP ))
MIN_ITERS=5
MAX_ITERS=10
# NUM_EVENTS=10000000
# MIN_ITERS=1
# MAX_ITERS=1

# echo [$SECONDS][$RANK][$LOCAL_RANK] setup script
source $SCRIPTSDIR/$SYCL_SETUP > ./setup.log 2>&1
# added this otherwise all ranks use 1 GPU
#export CUDA_VISIBLE_DEVICES=$(( $LOCAL_RANK ))
cat > input.txt << EOF
1 ! Fortran bridge mode (CppOnly=1, FortranOnly=0, BothQuiet=-1, BothDebug=-2)
$NB_PAGE_LOOP ! Number of events in a single C++ or SYCL iteration (nb_page_loop)
$NUM_EVENTS $MAX_ITERS $MIN_ITERS ! Number of events and max and min iterations
0.01 ! Accuracy (ignored because max iterations = min iterations)
0 ! Grid Adjustment 0=none, 2=adjust (NB if = 0, ftn26 will still be used if present)
1 ! Suppress Amplitude 1=yes (i.e. use MadEvent single-diagram enhancement)
0 ! Helicity Sum/event 0=exact
1 ! Channel number (1-N) for single-diagram enhancement multi-channel (NB used even if suppress amplitude is 0!)
EOF

cat > randinit << EOF
r=$RAND_SEED
EOF

export MG5AMC_CARD_PATH=.

#echo [$SECONDS][$RANK][$LOCAL_RANK] start madevent $EXECUTABLE  $PWD
{ time -p $EXECUTABLE < input.txt; } > madevent_$RANK.stdout 2>&1
#$EXECUTABLE < input.txt
#echo [$SECONDS][$RANK][$LOCAL_RANK] done
