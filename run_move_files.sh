#!/bin/bash

BASE_DIR=$1
DEST_DIR=$2
#echo RANKS=$RANKS
#echo BASE_DIR=$BASE_DIR

module load conda/2022-09-08 > /dev/null 2>&1
conda activate > /dev/null 2>&1

python /eagle/atlas_aesp/move_files.py -d $DEST_DIR \
   -f $BASE_DIR/SubProcesses/P1_gg_ttxgg/dname.mg \
   -f $BASE_DIR/SubProcesses/P1_gg_ttxgg/results.dat \
   -f $BASE_DIR/SubProcesses/P1_gg_ttxgg/iproc.dat \
   -f $BASE_DIR/Cards/param_card.dat \
   -f $BASE_DIR/lib/Pdfdata/NNPDF23_lo_as_0130_qed_mem0.grid

