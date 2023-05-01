echo [$SECONDS] running SYCL setup for polaris
module load oneapi

export CUDA_PATH=$CUDA_HOME
export VECLVL=1
export CXTYPE=thrust
export CXX=clang++
export CC=clang
export FC=gfortran
export F77="gfortran -std=legacy"
export NTPBMAX=1024
export USEBUILDDIR=1
export HRDCOD=0
export CUDA_LIB_PATH=$CUDA_PATH/lib64/stubs
#export ATLASESP_DIR=/gpfs/jlse-fs0/projects/AtlasESP
export CUDA_VERSION_STR="cuda-11.8.0"
export SYCLFLAGS="-fsycl -fsycl-targets=nvptx64-nvidia-cuda -Xcuda-ptxas --maxrregcount=255 -Xcuda-ptxas --verbose -Xsycl-target-backend '--cuda-gpu-arch=sm_80' --cuda-path=$CUDA_PATH"

echo $LD_LIBRARY_PATH
ldd /eagle/atlas_aesp/madgraph/madgraph4gpu-sycl_vector/epochX/sycl/gg_ttgg.mad/SubProcesses/P1_gg_ttxgg/build.d_inl0_hrd0/madevent_sycl
