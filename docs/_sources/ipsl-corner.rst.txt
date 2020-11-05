IPSL Corner
***********

Summary
=======
We want to develop what we have called "the Metrics Garden": this is an end-to-end facility to produce metrics (this part will be largely be done thanks to the PCMDI-MP, controlled by libIGCM, i.e. the library that controls the production of our simulations), store them on a database (through csv or json files, or directly from the package), and finally search for the metrics results on request and display them on interactive portrait plots via a web interface. Sebastien Denvil and I are dealing with the production of the metrics ; then we work with Mark Morgan for the storage of the results on a dedicated database ; Patrick Brockmann has designed the UI that will search for the results, and produce the interactive portrait plots ; he is also actively working with Mark Morgan for the exploitation of the database.

I detailed here point by point the different developments we are looking for. The aim is to discuss with you guys which ones are of interest for you and can be handled at PCMDI, and which ones will be done here at IPSL.

Indexation of the metric results
--------------------------------

The philosophy of the Metrics Garden is to allow crossing the results of various simulations and metrics on the portrait plots by:
* storing all the results on the same database
* and fetching the results we want (on request from the UI) for display
 
Following this, an important issue is to store the metric results with the appropriate indexation (set of keywords) on the database, so that we can find them afterwards. The indexation has to be univocal. In attached file [(see wiki page)](https://github.com/PCMDI/wgne-wgcm_metrics/wiki/Reference-Syntax-indexation) , you will find the set of keywords we identified as necessary to index the results. As you will see, we require much more information than what is currently available in the output json files. This is largely inspired from the CMIP5 DRS, and we already know that the CMIP6 DRS will be potentially different... anyway, the present document aims at opening discussions on this issue and we will be very happy to discuss it with you.
 The question here is to see with you guys if extending the information provided by the PCMDI-MP is something that could be interesting for you as well (notably for the information related to the reference and the metric). We could discuss this issue together, at least to define the good practices to develop this aspect within the PCMDI-MP.

Adding new metrics
------------------

 Another issue is to add a collection of metrics to document the mean state of the model. We are looking for the following metrics:

* latitude of the subtropical jets (in progress)
* ENSO metrics (with Eric)
* metrics for the sea ice following Massonnet et al. (2012) (attached file ; in progress)
* metrics for the turbulent fluxes (to be discussed with you Pete)
* ocean metrics ; the collection of metrics is not defined yet but it should be done in the coming months
* metrics for the land surfaces (work in progress with the ORCHIDEE people)
 
Among all those, what are the plans at PCMDI to include additionnal metrics to the PCMDI-MP (like the ENSO Metrics of Eric)? We can discuss about a little bit of coordination, both for the metrics and the references that will be added in the obs directory.
 We will create an "ipsl" directory within the "metrics" module, where we will add all the diagnostics developed at IPSL (in parallel of the "wgne" module, so that we don't interfere with what you guys do).

Miscellaneous
-------------

* a Python dictionnary correspondance table for the variable names: would you have specific recommendation for this? Do you plan to include a template of such correspondance table in the PCMDI-MP?
* when I was at the PCMDI, we talked about a way to recognize the variable units ; do you confirm that it is still of interest (I've seen that there is a branch on github that should deal with this issue)
* in some cases, the regridding is not necessary for the calculation of the metrics (as for the position of the subtropical jets). Would you consider adding an option in the parameter file so that the regridding can be switched off?

Future developments and challenges
----------------------------------

 In the future, the question is also whether we could plan to calculate metrics derived from temporal or spatio-temporal analysis (spectrums, EOFs) ; the aim would be to have metrics for the main variability modes (AO-NAO, PNA...), weather regimes and QBO (to give some examples). Is it in the plans of the PCMDI to develop the package to handle time series (longer than the 12 months of the annual cycle)?

If we want to describe a given metric and that this description is univocal,
we have to give enough information on the numerical experiment (or
simulation), the reference, the regridding method and the metric itself. We
have identified the following suite of keywords that could be able to fully identify a metric.

In the json files, at IPSL we want to have the keyword/value pairs. Example: "MetricName":"rms_xyt"
We would need to do this for all the keywords.

Concerning the different tracking dates, that would be a good point to agree on a given format for all the date provided in the json file.

Some elements (quoted with "!!!") necessitate more thoughts. As well, we could add more details on the respective grids of both the numerical experiment and the reference. Feedbacks and further discussions are welcome!



  * Description of the simulation

    * ModelActivity = project name (CMIP3, CMIP5…), or the type of simulation that we run at IPSL (PROD, DEVT or TEST) ; this is surely a keyword that has to be discussed

    * ModellingGroup = name of the modelling group (ex: IPSL, KNMI…); same names as in the CMIP5 tree

    * Model = model name (ex: HadGEM, CNRM-CM5...)

    * !!! MIPtable = Amon, Omon… we are not sure that the MIPtable has to be part of the indexation; maybe there is something more clever to be done

    * Experiment = the type of experiment (ex: historical, amip…)

    * SimName = the name of the numerical experiment of simulation (ex: r1i1p1, mysimname1…)

    * ModelFreeSpace = a custom comment to add some more information that can be helpful to document some details on the simulation

    * Login = for us at IPSL, login on which the simulation has been ran

    * Center = for us at IPSL, name of the computing center

    * SimTrackingDate = date of the creation of the file (end of the simulation or update)

  * Description of the reference

    * !!! RefActivity = if there is one, the project associated with the reference (obs4mips…)

    * RefName = the reference name (ex: ERAInterim, CERES-EBAF, AIRS…)

    * !!! RefType = what type of reference is it ? (ex: reanalysis, in-situ, satellite…) (should we merge RefActivity and RefType ?)

    * RefTrackingDate = date of creation of the file (a date that gives a possibility to track down an update)

    * RefFreeSpace = a custom comment to add some more information ; maybe not needed but say it's rather cheap to add it.

  * Description of the regridding

    * RegridMethod = the regridding method that has been used to do the model/reference comparison (bilinear, ESMF, None…)

    * GridName = the name of the grid (ex: regular, gaussian, ORCA, None…)

    * !!! GridResolution = the effective average horizontal grid resolution (ex: 2x2) or the number of grid points and vertical levels (ex: 96x96x39) ; at the moment we provide a tuple, ex: ( 96, 96 ). Should we rather go for a character chain?

  * Description of the metric:

    * Period = period on which the metric is calculated (ex: 1980-01-01_2005-12-31)

    * MetricName = name of the metric (ex: RMSE, corr, ENSO_Metrics_1…)

    * MetricReferenceArticle = explicit ; example: "Gleckler et al. 2009"

    * DataType = the type of data we are using (ex: “SE” for a seasonal cycle, “TS_MO” for a monthly time series, “Ann” for the annual mean…)

    * DomainName = the name of the domain we are working on (ex: Globe, NHEX, MyCustomDomain…)

    * Region = we have to decide whether we use region or domain to provide the information if we are working on land surface, ocean or global

    * GeographicalBounds = the geographical limits of the domain (if it is a lon x lat domain) (ex: 20.00E_120.00E_20.00S_20.00N)

    * Variable (if more than one variable => separate them with a _: t2m_slp; if incorrect/insufficient, leave the field empty and find an explicit and unique MetricName)

    * MetricFreeSpace = a custom comment to add some more information

    * Result = explicit

    * P-value = the p-value of the associated statistical test (ex: 2.e-16, 0.002, None…)

    * 95signifThreshold = the threshold value of the statistic corresponding to the 95% significance level (ex: the value of the correlation coefficient that is significant at 95% for the related number of dof)

    * MetricContactExpert = the email of the contact, in general the developer of the metric (Ex: Jean-Louis.Dufresne@lmd.jussieu.fr)

    * MetricTrackingDate = date of calculation of the metric



