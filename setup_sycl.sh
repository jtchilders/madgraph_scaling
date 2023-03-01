module load oneapi/eng-compiler/2022.12.30.003
export INTEL_AOT_STRING="12.60.7"
export CXX=icpx
export CC=icx
export FC=gfortran
export F77="gfortran -std=legacy"
export NTPBMAX=1024
export USEBUILDDIR=1
export SYCLFLAGS="-fsycl -fsycl-targets=spir64_gen -Xsycl-target-backend \"-device ${INTEL_AOT_STRING}\" -Xsycl-target-backend \"-options '-ze-opt-large-register-file'\""
export HRDCOD=0


