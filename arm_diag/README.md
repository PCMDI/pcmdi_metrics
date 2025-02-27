# ARM Diagnostic package

#### 1. Install PMP
Install PMP via conda following [these instructions](http://pcmdi.github.io/pcmdi_metrics/install.html). For example:

conda create -n [YOUR_CONDA_ENVIRONMENT] -c conda-forge pcmdi_metrics
 

#### 2. Activate PMP installed conda environment
Activate your environment (if PMP installed env is differnt than your current one):

conda activate [YOUR_CONDA_ENVIRONMENT]


#### 3. Clone PMP repo to your local
Clone PMP repo to your local for pre-calculated data:

git clone https://github.com/PCMDI/pcmdi_metrics

cd [YOUR LOCAL CLONED PMP REPOSITORY]
git submodule update --init --recursive


#### 4. Modified paths for ARM Diagnostic package
cd pcmdi_metrics/pcmdi_metrics/arm_diags

edit arm_diag_driver.py for user defined paths

#### 5. Run ARM Diagnostic package

python arm_diag_driver.py

## References

Overview of the ARM-Diags:

Zhang, C., S. Xie, C. Tao, S. Tang, T. Emmenegger, J. D. Neelin, K. A. Schiro, W. Lin, and Z. Shaheen. "The ARM Data-oriented Metrics and Diagnostics Package for Climate Models-A New Tool for Evaluating Climate Models with Field Data." Bulletin of the American Meteorological Society (2020).
Technical report, 2024: "ARM Data-Oriented Metrics and DiagnosticsPackage (ARM-Diags) for Climate Model Evaluation" https://portal.nersc.gov/project/capt/ARMVAP/ARM_DIAG_v4.pdf
Presentation at ARM/ASR meeting 2020: "ARM Data-Oriented Diagnostics to Evaluate the Climate Model Simulation" https://asr.science.energy.gov/meetings/stm/presentations/2020/976.pdf
Presentation at ARM/ASR meeting 2023: "Overview of ARM diagnostic package (ARM-Diags) and its applications to climate model evaluation" https://asr.science.energy.gov/meetings/stm/presentations/2023/1576.pdf

Applications of the ARM-Diags:

Zhang, C., S. Xie, S. A. Klein, H.-Y. Ma, S. Tang, K. V. Weverberg, C. Morcrette, and J. Petch (2018), CAUSES: Diagnosis of the summertime warm bias in CMIP5 climate models at the ARM Southern Great Plains site, Journal of Geophysical Research: Atmospheres, 123(6), doi:10.1002/2017JD027200.
Emmenegger, T., Y. Kuo, S. Xie, C. Zhang, C. Tao, and J. D. Neelin, 2022: Evaluating Tropical Precipitation Relations in CMIP6 Models with ARM Data. J. Climate, 35, 6343–6360, https://doi.org/10.1175/JCLI-D-21-0386.1.
Zheng, X., C. Tao, C. Zhang, S. Xie, Y. Zhang, B. Xi, and X. Dong, 2023: Assessment of CMIP5 and CMIP6 AMIP Simulated Clouds and Surface Shortwave Radiation Using ARM Observations over Different Climate Regions. J. Climate, 36, 8475–8495, https://doi.org/10.1175/JCLI-D-23-0247.1.
Emmenegger, T., F. Ahmed, Y. Kuo, S. Xie, C. Zhang, C. Tao, and J. D. Neelin, 2024: The Physics behind Precipitation Onset Bias in CMIP6 Models: The Pseudo-Entrainment Diagnostic and Trade-Offs between Lapse Rate and Humidity. J. Climate, 37, 2013–2033, https://doi.org/10.1175/JCLI-D-23-0227.1.
