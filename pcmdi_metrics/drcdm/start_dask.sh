#!/usr/bin/env bash
set -eou pipefail
CPUS_PER_TASK=${CPUS_PER_TASK:-32}
MEM_FRACTION=${MEM_FRACTION:-0.9}
WORKER_PROCESSES=${WORKER_PROCESSES:-1}
LOCAL_DIR_BASE=${LOCAL_DIR_BASE:-/pscratch/sd/j/$USER/dask-tmp}
NODES=($(scontrol show hostnames "$SLURM_NODELIST"))
echo ${NODES}
SCHED_NODE=${NODES[0]}
SCHED_PORT=${SCHED_PORT:-8786}
SCHED_ADDR="tcp://${SCHED_NODE}:${SCHED_PORT}"

mkdir -p "${LOCAL_DIR_BASE}"

echo "Scheduler: ${SCHED_ADDR}"
echo "Launching scheduler on ${SCHED_NODE}"

srun --nodes=1 --ntasks=1 --cpus-per-task=2 \
     --nodelist="${SCHED_NODE}" \
     dask scheduler --host "${SCHED_NODE}" --port "${SCHED_PORT}" \
     > scheduler.log 2>&1 &

sleep 5

echo "Launching ${WORKER_PROCESSES} worker(s) per node on ${#NODES[@]} nodes(s)..."


srun --nodes=${#NODES[@]} --ntasks=${#NODES[@]} \
     --cpus-per-task=${CPUS_PER_TASK} \
     dask worker "${SCHED_ADDR}" \
       --nthreads ${CPUS_PER_TASK} \
       --nworkers ${WORKER_PROCESSES} \
       --memory-limit auto \
       --local-directory ${LOCAL_DIR_BASE} \
       --lifetime-stagger 5m \
       --lifetime-restart \
     > workers.log 2>&1 &

echo
echo "from dask.distributed import Client; Client('${SCHED_ADDR}')"
