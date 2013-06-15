#!/bin/bash

#####
# esg-functions: ESGF Node Application Stack Functions
# description: Installer Functions for the ESGF Node application stack
#
#****************************************************************************
#*                                                                          *
#*  Organization: Lawrence Livermore National Lab (LLNL)                    *
#*   Directorate: Computation                                               *
#*    Department: Computing Applications and Research                       *
#*      Division: S&T Global Security                                       *
#*        Matrix: Atmospheric, Earth and Energy Division                    *
#*       Program: PCMDI                                                     *
#*       Project: Earth Systems Grid Fed (ESGF) Node Software Stack         *
#*  First Author: Gavin M. Bell (gavin@llnl.gov)                            *
#*                                                                          *
#****************************************************************************
#*                                                                          *
#*   Copyright (c) 2009, Lawrence Livermore National Security, LLC.         *
#*   Produced at the Lawrence Livermore National Laboratory                 *
#*   Written by: Gavin M. Bell (gavin@llnl.gov)                             *
#*   LLNL-CODE-420962                                                       *
#*                                                                          *
#*   All rights reserved. This file is part of the:                         *
#*   Earth System Grid Fed (ESGF) Node Software Stack, Version 1.0          *
#*                                                                          *
#*   For details, see http://esgf.org/                                      *
#*   Please also read this link                                             *
#*    http://esgf.org/LICENSE                                               *
#*                                                                          *
#*   * Redistribution and use in source and binary forms, with or           *
#*   without modification, are permitted provided that the following        *
#*   conditions are met:                                                    *
#*                                                                          *
#*   * Redistributions of source code must retain the above copyright       *
#*   notice, this list of conditions and the disclaimer below.              *
#*                                                                          *
#*   * Redistributions in binary form must reproduce the above copyright    *
#*   notice, this list of conditions and the disclaimer (as noted below)    *
#*   in the documentation and/or other materials provided with the          *
#*   distribution.                                                          *
#*                                                                          *
#*   Neither the name of the LLNS/LLNL nor the names of its contributors    *
#*   may be used to endorse or promote products derived from this           *
#*   software without specific prior written permission.                    *
#*                                                                          *
#*   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS    *
#*   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT      *
#*   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS      *
#*   FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LAWRENCE    *
#*   LIVERMORE NATIONAL SECURITY, LLC, THE U.S. DEPARTMENT OF ENERGY OR     *
#*   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,           *
#*   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT       *
#*   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF       *
#*   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND    *
#*   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,     *
#*   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT     *
#*   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF     *
#*   SUCH DAMAGE.                                                           *
#*                                                                          *
#****************************************************************************
#####

#uses: perl, awk, ifconfig, tar, wget, curl, su, useradd, groupadd,
#      id, chmod, chown, chgrp, cut, svn, mkdir, killall, java, egrep,
#      lsof, unlink, ln, pax, keytool, openssl, getent

#note: usage of readlink not macosx friendly :-( usage of useradd /
#      groupadd is RedHat/CentOS dependent :-(

declare -r _ESG_FUNCTIONS_=1

#Needed to reduce the number of commands when wanting to make a verbose conditional print
verbose_print() { ((VERBOSE)) && echo $@; return 0; }
debug_print() { ((DEBUG)) && echo -e $@ >&2; return 0; }

_trimline() {
        # Strips leading and trailing whitespace even if IFS is set, also
        # removing the final newline on every line of input (i.e. the
        # result of using this on a multi-line string will be a
        # single-line string with no space between the last word on one
        # line and the first word on the next, with no leading or trailing
        # whitespace)
    echo "$@" | perl -p -e 's/^\s+|\s+$//g';
}

_version_cmp() {
    # Takes two strings, splits them into epoch (before the last ':'),
    # version (between the last ':' and the first '-'), and release
    # (after the first '-'), and then calls _version_segment_cmp on
    # each part until a difference is found.
    #
    # Empty segments are replaced with "-1" so that an empty segment
    # can precede a non-empty segment when being passed to
    # _version_segment_cmp.  As with _version_segment_cmp, leading
    # zeroes will likely confuse comparison as this is still
    # fundamentally a string sort to allow strings like "3.0alpha1".
    #
    # If $1 > $2, prints 1.  If $1 < $2, prints -1.  If $1 = $2, prints 0.
    # Usage example:
    #   if [ "$(_version_cmp $MYVERSION 1:2.3.4-5)" -lt 0 ] ; then ...

    EPOCHA=(`echo $1 | perl -ne 'my ($part)=/(.*):.*/;print "$part\n"'`)
    EPOCHB=(`echo $2 | perl -ne 'my ($part)=/(.*):.*/;print "$part\n"'`)
    EPOCHA=${EPOCHA:-"-1"}
    EPOCHB=${EPOCHB:-"-1"}

    NONEPOCHA=(`echo $1 | perl -ne 'my ($part)=/(?:.*:)?(.*)/;print "$part\n"'`)
    NONEPOCHB=(`echo $2 | perl -ne 'my ($part)=/(?:.*:)?(.*)/;print "$part\n"'`)

    VERSIONA=(`echo $NONEPOCHA | perl -ne 'my ($part)=/([^-]*)/;print "$part\n"'`)
    VERSIONB=(`echo $NONEPOCHB | perl -ne 'my ($part)=/([^-]*)/;print "$part\n"'`)
    VERSIONA=${VERSIONA:-"-1"}
    VERSIONB=${VERSIONB:-"-1"}

    RELEASEA=(`echo $NONEPOCHA | perl -ne 'my ($part)=/[^-]*-(.*)/;print "$part\n"'`)
    RELEASEB=(`echo $NONEPOCHB | perl -ne 'my ($part)=/[^-]*-(.*)/;print "$part\n"'`)
    RELEASEA=${RELEASEA:-"-1"}
    RELEASEB=${RELEASEB:-"-1"}

    EPOCHCMP=$(_version_segment_cmp ${EPOCHA} ${EPOCHB})
    if [ ${EPOCHCMP} -ne 0 ] ; then
        echo ${EPOCHCMP}
    else
        VERSIONCMP=$(_version_segment_cmp ${VERSIONA} ${VERSIONB})
        if [ ${VERSIONCMP} -ne 0 ] ; then
            echo ${VERSIONCMP}
        else
            RELEASECMP=$(_version_segment_cmp ${RELEASEA} ${RELEASEB})
            if [ ${RELEASECMP} -ne 0 ] ; then
                echo ${RELEASECMP}
            else
                echo "0"
            fi
        fi
    fi
}

_version_segment_cmp() {
    # Takes two strings, splits them on each '.' into arrays, compares
    # array elements until a difference is found.
    #
    # If a third argument is specified, it will override the separator
    # '.' with whatever characters were specified.
    #
    # This doesn't take into account epoch or release strings (":" or
    # "-" segments).  If you want to compare versions in the format of
    # "1:2.3-4", use _version_cmp(), which calls this function.
    #
    # If the values for both array elements are purely numeric, a
    # numeric compare is done (to handle problems such as 9 > 10 or
    # 02 < 1 in a string compare), but if either value contains a
    # non-numeric value or is null a string compare is done.  Null
    # values are considered less than zero.
    #
    # If $1 > $2, prints 1.  If $1 < $2, prints -1.  If $1 = $2, prints 0.
    #
    # Usage example:
    #   if [ "$(_version_segment_cmp $MYVERSION 1.2.3)" -lt 0 ] ; then ...

    SEP=${3:-"."}

    VERSIONA=(`echo $1 | perl -pe "s/[$SEP]/ /g"`)
    VERSIONB=(`echo $2 | perl -pe "s/[$SEP]/ /g"`)

    if [ ${#VERSIONA[*]} -gt ${#VERSIONB[*]} ] ; then
        VERSIONLENGTH=${#VERSIONA[*]}
    else
        VERSIONLENGTH=${#VERSIONB[*]}
    fi

    for index in `seq 1 $VERSIONLENGTH` ; do
        if ( [ -z ${VERSIONA[$index]##*[!0-9]*} ] ||
                [ -z ${VERSIONB[$index]##*[!0-9]*} ] ) ; then
            # Non-numeric comparison
            if [[ ${VERSIONA[$index]} > ${VERSIONB[$index]} ]] ; then
                echo "1"
                return
            elif [[ ${VERSIONA[$index]} < ${VERSIONB[$index]} ]] ; then
                echo "-1"
                return
            fi
        else
            # Purely numeric comparison
            if (( ${VERSIONA[$index]:-0} > ${VERSIONB[$index]:-0} )) ; then
                echo "1"
                return
            elif (( ${VERSIONA[$index]:-0} < ${VERSIONB[$index]:-0} )) ; then
                echo "-1"
                return
            fi
        fi
    done
    echo "0"
}

#-------------------------------
# Version Checking Utility Functions
#-------------------------------
checked_done() {
    if (($1)); then
        echo ""
        echo "Sorry..."
        echo "This action did not complete successfully"
        echo "Please re-run this task until successful before continuing further"
        echo ""
        echo "Also please review the installation FAQ it may assist you"
        echo "http://esgf.org/wiki/ESGFNode/FAQ"
        echo ""
        exit $1
    fi
    return 0
}

check_version_atleast() {
    # Takes the following arguments:
    #   $1: a string containing the version to test
    #   $2: the minimum acceptable version
    #
    # Returns 0 if the first argument is greater than or equal to the
    # second and 1 otherwise.
    #
    # Returns 255 if called with less than two arguments.

    debug_print "DEBUG: check_version_atleast \$1='$1'  \$2='$2'"

    if [[ -z "${1}" || -z "${2}" ]] ; then
        echo "CRITICAL FAILURE[1]: check_version_atleast called with insufficient arguments" >&2
        echo "  (\$1='$1'  \$2='$2')" >&2
        return 255
    fi

    if [ "$(_version_cmp ${1} ${2})" -ge 0 ] ; then return 0 ; fi
    return 1;
}

check_version_between() {
    # Takes the following arguments:
    #   $1: a string containing the version to test
    #   $2: the minimum acceptable version
    #   $3: the maximum acceptable version
    #
    # Returns 0 if the tested version is in the acceptable range
    # (greater than or equal to the second argument, and less than or
    # equal to the third), and 1 otherwise.
    #
    # Returns 255 if called with less than three arguments.

    debug_print "DEBUG: check_version_between \$1='$1'  \$2='$2'  \$3='$3'"

    if [[ -z "${1}" || -z "${2}" || -z "${3}" ]] ; then
        echo "CRITICAL FAILURE[2]: check_version_between called with insufficient arguments" >&2
        echo "  (\$1='$1'  \$2='$2'  \$3='$3')" >&2
        return 255
    fi

    if [ "$(_version_cmp ${1} ${2})" -ge 0 ] \
        && [ "$(_version_cmp ${1} ${3})" -le 0 ] ; then
        return 0 ;
    fi
    return 1;
}

check_version_helper() {
    # Primary helper method for verifying version constraints,
    # automatically detecting by argument count whether to check for a
    # minimum version or a range.
    #
    # Takes the following arguments:
    #   $1: a string containing the version to test
    #   $2: the minimum acceptable version
    #   $3 (optional): the maximum acceptable version
    #
    # If called with only one argument, the function will attempt to
    # split it on spaces into multiple arguments automatically, and
    # then follow the above argument logic.
    #
    # Returns 0 if the tested version is in the acceptable range
    #
    # Returns 255 if less than two arguments are detected after
    # automatic argument splitting.

    debug_print "DEBUG: check_version_helper \$1='$1'  \$2='$2'  \$3='$3'"

    # Split a lone argument
    [[ $# == 1 ]] && set -- $1

    # Spit out a nasty error message and return with 255 if there are
    # insufficient arguments (this causes the version check to fail,
    # but does NOT abort the script -- watch for the CRITICAL FAILURE
    # string in your output)
    if [[  -z "${1}" || -z "${2}"  ]]; then
        echo "CRITICAL FAILURE[3]: check_version_between called with insufficient arguments" >&2
        echo "  (\$1='$1'  \$2='$2'  \$3='$3')" >&2
        return 255
    fi

    if [ -z "${3}" ] ; then
        # Only two arguments, check for a minimum version
        check_version_atleast ${1} ${2}
        return $?
    fi
    check_version_between ${1} ${2} ${3}
    return $?
}

#--------------------------------------------------------------------------

check_version() {
    # This is the most commonly used "public" version checking
    # routine.  It delegates to check_version_helper() for the actual
    # comparison, which in turn delegates to other functions in a chain.
    #
    # Arguments:
    #   $1: a string containing executable to call with the argument
    #       "--version" or "-version" to find the version to check against
    #   $2: the minimum acceptable version string
    #   $3 (optional): the maximum acceptable version string
    #
    # Returns 0 if the detected version is within the specified
    # bounds, or if there were not even two arguments passed.
    #
    # Returns 1 if the detected version is not within the specified
    # bounds.
    #
    # Returns 2 if running the specified command with "--version" or
    # "-version" as an argument results in an error for both
    # (i.e. because the command could not be found, or because neither
    # "--version" nor "-version" is a valid argument)

    debug_print "\nDEBUG: check_version [$@]"
    [ -z "${2}" ] && return 0
    local min_version=${2}
    local max_version=${3}
    debug_print "min_version = [$min_version]"
    debug_print "max_version = [$max_version]"

    local version_tempfile=$(mktemp)
    $1 --version >& ${version_tempfile} || $1 -version >& ${version_tempfile}
    [ $? != 0 ] && echo && echo " WARNING: could not find a version from '$1'" && return 2

    local current_version=$(cat ${version_tempfile} 2>&1 | perl -ne '/(\d+\.+\d*\.*\d*[.-_@+#]*\d*).*/, print "$1 "' | tr -d "\"" | cut -d " " -f1,1)
    local current_version=$(_trimline ${current_version})
    debug_print "current_version = [$current_version]"

    check_version_helper "${current_version}" "${min_version}" "${max_version}"
    local ret=$?
    (($DEBUG2)) && echo "The return value from the call to helper function check_version_ is $ret"
    if [ $ret == 0 ] ; then
        rm -f ${version_tempfile}
        return 0
    fi

    printf "\nThe detected version of ${1} [${current_version}] is not between [${min_version}] and [${max_version}] \n"
    cat ${version_tempfile}
    rm -f ${version_tempfile}
    return 1
}

check_version_with() {
    # This is an alternate version of check_version() (see above)
    # where the second argument specifies the entire command string with
    # all arguments, pipes, etc. needed to result in a version number
    # to compare.
    #
    # Arguments:
    #   $1: a string containing the name of the program version to
    #       check (this is only used in debugging output)
    #   $2: the complete command to be passed to eval to produce the
    #       version string to test
    #   $3: the minimum acceptable version string
    #   $4 (optional): the maximum acceptable version string
    #
    # Returns 0 if the detected version is within the specified
    # bounds, or if at least three arguments were not passed
    #
    # Returns 1 if the detected version is not within the specified
    # bounds.
    #
    # Returns 2 if running the specified command results in an error

    debug_print "\nDEBUG: check_version_with  \$1='$1'"
    local app_name=${1}
    local version_command=${2:-"${app_name} --version"}
    local min_version=${3}
    local max_version=${4}
    debug_print "min_version = [$min_version]"
    debug_print "max_version = [$max_version]"

    [ -z "${min_version}" ] && return 0

    local current_version=$(eval ${version_command})
    if [ $? != 0 ] || [ -z "${current_version}" ]; then
        echo " WARNING: Could not detect version of ${app_name##*/}; Check the version command: [${version_command}] => value: [${current_version}]"
        return 2
    fi
    current_version=$(_trimline ${current_version})

    check_version_helper "${current_version}" "${min_version}" "${max_version}"
    local ret=$?
    debug_print " The return value from the call to helper function check_version_helper is $ret"
    [ $ret == 0 ] && return 0

    printf "\nThe detected version of ${app_name##*/} [${current_version}] is not between [${min_version}] and [${max_version}] \n"
    return 1
}

#For python module version checking
#Looking for __version__ var
check_module_version() {
    debug_print "\nDEBUG: check_module_version  \$1='$1'  \$2='$2'"
    local module_name=$1
    local min_version=$2

    local current_version=$(${cdat_home}/bin/python -c "import ${module_name}; print ${module_name}.__version__" 2> /dev/null)
    [ $? != 0 ] && echo " WARNING:(2) Could not detect version of ${module_name}" && return 2
    [ -z "${current_version}" ] && echo " WARNING:(1) Could not detect version of ${module_name}" && return 3

    check_version_helper "${current_version}" "${min_version}"
    local ret=$?
    debug_print " The return value from the call to helper function check_version_ is $ret"
    [ $ret == 0 ] && return 0

    printf "\nSorry, the detected version of $1 [${current_version}] is older than required minimum version [${min_version}] \n"
    return 1
}

get_current_esgf_library_version() {
    # Some ESGF components, such as esgf-security, don't actually
    # install a webapp or anything that carries an independent
    # manifest or version command to check, so they must be checked
    # against the ESGF install manifest instead.
    [ ! -f "/esg/esgf-install-manifest" ] && return 0
    local library_name=${1}
    local v=$(grep library:${1} /esg/esgf-install-manifest | cut -d= -f2)
    echo $v
    [ -n "${v}" ] && return 0 || return 1
}

get_current_webapp_version() {
    local webapp_name=$1
    local version_property=${2:-"Version"}
    local v=$(echo $(sed -n '/^'${version_property}':[ ]*\(.*\)/p' ${tomcat_install_dir}/webapps/${webapp_name}/META-INF/MANIFEST.MF | awk '{print $2}' | xargs 2> /dev/null))
    echo $v
    [ -n "${v}" ] && return 0 || return 1
}

check_webapp_version() {
    debug_print "\nDEBUG: check_webapp_version  \$1='$1'  \$2='$2'  \$3='$3'"
    local webapp_name=$1
    local min_version=$2
    local version_property=${3:-"Version"}

    [ ! -d "${tomcat_install_dir}/webapps/${webapp_name}" ] && echo " Web Application \"${webapp_name}\" is not present or cannot be detected!" && return 2

    local current_version=$(get_current_webapp_version ${webapp_name} ${version_property})
    local current_version=$(_trimline ${current_version})
    [ $? != 0 ] && echo " WARNING:(2) Could not detect version of ${webapp_name}" && return 3
    [ -z "${current_version}" ] && echo " WARNING:(1) Could not detect version of ${webapp_name}" && return 4

    check_version_helper "${current_version}" "${min_version}"
    local ret=$?
    debug_print " The return value from the call to check_version_helper is $ret"
    [ $ret == 0 ] && return 0

    printf "\nSorry, the detected version of $1 [${current_version}] is older than required minimum version [${min_version}] \n"
    return 1
}

#0ne-off version checking mechanism for applications where version number is in the name of the directory
#of the form "app_dir-<version_num>"
check_app_version() {
    debug_print "\nDEBUG: check_app_version  \$1='$1'  \$2='$2'"

    local app_dir=$1
    local min_version=$2

    local current_version=$(readlink -f ${tomcat_install_dir} | sed -ne 's/.*-\(.*\)$/\1/p')
    [ $? != 0 ] && echo " WARNING:(2) Could not detect version of ${app_dir##*/}" && return 2
    [ -z "${current_version}" ] && echo " WARNING:(1) Could not detect version of ${app_dir##*/}" && return 3

    check_version_helper "${current_version}" "${min_version}"
    local ret=$?
    debug_print " The return value from the call to helper function check_version_ is $ret"
    [ $ret == 0 ] && return 0

    printf "\nSorry, the detected version of ${app_dir##*/} [${current_version}] is older than required minimum version [${min_version}] \n"
    return 1
}

#----------------------------------------------------------
# Environment Management Utility Functions
#----------------------------------------------------------
remove_env() {
    local key=${1}
    ((DEBUG)) && echo "removing ${key}'s environment from ${envfile}"
    sed -i '/'${key}'/d' ${envfile}
    return $?
}

remove_install_log_entry() {
    local key=${1}
    ((DEBUG)) && echo "removing ${key}'s install log entry from ${install_manifest}"
    sed -i '/[:]\?'${key}'=/d' ${install_manifest}
    return $?
}

# Environment variable files of the form
# Ex: export FOOBAR=some_value
# Will have duplcate keys removed such that the
# last entry of that variable is the only one present
# in the final output.
# arg 1 - The environment file to dedup.
dedup() {
    local infile=${1:-${envfile}}
    [ ! -e "${infile}" ] && echo "WARNING: dedup() - unable to locate ${infile} does it exist?" && return 1
    [ ! -w "${infile}" ] && echo "WARNING: dedup() - unable to write to ${infile}" && return 1
    local tmp=$(tac ${infile} | awk 'BEGIN {FS="[ =]"} !($2 in a) {a[$2];print $0}' | sort -k2,2)
    echo "$tmp" > ${infile}
}

dedup_properties() {
    local infile=${1:-${config_file}}
    [ ! -e "${infile}" ] && echo "WARNING: dedup_properties() - unable to locate ${infile} does it exist?" && return 1
    [ ! -w "${infile}" ] && echo "WARNING: dedup_properties() - unable to write to ${infile}" && return 1
    local tmp=$(tac ${infile} | awk 'BEGIN {FS="[ =]"} !($1 in a) {a[$1];print $0}' | sort -k1,1)
    echo "$tmp" > ${infile}
}

#####
# Get Current IP Address - Needed (at least temporarily) for Mesos Master
####
#Takes a single interface value
# "eth0" or "lo", etc...
get_config_ip() {
    ifconfig $1 | grep "inet[^6]" | awk '{ gsub (" *inet [^:]*:",""); print $1}'
}


#----------------------------------------------------------
# Postgresql informational functions
#
# These functions require that Postgresql be already installed and
# running correctly.
#----------------------------------------------------------
postgres_create_db() {
    # Creates a database if it does not already exist
    if [ -z "$(postgres_list_dbs ${1})" ] ; then
        #Create the database...
        echo "Creating ESGF database: [${1}]"
        PGPASSWORD=${PGPASSWORD:-${pg_sys_acct_passwd}} createdb ${1} >& /dev/null
        (( $? > 1 )) && echo " ERROR: Could not create esgf node database: ${node_db_name}" && return $?
    else
        echo "ESGF database [${1}] already exists, not creating."
    fi
}

postgres_list_db_schemas() {
    # This prints a list of all schemas known to postgres.
    # If $1 is specified, it is used an awk filter
    # Returns the return value of the matches
    #
    # 'psql' must be in the path for this to work
    #
    (PGPASSWORD=${PGPASSWORD:-${pg_sys_acct_passwd}} \
        psql -U ${postgress_user:-"dbsuper"} ${db_database:-"esgcet"} \
             -qt -c "\dn;" | \
        awk '/'${1:-"."}'/ {print $1}' | \
        grep -Ev "^pg_.*")
}

postgres_list_schemas_tables() {
    # List all Postgres tables in all schemas, in the schemaname.tablename
    # format, in the ESGF database
    # If $1 is specified, it is used as a grep filter
    # Returns the return value of the final grep
    #
    # 'psql' must be in the path for this to work
    #
    (PGPASSWORD=${PGPASSWORD:-${pg_sys_acct_passwd}} \
        echo "SELECT schemaname,relname FROM pg_stat_user_tables;" \
        | psql -U ${postgress_user:-"dbsuper"} \
               ${db_database:-"esgcet"} -At \
        | tr '|' '.' \
        | grep ${1:-'.'})
}

postgres_list_dbs() {
    # This prints a list of all databases known to postgres.
    # If $1 is specified, it is used a grep filter
    # Returns the return value of the final grep
    #
    # 'psql' must be in the path for this to work
    #
    (PGPASSWORD=${PGPASSWORD:-${pg_sys_acct_passwd}} \
        psql -lat -U ${postgress_user:-"dbsuper"} | cut -d' ' -f2 | \
        grep -Ev "^(template[0-9]|postgres)$" | grep ${1:-"."})
}

postgres_clean_schema_migration() {
    # Removes entries from the esgf_migrate_version table if any exist
    # where repository_id matches an SQL LIKE to the first argument
    #
    # The SQL LIKE strings are generally defined in
    # "src/python/esgf/<reponame>/schema_migration/migrate.cfg" in
    # each relevant repository.
    if [ -n "$(postgres_list_schemas_tables public.esgf_migrate_version)" ] ; then
        if (( $(PGPASSWORD=${pg_sys_acct_passwd:=${security_admin_password}} \
            psql -U ${postgress_user} ${node_db_name} \
            -c "select count(*) from esgf_migrate_version where repository_id LIKE '%${1}%'" \
            | tail -n +3 | head -n 1) > 0 )); then
            echo "cleaning out schema migration bookeeping for esgf_node_manager..."
            $(PGPASSWORD=${pg_sys_acct_passwd:=${security_admin_password}} \
                psql -U ${postgress_user} ${node_db_name} \
                -c "delete from esgf_migrate_version where repository_id LIKE '%${1}%'" >& /dev/null)
        fi
    fi
}

#----------------------------------------------------------
# Process Launching and Checking...
#----------------------------------------------------------
#This function is for repeatedly running a function until it returns
#true and/or the number of iterations have been reached.  The format of
#the args for this call are as follows:
#
# pcheck <num_of_iterations> <wait_time_in_seconds> <return_on_true> -- [function name] <args...>
# The default operation is the run the function once a scecond for 5 seconds or until it returns true
# The default value of iterations is 5
# The default value of wait time is  1 (second)
# The default value of return on true is 1 (no more iterations after function/command succeeds)
# the "--" is a literal argument that MUST precede the function or command you wish to call
#
# Ex:
# Run a function or command foo 3x waiting 2 seconds between and returning after function/command success
# pcheck 3 2 1 -- foo arg1 arg2
# Run a function or command foo using defaults
# pcheck -- foo arg1 arg2
#
# Returns the value from the final execution of the function or command.
pcheck() {
    debug_print "pcheck $@"
    #initial default values
    local iterations=5
    local wait_time=1
    local return_on_true=1
    local task_function=""

    local_vars=(iterations wait_time return_on_true)
    local i=0
    while [[ -n "$1" ]]; do
        if [ "$1" == "--" ] ; then
            shift
            task_function=$1
            shift
            break
        fi
        eval local ${local_vars[((i++))]}=$1
        shift
    done
    debug_print "iterations = ${iterations}"
    debug_print "wait_time = ${wait_time}"
    debug_print "return_on_true = ${return_on_true}"
    debug_print "task_function = ${task_function}"
    debug_print "args = [$@]"

    local ret=1
    while [[ $iterations > 0 ]]; do
        echo -n "."
        eval ${task_function} $@
        ret=$?
        ((return_on_true)) && [ $ret == 0 ] && break
        ((iterations != 1)) && sleep ${wait_time}
        : $((iterations--))
    done
    [ $ret == 0 ] && printf "\n${task_function} [OK]\n" || printf "\n${task_function} [FAIL]\n"
    return $ret
}

#Utility function, wraps md5sum so it may be used on either mac or
#linux machines
md5sum_() {
    hash -r
    if type md5sum >& /dev/null; then
        echo $(md5sum $@)
    else
        echo $(md5 $@ | sed -n 's/MD5[ ]*\(.*\)[^=]*=[ ]*\(.*$\)/\2 \1/p')
    fi
}

#----------------------------------------------------------
# Path munging...
#----------------------------------------------------------
_path_unique() {
# Prints a unique path string
#
# The first (leftmost) instance of a path entry will be the one that
# is preserved.
#
# If $1 is specified, it will be taken as the string to deduplicate,
# otherwise $PATH is used.
#
# If $2 is specified, it will be taken as the path separator, which
# otherwise defaults to ':'
#
    local path_string=${1:-${PATH}}
    local pathsep=${2:-":"}

    echo -n ${path_string} | tr "${pathsep}" '\n' \
        | perl -e 'while (<>) { print $_ unless $s{$_}++; }' \
        | tr '\n' "${pathsep}"
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
    cd $(dirname ${file})
    file=$(basename ${file})

    # Iterate down symlinks.  If we exceed a maximum number symlinks, assume that
    # we're looped and die horribly.
    local maxlinks=20
    local count=0
    local current_dir
    while [ -L "${file}" ] ; do
        file=$(readlink ${file})
        cd $(dirname ${file})
        file=$(basename ${file})
        ((count++))
        if (( count > maxlinks )) ; then
            current_dir=$(pwd -P)
            echo "CRITICAL FAILURE[4]: symlink loop detected on ${current_dir}/${file}"
            cd ${start_dir}
            exit ${count}
        fi
    done
    current_dir=$(pwd -P)
    echo "${current_dir}/${file}"
    cd ${start_dir}
}

#----------------------------------------------------------
# Property reading and writing...
#----------------------------------------------------------
#Load properties from a java-style property file
#providing them as script variables in this context
#arg 1 - optional property file (default is ${config_file})
load_properties() {
    ((DEBUG)) && echo "load properties(): "
    local property_file=${1:-${config_file}}
    [ ! -r "${property_file}" ] && return 1
    dedup_properties ${property_file}
    IFS="="
    local count=0
    while read key value; do
        local key=$(echo $key |sed 's/\./_/g')
        [ -z "${key}" ] && continue
        ((DEBUG)) && echo -n "loading... "
        ((DEBUG)) && echo -n "[${key}] -> "
        ((DEBUG)) && echo "[${value}]"
        eval "${key}=\"${value}\""
        ((count++))
    done < ${property_file}
    echo "Loaded (imported) ${count} properties from ${property_file}"
    unset IFS
    return 0
}

#Gets a single property from a string arg and turns it into a shell var
#arg 1 - the string that you wish to get the property of (and make a variable)
#arg 2 - optional default value to set
get_property() {
    ((DEBUG)) && echo -n "get_property(): "
    local in_key=$1
    ((DEBUG)) && echo -n "[${in_key}] -> "
    local default=$2
    local prop_key=$(echo ${in_key} |sed 's/_/\./g')
    #dedup_properties ${config_file}
    local value=$(cat ${config_file} | sed -n 's/^\('${prop_key}'\)=\(.*$\)/\2/p' | xargs)
    [ -z "${value}" ] && [ -n "${default}" ] && value="${default}"
    ((DEBUG)) && echo "[${value}]"
    eval "${in_key}=\"${value}\""
    return 0
}

#Gets a single property from the arg string and turns the alias into a
#shell var assigned to the value fetched.
#arg 1 - the string that you wish to get the property of (and make a variable)
#arg 2 - the alias string value of the variable you wish to create and assign
#arg 3 - the optional default value if no value is found for arg 1
get_property_as() {
    ((DEBUG)) && echo -n "get_property_as(): "
    local in_key=$1
    ((DEBUG)) && echo -n "[${in_key}] -> "
    local alias=$2
    ((DEBUG)) && echo -n "[${alias}] -> "
    local default=$3
    local prop_key=$(echo ${in_key} |sed 's/_/\./g')
    #dedup_properties ${config_file}
    local value=$(cat ${config_file} | sed -n 's/^\('${prop_key}'\)=\(.*$\)/\2/p' | xargs)
    [ -z "${value}" ] && [ -n "${default}" ] && value=${default}
    ((DEBUG)) && echo "[${value}]"
    eval "${alias}=\"${value}\""
    return 0
}

#Removes a given variable's property representation from the property file
remove_property() {
    ((DEBUG)) && echo "removing $1's property from ${config_file}"
    local key=$(echo $1 |sed 's/_/\./g')
    sed -i '/'${key}'/d' ${config_file}
}

#Writes variable out to property file as java-stye property
#I am replacing all bash-style "_"s with java-style "."s
#arg 1 - The string of the variable you wish to write as property to property file
#arg 2 - The value to set the variable to (default: the value of arg1)
write_as_property() {
    ((DEBUG)) && echo -n "write_as_property(): "
    local key=$(echo $1 |sed 's/_/\./g')
    local value=${2:-${!1}}
    ((DEBUG)) && echo -n "[${key}] -> "
    ((DEBUG)) && echo "[${value}]"
    [ -z "${value}" ] && return 1
    cat >> ${config_file} <<EOF
${key}=${value}
EOF
    dedup_properties
    return 0
}

append_to_path() {
    # Appends path components to a variable, deduplicates the list,
    # then prints to stdout the export command required to append that
    # list to that variable
    #
    # Takes as arguments first a variable containing a colon-separated
    # path to append to, then a space-separated collection of paths to
    # append -- these path components MUST NOT contain spaces.
    #
    # If insufficient arguments are present, a warning message is
    # printed to stderr and nothing is printed to stdout.
    #
    # Example:
    #   append_to_path LD_LIBRARY_PATH /foo/lib /bar/lib
    #
    #   Would result in the entry:
    #     export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/foo/lib:/bar/lib
    #
    # NOTE: In the context of system setup this is usually
    #       NOT WHAT YOU WANT - use prefix_to_path (below)
    #
    local sep=':'
    local var="${1}"
    shift
    local appendage=$(echo "$@" | tr ' ' "${sep}")

    if [ -z "${var}" ] ; then
        echo "WARNING: append_to_path() called with no arguments!" >&2
        return
    fi
    if [ -z "${appendage}" ] ; then
        echo "WARNING: append_to_path() called with no path to append!" >&2
        return
    fi
    export ${var}=$(_path_unique \$${var}:${!var}:${appendage})
    echo "export ${var}=${!var}"
}

prefix_to_path() {
    # Prepends path components to a variable, deduplicates the list,
    # then prints to stdout the export command required to prepend
    # that list to that variable.
    #
    # Takes as arguments first a variable containing a colon-separated
    # path to prepend to, then a space-separated collection of paths to
    # prepend -- these path components MUST NOT contain spaces.
    #
    # If insufficient arguments are present, a warning message is
    # printed to stderr and nothing is printed to stdout.
    #
    # Example:
    #   prefix_to_path LD_LIBRARY_PATH /foo/lib /bar/lib
    #
    #   Would result in the entry:
    #     export LD_LIBRARY_PATH=/foo/lib:/bar/lib:$LD_LIBRARY_PATH
    #
    # NOTE: In the context of system setup this is usually
    #       WHAT YOU WANT; that your libs are found before any user libs are
    #
    local sep=':'
    local var="${1}"
    shift
    local appendage=$(echo "$@" | tr ' ' "${sep}")

    if [ -z "${var}" ] ; then
        echo "WARNING: prefix_to_path() called with no arguments!" >&2
        return
    fi
    if [ -z "${appendage}" ] ; then
        echo "WARNING: prefix_to_path() called with no path to prepend!" >&2
        return
    fi
    export ${var}=$(_path_unique ${appendage}:${!var}:\$${var})
    echo "export ${var}=${!var}"
}

#Given a directory the contents of the directory is backed up as a tar.gz file in
#arg1 - a filesystem path
#arg2 - destination directory for putting backup archive (default esg_backup_dir:-/esg/backups)
#arg3 - the number of backup files you wish to have present in destination directory (default num_backups_to_keep:-7)
backup() {
    [ -z "$1" ] && echo "backup - source must be provided as arg1" && return 1
    [ ! -d "$1" ] && echo "backup - must take a directory! $1 not a directory" && return 1
    local source="$(readlink -f $1)"
    local backup_dir=${2:-${esg_backup_dir:-"/esg/backups"}}
    local num_backups_to_keep=${3:-${num_backups_to_keep:-7}}

    echo "Backup - Creating a backup archive of ${source}"
    pushd ${source%/*} >& /dev/null
    mkdir -p ${backup_dir} >& /dev/null
    local backup_filename=$(readlink -f ${backup_dir})/${source##*/}.$(date ${date_format}).tgz
    tar czf ${backup_filename} ${source##*/}
    [ $? != 0 ] && echo " ERROR: Problem with creating backup archive: ${backup_filename}" && popd >& /dev/null && return 1
    if [ -e ${backup_filename} ]; then
        echo "Created backup: ${backup_filename}"
    else
        echo "Could not locate backup file ${backup_filename}"
        popd >& /dev/null
        return 1
    fi


    #-------------
    #keep only the last num_backups_to_keep files
    pushd ${backup_dir} >& /dev/null
    local files=(`ls -t | grep ${source##*/}.\*.tgz | tail -n +$((${num_backups_to_keep}+1)) | xargs`)
    if (( ${#files[@]} > 0 )); then
        echo "Tidying up a bit..."
        echo "${#files[@]} old backup files to remove: ${files[@]}"
        rm -v ${files[@]}
    fi
    popd >& /dev/null
    #-------------

    popd >& /dev/null
    return 0
}

#Get (or generate) the id suitable for use in the context of zookeeper
#and thus the sharded solr install.  If this variable is not set then
#an ID is generated, unique to this host.
#NOTE: A lot of things rely on this ID so at the moment it is okay to
#provide a simple way to be able to determine an id externally... but
#this is only something for the testing phase for the most part.
get_node_id() {
    esgf_node_id=${esgf_node_id:-$(sha1sum <(echo esgf$(hostname -i)) | awk '{print $1}')}
    echo ${esgf_node_id}
}


git-tagrelease() {
    # Makes a commit to the current git repository updating the
    # release version string and codename, tags that commit with the
    # version string, and then immediately makes another commit
    # appending "-devel" to the version string.
    #
    # This is to prepare for a release merge.  Note that the tag will
    # not be against the correct revision after a merge to the release
    # branch if it was not a fast-forward merge, so ensure that there
    # are no unmerged changes from the release branch before using.
    #
    # If that happens, delete the tag, issue a git reset --hard
    # against the last commit before the tag, merge the release
    # branch, and try again.
    #
    # Arguments:
    # $1: the release version string (mandatory)
    # $2: the release codename (optional)
    #
    # Examples:
    #   git-tagrelease v4.5.6 AuthenticGreekPizzaEdition
    # or just
    #   git-tagrelease v4.5.6

    # The file containing the release variables that needs to be modified
    RELEASEFILE="esg-node"

    # The strings that will be matched (against the beginning of a
    # line) for version and codename.  The values in ${1} and ${2}
    # will be wrapped in double-quotes and appended, replacing
    # whatever followed previously.
    VERSIONSTRING="script_version="
    CODENAMESTRING="script_release="

    if [ ! -f ${RELEASEFILE} ] ; then
        echo "The release file ('${RELEASEFILE}') was not found!"
        echo "Are you sure you're in the right repository and directory?"
        return 1
    fi

    if [ X"${1}" = "X" ] ; then
        echo "You didn't specify a release version!"
        return 2
    fi

    perl -p -i -e "s#^${VERSIONSTRING}.*#${VERSIONSTRING}\"${1}\"#" ${RELEASEFILE}

    COMMITSTRING="Update release version to ${1}"
    if [ X"${2}" != "X" ] ; then
        perl -p -i -e "s#^${CODENAMESTRING}.*#${CODENAMESTRING}\"${2}\"#" ${RELEASEFILE}
        COMMITSTRING="Update release version to ${1}, ${2}"
    fi

    git add ${RELEASEFILE}
    git commit -m "${COMMITSTRING}"
    git tag ${1}

    # Immediately set version "-devel" to distinguish further development
    perl -p -i -e "s#^${VERSIONSTRING}.*#${VERSIONSTRING}\"${1}-devel\"#" ${RELEASEFILE}
    git add ${RELEASEFILE}
    git commit -m "Update development version string to ${1}-devel"
}

#------------------------------------------
#Certificate Gymnasitcs
#------------------------------------------
declare -r expired=0
declare -r day=$((60*60*24))
declare -r warn=$((day*7))
declare -r info=$((day*30))

print_cert() {
    local cert=${1:?"You must provide the certificate file to print"}
    echo "CERTIFICATE = $cert"
    openssl x509 -noout -in $cert -subject -enddate
}

check_cert_expiry() {
    local file=${1}
    [ -z "${file}" ] && debug_print "skipping blank file entry" && continue
     #skip links
     [ -L "$file" ] && debug_print "skipping symlink" && continue

     verbose_print "inspecting ${file}"
     if ! openssl x509 -noout -in $file -checkend $info; then
         #file will expired in the maximal amount of time
         if ! openssl x509 -noout -in $file -checkend $expired; then
             certs_expire=$certs_expire"$(print_cert $file)\n\n"
             trash_expired_cert ${file}
         elif ! openssl x509 -noout -in $file -checkend $day; then
             certs_warn=$certs_day"$(print_cert $file)\n\n"
         elif ! openssl x509 -noout -in $file -checkend $warn; then
             certs_warn=$certs_warn"$(print_cert $file)\n\n"
         else
             certs_info=$certs_info"$(print_cert $file)\n\n"
         fi
     fi
}

check_cert_expiry_for_files() {
    echo "Checking for expired certs [file(s): $@]..."
    for file in $@
    do
        [ ! -e "${file}" ] && echo "no such file: ${file}, skipping... " && continue
        check_cert_expiry ${file}
    done
    local message=
    [ "$var_expire" ] && message=$message"Certificates will expire in:\n$var_expire\n"
    [ "$certs_expire" ] && message=$message"Certificates already expired :\n$certs_expire\n"
    [ "$certs_day" ] && message=$message"Certificates will expire within a day:\n$certs_day\n"
    [ "$certs_warn" ] && message=$message"Certificates expiring this week:\n$certs_warn\n"
    [ "$certs_info" ] && message=$message"Certificates expiring this month:\n$certs_info\n"

    #mail -s "Certificates Expiration closes" gavin@llnl.gov < <(printf "$message")
    printf "$message"
}

check_certs_in_dir() {
    local my_cert_dir=${1:-${ESGF_PROJECT_ROOT:-/tmp}/esg_trusted_certificates}
    echo "Checking for expired certs in dir: ${my_cert_dir} ..."
    for file in $(find ${my_cert_dir} -type f -regex '.*/[a-f0-9]*\.0')
    do
        check_cert_expiry $file
    done

    #Build message
    local message=
    [ "$certs_expire" ] && message=$message"Certificates already expired :\n$certs_expire\n"
    [ "$certs_day" ] && message=$message"Certificates will expire within a day:\n$certs_day\n"
    [ "$certs_warn" ] && message=$message"Certificates expiring this week:\n$certs_warn\n"
    [ "$certs_info" ] && message=$message"Certificates expiring this month:\n$certs_info\n"

    #mail -s "Certificates Expiration closes" gavin@llnl.gov < <(printf "$message")
    printf "$message"
}

trash_expired_cert() {
    local expired_cert=${1:?"Must provide certificate to trash"}
    mkdir -p ${ESGF_PROJECT_ROOT:-/tmp}/trash
    mv -v ${file} ${ESGF_PROJECT_ROOT:-/tmp}/trash
    echo "Trashed expired certificate $file"
}
#------------------------------------------

set_aside_web_app() {
    local app_home=$1

    ! $(echo ${app_home} | grep -q ${tomcat_install_dir}) && echo "WARNING: Bad application home directory [${app_home}]" && checked_done 1

    [ -d "${app_home}" ] && \
        echo "Moving Previous Installation of ${app_home##*/}..." && \
        mv -v ${app_home}{,.bak}
}

# arg1 = full path to web application
# arg2 = 0  = sucess
#        >0 = failure (return code style, pefect for taking "$?" of extraction command)
set_aside_web_app_cleanup() {
    local app_home=${1}
    local success=${2}

    ! $(echo ${app_home} | grep -q ${tomcat_install_dir}) && echo "WARNING: Bad application home directory [${app_home}]" && checked_done 1

    if [ -d "${app_home}.bak" ]; then
        if (( success == 0 )); then
            echo -n "Removing Previous Installation of ${app_home##*/}... "
            rm -rf "${app_home}.bak" && echo "[OK]" || echo "[FAIL]"
        else
            echo
            echo "*********************************************************************"
            echo "* WARNING: Problem with ${app_home##*/} application extraction...  *"
            echo "* Restoring previous installation                                  *"
            echo "*********************************************************************"
            mv -v ${app_home}{.bak,} && echo "[OK]" || echo "[FAIL]"
            echo
        fi
    fi
}
