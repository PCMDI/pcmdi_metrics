#!/usr/bin/env bash

## SYSTEM SPECIFIC OPTIONS, EDIT THESE TO MATCH YOUR SYSTEM

## Directory where to install UVCDAT and the METRICS Packages
install_prefix="PCMDI_METRICS"

## Temporary build directory
build_directory="${install_prefix}/tmp"

## Speed up your build by increasing the following to match your number of processors
num_cpus=4

#### BUILD OPTIONS #####
## Do we want to build with graphics capabilities
build_graphics=false

## Do we want to build with CMOR
build_cmor=false

## Do we build UV-CDAT with parallel capabilities (MPI)
build_parallel=false

## Do we keep or remove uvcdat_build diretory before building UV-CDAT
## Useful for case where multiple make necessary
## valid values: true false
keep_uvcdat_build_dir=false

### DO NOT EDIT AFTER THIS POINT !!!!! ###

# Prevent installer from hanging due to cdms2 logging
export UVCDAT_ANONYMOUS_LOG=False

setup_cmake() {

    ## Source funcs needed by installer
    . ${metrics_build_directory}/installer_funcs.bash
    echo -n "Checking for CMake >=  ${cmake_min_version} "
    check_version_with cmake "cmake --version | head -n1 | awk '{print \$3}' | awk -F . '{print \$1\".\"\$2\".\"\$3}'" ${cmake_min_version} ${cmake_max_version}
    [ $? == 0 ] && (( ! force_install )) && echo " [OK]" && return 0

    echo
    echo "*******************************"
    echo "Setting up CMake ${cmake_version}"
    echo "*******************************"
    echo

    local default="Y"
    ((force_install)) && default="N"
    local dosetup
    if [ -x ${cmake_install_dir}/bin/cmake ]; then
        echo "Detected an existing CMAKE installation..."
        read -e -p "Do you want to continue with CMAKE installation and setup? $([ "$default" = "N" ] && echo "[y/N]" || echo "[Y/n]") " dosetup
        [ -z ${dosetup} ] && dosetup=${default}
        if [ "${dosetup}" != "Y" ] && [ "${dosetup}" != "y" ]; then
            echo "Skipping CMAKE installation and setup - will assume CMAKE is setup properly"
            return 0
        fi
        echo
    fi

    #make top level directory for cmake repo clone
    mkdir -p ${cmake_build_directory%/*}
    chmod a+rw ${cmake_build_directory%/*}

    if [ ! -d "${cmake_build_directory}" ]; then
      echo "Cloning CMake repository ${cmake_repo}..."
      git clone ${cmake_repo} ${cmake_build_directory}
      if [ ! -d ${cmake_build_directory}/.git ]; then
        echo "Apparently was not able to fetch from cmake repo using git protocol (port 9418)... trying https protocol..."
        git clone ${cmake_repo_https} ${cmake_build_directory}
        if [ ! -d ${cmake_build_directory}/.git ]; then
          echo "Apparently was not able to fetch from cmake repo using https protocol (port 2)... trying http protocol..."
          git clone ${cmake_repo_http} ${cmake_build_directory}
          if [ ! -d ${cmake_build_directory}/.git ]; then
            echo "Could not fetch from cmake repo (with git/https/http protocol). Please check you are online and your firewall settings"
            exit 1
          fi
        fi
      fi
    fi

    (
        unset LD_LIBRARY_PATH
	unset CFLAGS
	unset LDFLAGS

        ((DEBUG)) && printf "\n-----\n cd ${cmake_build_directory} \n-----\n"
        cd ${cmake_build_directory} >& /dev/null

        ((DEBUG)) && printf "\n-----\n git checkout v${cmake_version} \n-----\n"
        git checkout v${cmake_version}
        [ $? != 0 ] && echo "ERROR: Could not checkout CMake @ v${cmake_version}" && checked_done 2

        ((DEBUG)) && printf "\n-----\n ./configure --parallel=${num_cpus} --prefix=${cmake_install_dir} \n-----\n"
        ./configure --parallel=${num_cpus} --prefix=${cmake_install_dir}
        [ $? != 0 ] && echo "ERROR: Could not configure CMake successfully" && checked_done 3

        ((DEBUG)) && printf "\n-----\n make -j ${num_cpus} \n-----\n"
        make -j ${num_cpus}
        [ $? != 0 ] && echo "ERROR: Could not make CMake successfully" && checked_done 4

        ((DEBUG)) && printf "\n-----\n make install \n-----\n"
        make install
        [ $? != 0 ] && echo "ERROR: Could not install CMake successfully" && checked_done 5
    )
    echo "returning from build subshell with code: [$?]"
    (( $? > 1 )) && echo "ERROR: Could not setup CMake successfully, aborting... " && checked_done 1

    cmake_version=$(${cmake_install_dir}/bin/cmake --version | awk '{print $3}' | sed -e 's/\([^-]*\)-.*/\1/')
    printf "\ninstalled CMake version = ${cmake_version}\n\n"

    checked_done 0
}

#####
# CDAT = Python+CDMS
#####
setup_cdat() {
    FC=gfortran
    F77=gfortran
    F90=gfortran
    CC=gcc
    CXX=g++
    echo -n "Checking for *UV* CDAT (Python+CDMS) ${cdat_version} "

    #-----------CDAT -> UVCDAT Migration------------------
    #rewrite cdat_home to new uvcdat location
    #-----------------------------------------------------
    cdat_home=$(perl -pe 's/(?<!uv)cdat/uvcdat/' <<<${cdat_home})
    CDAT_HOME=${cdat_home}
    #-----------------------------------------------------
    ${cdat_home}/bin/python -c "import cdat_info; print cdat_info.Version" 
    local ret=$?
    ((ret == 0)) && (( ! force_install )) && echo " [OK]" && return 0
    echo "No python in your install directory, trying your PATH"
    python -c "import cdat_info; print cdat_info.Version" 
    if [ $? == 0 ]; then
       echo "you have a valid cdat in your path"
       cdat_home=`python -c "import sys; print sys.prefix"`
       echo "It is located at:" ${cdat_home}
       cat > ${install_prefix}/bin/setup_runtime.sh  <<  EOF  
       . ${cdat_home}/bin/setup_runtime.sh
       export PYTHONPATH=${install_prefix}/lib/python2.7/site-packages:\${PYTHONPATH}
       export PATH=${PATH}:${install_prefix}/bin
EOF
       return 0
    fi


    ## Source funcs needed by installer
    . ${metrics_build_directory}/installer_funcs.bash
    echo
    echo "*******************************"
    echo "Setting up CDAT - (Python + CDMS)... ${cdat_version}"
    echo "*******************************"
    echo

    local dosetup="N"
    if [ -x ${cdat_home}/bin/python ]; then
        echo "Detected an existing CDAT installation..."
        read -e -p "Do you want to continue with CDAT installation and setup? [Y/N] " dosetup
        if [ "${dosetup}" != "Y" ] && [ "${dosetup}" != "y" ]; then
            echo "Skipping CDAT installation and setup - will assume CDAT is setup properly"
            return 0
        fi
        echo
    fi

    mkdir -p ${uvcdat_build_directory}
    [ $? != 0 ] && checked_done 1
    pushd ${uvcdat_build_directory} >& /dev/null
    local cdat_git_protocol="git://"
    if [ ! -d ${uvcdat_build_directory}/uvcdat ]; then
      echo "Fetching the cdat project from GIT Repo..."
      ((DEBUG)) && echo "${cdat_repo}"
      git clone ${cdat_repo} uvcdat
      if [ ! -d ${uvcdat_build_directory}/uvcdat/.git ]; then
        cdat_git_protocol="https://"
        echo "Apparently was not able to fetch from GIT repo using git protocol. (port 9418).. trying https protocol..."
        ((DEBUG)) && echo "${cdat_repo_https}"
        git clone ${cdat_repo_https} uvcdat
        if [ ! -d ${uvcdat_build_directory}/uvcdat/.git ]; then
          cdat_git_protocol="http://"
          echo "Was still not able to fetch from GIT repo this time using https protocol... (port 22) trying http protocol..."
          ((DEBUG)) && echo "${cdat_repo_http}"
          git clone ${cdat_repo_http} uvcdat
          [ ! -d ${uvcdat_build_directory}/uvcdat/.git ] && echo "Could not fetch from cdat's repo (with git, https nor http protocol)i please check your internet connection and firewall settings" && checked_done 1
        fi
      fi
    fi
    cd uvcdat >& /dev/null
    git checkout ${cdat_version}
    [ $? != 0 ] && echo " WARNING: Problem with checking out cdat revision [${cdat_version}] from repository :-("
    #NOTE:
    #cdms configuration with --enable-esg flag looks for pg_config in
    #$postgress_install_dir/bin.  This location is created and added
    #to the executable PATH by the 'setup_postgress' function.
    #if [ -n "${certificate}" ]; then
    #    pip_string="-DPIP_CERTIFICATE="${certificate}
    #    echo "Using user defined certificate path: ${certificate}"
    #fi

    local uvcdat_build_directory_build=${uvcdat_build_directory}/uvcdat_build
    (
        unset LD_LIBRARY_PATH
        unset PYTHONPATH
        unset CFLAGS
        unset LDFLAGS
        if [  ${keep_uvcdat_build_dir} = false ]; then
            echo "removing UVCDAT build directory"
            [ -d ${uvcdat_build_directory_build} ] && rm -rf ${uvcdat_build_directory_build}
        else 
          echo "You said you wanted to keep uvcdat_build_dir"
        fi
        mkdir -p ${uvcdat_build_directory_build} >& /dev/null
        pushd ${uvcdat_build_directory_build} >& /dev/null
        #(zlib patch value has to be 3,5,7 - default is 3)
        local zlib_value=$(pkg-config --modversion zlib | sed -n -e 's/\(.\)*/\1/p' | sed -n -e '/\(3|5|7\)/p') ; [[ ! ${zlib_value} ]] && zlib_value=3

        if [ ${build_graphics} = false ]; then
          echo "LEAN MODE will not build graphics"
          uvcdat_mode="-DCDAT_BUILD_MODE=LEAN -DCDAT_BUILD_ESMF_ESMP=ON"
        else
          echo "Turning on graphics this will take sensibly longer to build"
          uvcdat_mode="-DCDAT_BUILD_MODE=DEFAULT -DCDAT_BUILD_GUI=OFF -DCDAT_BUILD_ESMF_ESMP=ON"
        fi

        if [ ${build_cmor} = false ]; then
          uvcdat_cmor=""
        else
          echo "Turning on CMOR"
          uvcdat_cmor="-DCDAT_BUILD_CMOR=ON"
        fi

        if [ ${build_parallel} = false ]; then
          uvcdat_parallel=""
        else
          echo "Turning on build for parallel features, wil ltakes sensibly longer"
          uvcdat_parallel="-DCDAT_BUILD_PARALLEL=ON"
        fi

        cmake_cmd="cmake ${uvcdat_build_directory}/uvcdat ${uvcdat_mode} ${uvcdat_cmor} ${uvcdat_parallel} -DCMAKE_INSTALL_PREFIX=${cdat_home} -DZLIB_PATCH_SRC=${zlib_value} -DGIT_PROTOCOL=${cdat_git_protocol} "

        echo "CMAKE ARGS: "${cmake_cmd}
        echo "PATH:"${PATH}
        echo "PWD:"`pwd`
        ${cmake_cmd}
        [ $? != 0 ] && echo " ERROR: Could not configure (cmake) cdat code (1)" && popd && checked_done 1
        ${cmake_cmd}
        [ $? != 0 ] && echo " ERROR: Could not configure (cmake) cdat code (2)" && popd && checked_done 1

        echo "CMAKE ARGS"${cmake_args}
        make -j ${num_cpus}
        [ $? != 0 ] && echo " ERROR: Could not compile (make) cdat code" && popd && checked_done 1

        echo "CMAKE ARGS"${cmake_args}
        echo "UVCDAT BDIR"${uvcdat_build_directory}

        popd >& /dev/null
    )
    [ $? != 0 ] && echo " ERROR: Could not compile (make) cdat code" && popd && checked_done 1

    ${cdat_home}/bin/python -c "import cdms2" 2>/dev/null
    [ $? != 0 ] && echo " ERROR: Could not load CDMS (cdms2) module" && popd && checked_done 1

    popd >& /dev/null
    echo

    checked_done 0
}

setup_cdat_xtra() {
    echo "Installing Extra Package ${1}"${uvcdat_build_directory}/uvcdat/Packages/$1
    cd ${uvcdat_build_directory}/uvcdat/Packages/$1 >& /dev/null
    env BUILD_DIR="." CFLAGS="-I${install_prefix}/Externals/include" ${install_prefix}/bin/python setup.py install
    [ $? != 0 ] && echo " Error could not install CDAT extra python package ${1} using ${install_prefix}/bin/python" 
}

setup_metrics() {
    cd ${metrics_build_directory} >& /dev/null
    ${cdat_home}/bin/python setup.py install --prefix=${install_prefix}
    [ $? != 0 ] && echo " Error could not install metrics python package using ${cdat_home}/bin/python" 
}

_full_path() {
    # Figure out the full path and resolved symlinks
    # Saves current dir
    local DIR=`pwd`
    if [ ! -d $1 ]; then
        if [ ${1:0:1} == "/" ]; then
            local PTH=$1
        else
            local PTH=`pwd -P`/$1
        fi
    else
        pushd $1 >& /dev/null
        local PTH=`pwd -P`
    fi
    mkdir -p ${PTH}
    echo ${PTH}
    if [ $? != 0 ]; then
        exit 1
    fi
    pushd ${DIR} >& /dev/null
    exit 0
}

_readlinkf() {
    # This is a portable implementation of GNU's "readlink -f" in
    # bash/zsh, following symlinks recursively until they end in a
    # file, and will print the full dereferenced path of the specified
    # file even if the file isn't a symlink.
    #
    # Loop detection exists, but only as an abort after passing a
    # maximum length.

    local start_dir=$(pwd)
    local file=${1}
    local current_dir
    current_dir=$(pwd -P)
    cd $(dirname ${file}) >& /dev/null
    if [ $? != 0 ]; then
       echo ${current_dir}/${file}
       exit 0
    fi

    file=$(basename ${file})

    # Iterate down symlinks.  If we exceed a maximum number symlinks, assume that
    # we're looped and die horribly.
    local maxlinks=20
    local count=0
    while [ -L "${file}" ] ; do
        file=$(readlink ${file})
        cd $(dirname ${file}) >& /dev/null
        file=$(basename ${file})
        ((count++))
        if (( count > maxlinks )) ; then
            current_dir=$(pwd -P)
            echo "CRITICAL FAILURE[4]: symlink loop detected on ${current_dir}/${file}"
            cd ${start_dir} >& /dev/null
            exit ${count}
        fi
    done
    echo "${current_dir}/${file}"
    cd ${start_dir} >& /dev/null
}

main() {
    ## Generic Build Parameters
    cmake_repo=git://cmake.org/cmake.git
    cmake_repo_http=http://cmake.org/cmake.git
    cmake_repo_https=https://cmake.org/cmake.git
    cmake_min_version=2.8.11
    cmake_max_version=2.9
    cmake_version=2.8.12
    force_install=0
    DEBUG=1
    cdat_repo=git://github.com/UV-CDAT/uvcdat.git
    cdat_repo_http=http://github.com/UV-CDAT/uvcdat.git
    cdat_repo_https=https://github.com/UV-CDAT/uvcdat.git
    cdat_version="master"
    metrics_repo=git://github.com/PCMDI/pcmdi_metrics.git
    metrics_repo_http=http://github.com/PCMDI/pcmdi_metrics.git
    metrics_repo_https=https://github.com/PCMDI/pcmdi_metrics.git
    metrics_checkout="master"
    install_prefix=$(_full_path ${install_prefix})
    if [ $? != 0 ]; then
        echo "Could not create directory ${install_prefix}"
        exit 1
    fi
    build_directory=$(_full_path ${build_directory})
    if [ $? != 0 ]; then
        echo "Could not create directory ${build_directory}"
        exit 1
    fi
    metrics_build_directory=${build_directory}/metrics
    cmake_build_directory=${build_directory}/cmake
    uvcdat_build_directory=${build_directory}/uvcdat
    cmake_install_dir=${install_prefix}/Externals
    cdat_home=${install_prefix}
    echo "Installing into: "${install_prefix}
    echo "Temporary build directory: "${build_directory}
    ## clone pcmdi_metrics repo
    git clone ${metrics_repo} ${metrics_build_directory}
    if [ ! -e ${metrics_build_directory}/.git/config ]; then
      echo " WARN: Could not clone metrics repo via git protocol (port 9418)! Trying https protocol"
      git clone ${metrics_repo_https} ${metrics_build_directory}
      if [ ! -e ${metrics_build_directory}/.git/config ]; then
        echo " WARN: Could not clone metrics repo via https (port 22)! Trying http protocol (port 80)"
        git clone ${metrics_repo_http} ${metrics_build_directory}
        if [ ! -e ${metrics_build_directory}/.git/config ]; then
            echo " ERROR: Could not clone metrics repo via git/https/http! Check you are connected to the internet or your firewall settings"
            exit 1
        fi
      fi
    fi

    cd ${metrics_build_directory} >& /dev/null
    git checkout ${metrics_checkout}

    ## Source funcs needed by installer
    . ${metrics_build_directory}/installer_funcs.bash

    mkdir -p ${install_prefix}
    mkdir -p ${install_prefix}/Externals
    mkdir -p ${install_prefix}/Externals/bin
    mkdir -p ${install_prefix}/Externals/lib
    mkdir -p ${install_prefix}/Externals/include
    mkdir -p ${install_prefix}/Externals/share
    
    PATH=${install_prefix}/Externals/bin:${PATH}
    setup_cmake
    setup_cdat
    echo "After setup_cdat ${cdat_home}"
    setup_metrics
    pushd ${uvcdat_build_directory}/uvcdat >& /dev/null
    git apply ${metrics_build_directory}/src/patch_uvcdat.patch
    setup_cdat_xtra genutil
    setup_cdat_xtra xmgrace
    setup_cdat_xtra cdutil
    rm -rf ${install_prefix}/sample_data

    echo
    echo
    echo "*******************************"
    echo "UVCDAT  - ${cdat_version} - Install Success"
    echo "Metrics - ${metrics_checkout} - Install Success"
    echo "*******************************"
    echo "Please test as follows:"
    echo "source ${cdat_home}/bin/setup_runtime.sh"
    echo "python ${build_directory}/metrics/test/test_suite.py"
    echo "*******************************"
    echo "Create your customized input_parameters.py (inspire yourself from examples in ${install_prefix}/doc/parameter_files/pcmdi_input_parameters_sample.py"
    echo "Once you have a parameter file run:"
    echo "source ${install_prefix}/bin/setup_runtime.sh"
    echo "pcmdi_metrics_driver.py -p /path/to/your/edited/parameter_file.py"
    echo "*******************************"
    echo "Once everything is ok, you can safely remove the temporary directory: ${build_directory}"
    echo "*******************************"
    echo "For further information or suggestions please contact the PCMDI Metrics Team @ pcmdi-metrics@llnl.gov"
    echo "*******************************"
    echo

}
 main
