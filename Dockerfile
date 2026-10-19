FROM condaforge/miniforge3:24.11.3-0

SHELL ["/bin/bash", "-lc"]

WORKDIR /opt/pmp

COPY conda-env/ci.yml /tmp/conda-env-ci.yml

RUN python - <<'PY' && \
from pathlib import Path

src = Path('/tmp/conda-env-ci.yml')
dst = Path('/tmp/conda-env-ci-docker.yml')
lines = src.read_text().splitlines()
dst.write_text('\n'.join(line for line in lines if not line.startswith('prefix:')) + '\n')
PY
    conda env create -n pcmdi_metrics_ci -f /tmp/conda-env-ci-docker.yml && \
    conda clean -afy

COPY . /opt/pmp

RUN conda run -n pcmdi_metrics_ci python -m pip install --no-build-isolation --no-deps . && \
    conda clean -afy

ENV CONDA_DEFAULT_ENV=pcmdi_metrics_ci
ENV PATH=/opt/conda/envs/pcmdi_metrics_ci/bin:/opt/conda/bin:${PATH}

CMD ["python", "-c", "import pcmdi_metrics; print(f'PMP is ready: {pcmdi_metrics.__version__}')"]
