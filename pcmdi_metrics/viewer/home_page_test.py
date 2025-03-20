# Create Home Page
home_content = f"""
<!DOCTYPE html>
    <html lang="en">

    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PMP Viewer</title>
        <link rel="stylesheet" href="./assets/style.css">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">
        <div class="banner">
            <div class="viewer">
                <p>
                    (Prototype) <br>
                    <b>MIPS:</b> CMIP5, CMIP6 <br>
                    <b>EXPS:</b> historical, amip <br>
                    <b>Created:</b> 02-06-2025
                </p>
                <img src="./assets/PMPLogo_500x421px_72dpi.png" alt="PMP_logo">
                <h1>VIEWER</h1>
            </div>
        </div>
    </head>

    <body>

    <div class="container">
        <div class="responsive">
            <div class="gallery">
                <a target="_blank" href="https://pcmdi.llnl.gov/pmp-preliminary-results/graphics/mean_climate/cmip6/historical/clim/v20210811/pr/global/pr_cmip6_historical_ACCESS-CM2_djf_global.png">
                    <img src="https://pcmdi.llnl.gov/pmp-preliminary-results/graphics/mean_climate/cmip6/historical/clim/v20210811/pr/global/pr_cmip6_historical_ACCESS-CM2_djf_global.png" alt="mean_clim_divedown_test_img" width="600" height="300">
                </a>
                <div class="desc">Mean Climate Dive Down Plots</div>
            </div>
        </div>

        <div class="responsive">
            <div class="gallery">
                <a target="_blank" href="https://pcmdi.llnl.gov/pmp-preliminary-results/graphics/mean_climate/cmip6/historical/clim/v20210811/pr/global/pr_cmip6_historical_ACCESS-CM2_djf_global.png">
                    <img src="https://pcmdi.llnl.gov/pmp-preliminary-results/graphics/mean_climate/cmip6/historical/clim/v20210811/pr/global/pr_cmip6_historical_ACCESS-CM2_djf_global.png" alt="mean_clim_divedown_test_img" width="600" height="300">
                </a>
                <div class="desc">Mean Climate Dive Down Plots</div>
            </div>
        </div>
    </div>

    <div class="container">
        <div class="responsive">
            <div class="gallery">
                <a target="_blank" href="https://pcmdi.llnl.gov/pmp-preliminary-results/graphics/mean_climate/cmip6/historical/clim/v20210811/pr/global/pr_cmip6_historical_ACCESS-CM2_djf_global.png">
                    <img src="https://pcmdi.llnl.gov/pmp-preliminary-results/graphics/mean_climate/cmip6/historical/clim/v20210811/pr/global/pr_cmip6_historical_ACCESS-CM2_djf_global.png" alt="mean_clim_divedown_test_img" width="600" height="300">
                </a>
                <div class="desc">Mean Climate Dive Down Plots</div>
            </div>
        </div>

        <div class="responsive">
            <div class="gallery">
                <a target="_blank" href="https://pcmdi.llnl.gov/pmp-preliminary-results/graphics/mean_climate/cmip6/historical/clim/v20210811/pr/global/pr_cmip6_historical_ACCESS-CM2_djf_global.png">
                    <img src="https://pcmdi.llnl.gov/pmp-preliminary-results/graphics/mean_climate/cmip6/historical/clim/v20210811/pr/global/pr_cmip6_historical_ACCESS-CM2_djf_global.png" alt="mean_clim_divedown_test_img" width="600" height="300">
                </a>
                <div class="desc">Mean Climate Dive Down Plots</div>
            </div>
        </div>
    </div>

    </body>
    </html>
    """
with open("home_page_test.html", "w") as test_file:
    test_file.write(home_content)

# <img src="./assets/PCMDILogoText_1365x520px_300dpi.png" alt="PCMDI_logo" width="250px" style="margin-right: 850px; margin-top:20px;">
# <img src="./assets/PMPLogo_500x421px_72dpi.png" alt="PMP_logo" width="100px">
