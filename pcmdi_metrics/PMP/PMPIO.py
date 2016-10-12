import os
import logging
import json
import genutil
import cdat_info
import cdutil
import MV2
import cdms2
import hashlib
from CDP.base.CDPIO import *


class CDMSDomainsEncoder(json.JSONEncoder):
    def default(self, o):
        components = o.components()[0].kargs
        args = '.'.join(
            ['%s=%s' % (key, val) for key, val in components.iteritems()]
        )
        return {o.id: 'cdutil.region.domain(%s)' % args}


class PMPIO(CDPIO, genutil.StringConstructor):
    def __init__(self, root, file_template, file_mask_template=None):
        genutil.StringConstructor.__init__(self, root + '/' + file_template)
        self.target_grid = None
        self.mask = None
        self.target_mask = None
        self.regrid_tool = 'esmf'
        self.file_mask_template = file_mask_template
        self.root = root
        self.extension = ''
        self.setup_cdms2()

    def read(self):
        pass

    def __call__(self):
        path = os.path.abspath(genutil.StringConstructor.__call__(self))
        if self.extension in path:
            return path
        else:
            return path + '.' + self.extension

    def write(self, data, extension='json', *args, **kwargs):
        self.extension = extension.lower()
        file_name = self()
        dir_path = os.path.split(file_name)[0]

        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
            except:
                logging.error(
                    'Could not create output directory: %s' % dir_path)

        if self.extension == 'json':
            f = open(file_name, 'w')
            # data['metrics_git_sha1'] = pcmdi_metrics.__git_sha1__
            data['uvcdat_version'] = cdat_info.get_version()
            json.dump(data, f, cls=CDMSDomainsEncoder, *args, **kwargs)
            f.close()

        elif self.extension in ['asc', 'ascii', 'txt']:
            f = open(file_name, 'w')
            for key in data.keys():
                f.write('%s %s\n' % (key, data[key]))
            f.close()

        elif self.extension == 'nc':
            f = cdms2.open(file_name, 'w')
            f.write(data, *args, **kwargs)
            # f.metrics_git_sha1 = pcmdi_metrics.__git_sha1__
            f.uvcdat_version = cdat_info.get_version()
            f.close()

        else:
            logging.error('Unknown extension: %s' % extension)
            raise RuntimeError('Unknown extension: %s' % extension)

        logging.info('Results saved to a %s file: %s' % (extension, file_name))

    def get_var_from_netcdf(self, var, var_in_file=None,
                            region={}, *args, **kwargs):
        self.var_from_file = self.extract_var_from_file(
            var, var_in_file, *args, **kwargs)

        self.region = region
        if self.region is None:
            self.region = {}
        self.value = self.region.get('value', None)
        if self.is_masking():
            self.var_from_file = self.mask_var(self.var_from_file)

        self.var_from_file = \
            self.set_target_grid_and_mask_in_var(self.var_from_file)
        self.var_from_file = \
            self.set_domain_in_var(self.var_from_file, self.region)

        return self.var_from_file

    def extract_var_from_file(self, var, var_in_file, *args, **kwargs):
        if var_in_file is None:
            var_in_file = var
        self.extension = 'nc'
        var_file = cdms2.open(self(), 'r')
        extracted_var = var_file(var_in_file, *args, **kwargs)
        var_file.close()
        return extracted_var

    def is_masking(self):
        if self.value is not None:
            return True
        else:
            return False

    def mask_var(self, var):
        if self.mask is None:
            self.set_file_mask_template()
            self.mask = self.get_mask_from_var(var)
        if self.mask.shape != var.shape:
            dummy, mask = genutil.grower(var, self.mask)
        else:
            mask = self.target_mask
        mask = MV2.not_equal(mask, self.value)
        return MV2.masked_where(mask, var)

    def set_target_grid_and_mask_in_var(self, var):
        if self.target_grid is not None:
            var = var.regrid(self.target_grid, regridTool=self.regrid_tool,
                             regridMethod=self.regrid_method, coordSys='deg',
                             diag={}, periodicity=1
                             )
        if self.target_mask is not None:
            if self.target_mask.shape != var.shape:
                dummy, mask = genutil.grower(var, self.target_mask)
            else:
                mask = self.target_mask
            var = MV2.masked_where(mask, var)

        return var

    def set_domain_in_var(self, var, region):
        domain = region.get('domain', None)
        if domain is not None:
            if isinstance(domain, dict):
                var = var(**domain)
            elif isinstance(domain, (list, tuple)):
                var = var(*domain)
            elif isinstance(domain, cdms2.selectors.Selector):
                domain.id = region.get("id", "region")
                var = var(*[domain])
        return var

    def set_file_mask_template(self):
        if isinstance(self.file_mask_template, basestring):
            self.file_mask_template = PMPIO(self.root, self.file_mask_template,
                                            {'domain':
                                            self.region.get('domain', None)})

    def get_mask_from_var(self, var):
        try:
            o_mask = self.file_mask_template('sftlf')
        except:
            o_mask = cdutil.generateLandSeaMask(
                var, regridTool=self.regrid_tool).filled(1.) * 100.
            o_mask = MV2.array(o_mask)
            o_mask.setAxis(-1, var.getLongitude())
            o_mask.setAxis(-2, var.getLatitude())
        return o_mask

    def set_target_grid(self, target, regrid_tool='esmf',
                        regrid_method='linear'):
        self.regrid_tool = regrid_tool
        self.regrid_method = regrid_method
        if target == '2.5x2.5':
            self.target_grid = cdms2.createUniformGrid(
                -88.875, 72, 2.5, 0, 144, 2.5
            )
            self.target_grid_name = target
        elif cdms2.isGrid(target):
            self.target_grid = target
            self.target_grid_name = target
        else:
            logging.error('Unknown grid: %s' % target)
            raise RuntimeError('Unknown grid: %s' % target)

    def setup_cdms2(self):
        cdms2.setNetcdfShuffleFlag(0)  # Argument is either 0 or 1
        cdms2.setNetcdfDeflateFlag(0)  # Argument is either 0 or 1
        cdms2.setNetcdfDeflateLevelFlag(0)  # Argument is int between 0 and 9

    def hash(self, block_size=65536):
        self_file = open(self())
        buffer = self_file.read(block_size)
        hasher = hashlib.md5()
        while len(buffer) > 0:
            hasher.update(buffer)
            buffer = self_file.read(block_size)
        self_file.close()
        return hasher.hexdigest()
