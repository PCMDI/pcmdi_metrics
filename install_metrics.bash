#!/usr/bin/env bash

## SYSTEM SPECIFIC OPTIONS, EDIT THESE TO MATCH YOUR SYSTEM

## Directory where to install UVCDAT and the METRICS Packages
install_prefix="WGNE"

## Temporary build directory
build_directory="WGNE/tmp"

## Do we build UV-CDAT with parallel capabilities (MPI)
build_parallel="OFF"

## If you are behind a firewall or need a certificate to get out
## specify path to certificate below, leave blank otherwise
#certificate=${HOME}/ca.llnl.gov.pem.cer
certificate=

## Do we build graphics - Not currently needed, for future use
#build_graphics="OFF"

## Path to your "qmake" executable
## Qt is a pre-requisite if you turn graphics on
## You can download it from: http://qt-project.org/downloads
## if you leave the following blank we will attempt to use your system Qt
#qmake_executable=/usr/local/uvcdat/Qt/4.8.4/bin/qmake
#qmake_executable=/usr/bin/qmake

## Speed up your build by increasing the following to match your number of processors
num_cpus=16



### DO NOT EDIT AFTER THIS POINT !!!!! ###

# Prevent installer from hanging due to cdms2 logging
export UVCDAT_ANONYMOUS_LOG=False

setup_cmake() {

    ## Source funcs needed by installer
    . ${metrics_build_directory}/installer_funcs.bash
    echo -n "Checking for CMake >=  ${cmake_min_version} "
    check_version_with cmake "cmake --version | awk '{print \$3}' | sed -e 's/\([^-]*\)-.*/\1/'" ${cmake_min_version} ${cmake_max_version}
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
            echo "Apparently was not able to fetch from cmake repo using git protocol... trying http protocol..."
            git clone ${cmake_repo_http} ${cmake_build_directory}
            if [ ! -d ${cmake_build_directory}/.git ]; then
                echo "Could not fetch from cmake repo (with git nor http protocol)"
                exit 1
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
    echo -n "Checking for *UV* CDAT (Python+CDMS) ${cdat_version}"

    #-----------CDAT -> UVCDAT Migration------------------
    #rewrite cdat_home to new uvcdat location
    #-----------------------------------------------------
    cdat_home=$(perl -pe 's/(?<!uv)cdat/uvcdat/' <<<${cdat_home})
    CDAT_HOME=${cdat_home}
    #-----------------------------------------------------
    ${cdat_home}/bin/python -c "import cdat_info; print cdat_info.Version" 
    local ret=$?
    ((ret == 0)) && (( ! force_install )) && echo " [OK]" && return 0

    ## Source funcs needed by installer
    . ${metrics_build_directory}/installer_funcs.bash
    echo
    echo "*******************************"
    echo "Setting up CDAT - (Python + CDMS)... ${cdat_version}"
    echo "*******************************"
    echo

    local dosetup="N"
    if [ -x ${cdat_home}/bin/cdat ]; then
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
            cdat_git_protocol="http://"
            echo "Apparently was not able to fetch from GIT repo using git protocol... trying http protocol..."
            ((DEBUG)) && echo "${cdat_repo_http}"
            git clone ${cdat_repo_http} uvcdat
            [ ! -d ${uvcdat_build_directory}/uvcdat/.git ] && echo "Could not fetch from cdat's repo (with git nor http protocol)" && checked_done 1
        fi
    fi
    cd uvcdat >& /dev/null
    git checkout ${cdat_version}
    [ $? != 0 ] && echo " WARNING: Problem with checking out cdat revision [${cdat_version}] from repository :-("
    #NOTE:
    #cdms configuration with --enable-esg flag looks for pg_config in
    #$postgress_install_dir/bin.  This location is created and added
    #to the executable PATH by the 'setup_postgress' function.
    if [ -n "${certificate}" ]; then
        pip_string="-DPIP_CERTIFICATE="${certificate}
        echo "Using user defined certificate path: ${certificate}"
    fi

    local uvcdat_build_directory_build=${uvcdat_build_directory}/uvcdat_build
    (
        unset LD_LIBRARY_PATH
        unset PYTHONPATH
	unset CFLAGS
	unset LDFLAGS

        [ -d ${uvcdat_build_directory_build} ] && rm -rf ${uvcdat_build_directory_build}
        mkdir -p ${uvcdat_build_directory_build} >& /dev/null
        pushd ${uvcdat_build_directory_build} >& /dev/null
        #(zlib patch value has to be 3,5,7 - default is 3)
        local zlib_value=$(pkg-config --modversion zlib | sed -n -e 's/\(.\)*/\1/p' | sed -n -e '/\(3|5|7\)/p') ; [[ ! ${zlib_value} ]] && zlib_value=3

        # cmake_args="${pip_string} -DCDAT_BUILD_PARALLEL=${build_parallel} -DCMAKE_INSTALL_PREFIX=${cdat_home} -DZLIB_PATCH_SRC=${zlib_value} -DCDAT_BUILD_GUI=OFF -DGIT_PROTOCOL=${cdat_git_protocol} ${uvcdat_build_directory}/uvcdat -DCDAT_BUILD_GRAPHICS=${build_graphics} $([ "${build_graphics}" = "ON" ] && echo "-DQT_QMAKE_EXECUTABLE=${qmake_executable}")"
        cmake_cmd="cmake ${pip_string} -DCDAT_BUILD_UDUNITS2=ON -DCDAT_BUILD_PARALLEL=${build_parallel} -DCMAKE_INSTALL_PREFIX=${cdat_home} -DZLIB_PATCH_SRC=${zlib_value} -DCDAT_BUILD_ESGF=ON -DCDAT_BUILD_ESMF_ESMP=ON -DGIT_PROTOCOL=${cdat_git_protocol} ${uvcdat_build_directory}/uvcdat "

        echo "CMAKE ARGS: "${cmake_args}
        echo "PATH:"${PATH}
        echo "PWD:"`pwd`
        ${cmake_cmd}
        [ $? != 0 ] && echo " ERROR: Could not compile (make) cdat code (1)" && popd && checked_done 1
        ${cmake_cmd}
        [ $? != 0 ] && echo " ERROR: Could not compile (make) cdat code (2)" && popd && checked_done 1
        ${cmake_cmd}
        [ $? != 0 ] && echo " ERROR: Could not compile (make) cdat code (3)" && popd && checked_done 1

        echo "CMAKE ARGS"${cmake_args}
        make -j ${num_cpus}
        [ $? != 0 ] && echo " ERROR: Could not compile (make) cdat code (4)" && popd && checked_done 1

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

write_cdat_env() {
    ((show_summary_latch++))
    echo "export CDAT_HOME=${cdat_home}" >> ${envfile}
    prefix_to_path PATH ${cdat_home}/bin >> ${envfile}
    prefix_to_path PATH ${cdat_home}/Externals/bin >> ${envfile}
    prefix_to_path LD_LIBRARY_PATH ${cdat_home}/Externals/lib >> ${envfile}
    dedup ${envfile} && source ${envfile}
    return 0
}

write_cdat_install_log() {
    echo "$(date ${date_format}) uvcdat=${cdat_version} ${cdat_home}" >> ${install_manifest}

    #Parse the cdat installation config.log file and entries to the install log
    local build_log=${uvcdat_build_directory}/uvcdat_build/build_info.txt
    if [ -e "${build_log}" ]; then
        awk '{print "'"$(date ${date_format})"' uvcdat->"$1"="$2" '"${cdat_home}"'"}' ${build_log} | sed '$d' >> ${install_manifest}
    else
        echo " WARNING: Could not find cdat build logfile [${build_log}], installation log entries could not be generated!"
    fi

    dedup ${install_manifest}
    return 0
}

setup_cdat_xtra() {
    echo "Installing Extra Package ${1}"${uvcdat_build_directory}/uvcdat/Packages/$1
    cd ${uvcdat_build_directory}/uvcdat/Packages/$1 >& /dev/null
    env BUILD_DIR="." CFLAGS="-I${install_prefix}/Externals/include" ${install_prefix}/bin/python setup.py install
    [ $? != 0 ] && echo " Error could not install CDAT extra python package ${1} using ${install_prefix}/bin/python" 
}

setup_metrics() {
    cd ${metrics_build_directory} >& /dev/null
    ${install_prefix}/bin/python setup.py install
    [ $? != 0 ] && echo " Error could not install metrics python package using ${install_prefix}/bin/python" 
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
    cmake_min_version=2.8.12
    cmake_max_version=2.9
    cmake_version=2.8.12
    force_install=0
    DEBUG=1
    cdat_repo=git://github.com/UV-CDAT/uvcdat-devel.git
    cdat_repo_http=http://github.com/UV-CDAT/uvcdat-devel.git
    cdat_version="master"
    metrics_repo=git://github.com/PCMDI/wgne-wgcm_metrics.git
    metrics_repo_http=http://github.com/PCMDI/wgne-wgcm_metrics.git
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
    ## clone wgne repo
    git clone ${metrics_repo} ${metrics_build_directory}
    if [ ! -e ${metrics_build_directory}/.git/config ]; then
        echo " WARN: Could not clone metrics repo! Trying http protocol"
        git clone ${metrics_repo_http} ${metrics_build_directory}
        if [ ! -e ${metrics_build_directory}/.git/config ]; then
            echo " ERROR: Could not clone metrics repo! Check you are connected to the internet"
            exit 1
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
    setup_metrics
    pushd ${uvcdat_build_directory}/uvcdat >& /dev/null
    git apply ${metrics_build_directory}/src/patch_uvcdat.patch
    setup_cdat_xtra genutil
    setup_cdat_xtra xmgrace
    setup_cdat_xtra cdutil

    echo
    echo
    echo "*******************************"
    echo "UVCDAT - ${cdat_version} - Install Success"
    echo "Create your customized input_parameters.py (inspire yourself from examples in ${install_prefix}/doc/wgne_input_parameters_sample.py"
    echo "Once you have a parameter file run:"
    echo "${install_prefix}/bin/python ${install_prefix}/bin/wgne_metrics_driver.py -p /path/to/your/edited/parameter_file.py"
    echo "*******************************"
    echo

}
 main
