#!/usr/bin/env python

import MV2
import cdms2
import vcs
import genutil
from genutil import StringConstructor

class Plot_defaults:
    def __init__(self):
        self.x1=.12
        self.x2=.84
        self.y1=.17
        self.y2=.8
        self.levels=None
        self.colormap=None
        self.fillareacolors=None
        self.legend_x1=.89
        self.legend_x2=.91
        self.legend_y1=self.y1
        self.legend_y2=self.y2
        x=vcs.init()
        #X ticks
        self.xticorientation=x.createtextorientation()
        self.xticorientation.angle=360-90
        self.xticorientation.halign='right'
        self.xticorientation.height=10
        #Y ticks
        self.yticorientation=x.createtextorientation()
        self.yticorientation.angle=0
        self.yticorientation.halign='right'
        self.yticorientation.height=10
        # Ticks table
        self.tictable=x.createtexttable()
        # parameters text settings
        self.parameterorientation=x.createtextorientation()
        self.parameterorientation.angle=0
        self.parameterorientation.halign='center'
        self.parameterorientation.height=20
        self.parametertable=x.createtexttable()
        # Defaults
        self.draw_mesh='y'
        self.missing_color=240
        self.xtic1y1=None
        self.xtic1y2=None
        self.xtic2y1=None
        self.xtic2y2=None
        self.ytic1x1=None
        self.ytic1x2=None
        self.ytic2x1=None
        self.ytic2x2=None
        # Set the logo textorientation
        logo = x.createtext()
        logo.height = 20
        logo.halign = 'center'
        logo.path = 'right'
        logo.valign = 'half'
        # Set the logo texttable
        logo.font = 3
        logo.spacing = 2
        logo.expansion = 100
        logo.color = 250
        logo.string='PCMDI'
        logo.x=[.9]
        logo.y=[.98]
        self.logo=logo
        # Set the time stamp
        time_stamp = x.createtext()
        time_stamp.height = 10
        time_stamp.halign = 'center'
        time_stamp.path = 'right'
        time_stamp.valign = 'half'
        time_stamp.x = [0.9]
        time_stamp.y = [0.96]
        self.time_stamp=time_stamp
        
class Portrait:
    def __init__(self,files_structure=None,exclude=[],**kw):
        ''' initialize the portrait object, from file structure'''
        self.verbose = True # output files looked for to the screen
        self.files_structure=files_structure
        self.exclude=exclude
        # First determine the list of parameters on which we can have a portrait
        self.parameters_list=[]
        self.dummies=[]
        self.auto_dummies=[]
        self.grouped=[]
        self.slaves={}
        self.altered={}
        self.aliased={}
        self.portrait_types={}
        self.PLOT_SETTINGS=Plot_defaults()
        if files_structure is not None:
            sp=files_structure.split('%(')
            for s in sp:
                i=s.find(')')
                if i>-1: # to avoid the leading path
                    val=s[:i]
                    if not (val in self.parameters_list or val in ['files_structure','exclude']) :
                        self.parameters_list.append(s[:i])
        self.parameters_list.append('component')
        self.parameters_list.append('statistic')
        self.parameters_list.append('time_domain')
        for p in self.parameters_list:
            setattr(self,p,None)
        for k in kw.keys():
            setattr(self,k,kw[k])

    def alter_parameter(self,parameter=None,x=None,y=None,size=None,color=None):
        if not parameter is None:
            self.altered[parameter]={'x':x,'y':y,'size':size,'color':color}
        else:
            if not color is None:
                self.PLOT_SETTINGS.parametertable.color=color
            if not size is None:
                self.PLOT_SETTINGS.parameterorientation.size=size
        
    def string_construct(self,nms):
        n=nms[0]
        if not n in self.slaves.keys():
            t1=[n+' ' for nn in getattr(self,n)]
            t2=[str(nn)+' ' for nn in getattr(self,n)]
        else:
            slavs=self.slaves[n]
            nm=''
            for i in slavs:
                nm=nm+' '+i
            t1=[n+nm+' ' for nn in getattr(self,n)]
            v1=[res for res in getattr(self,n)]
            vals=[]
            for i in  range(len(v1)):
                tmp=''
                for a in v1[i]:
                    if not a=='':
                        tmp+=' '+str(a)+' '
                    else:
                        tmp+=' NONE'+' '
                vals.append(tmp)
            t2=[nn for nn in vals]
        for n in nms[1:]:
            if not n in self.slaves.keys():
                t1=[' '+t+' '+n for t in t1 for nn in getattr(self,n)]
                t2=[' '+t+' '+str(nn) for t in t2 for nn in getattr(self,n)]
            else:
                slavs=self.slaves[n]
                nm=' '
                for i in slavs:
                    nm=' '+nm+' '+i
                t1b=[n+nm for nn in getattr(self,n)]
                v1=[res for res in getattr(self,n)]
                vals=[]
                for i in  range(len(v1)):
                    tmp=''
                    for a in v1[i]:
                        if not a=='':
                            tmp+=' '+str(a)
                        else:
                            tmp+=' NONE'
                    vals.append(tmp)
                t2b=[nn for nn in vals]
                t1=[t+tb for t in t1 for tb in t1b]
                t2=[t+tb for t in t2 for tb in t2b]
        t3=[]
        t1=t1[0]
        sp=t1.split()
        n=len(sp)
        for tmp in t2:
            if isinstance(tmp,int):tmp=str(tmp)
            t=[]
            tt=tmp.split()
            for i in range(n):
                t.append(self.makestring(sp[i],tt[i]))
            t3.append("%%%".join(t))
        return t1,t2,t3


    def set(self,portrait_type,parameter=None,values=None):
        if portrait_type.lower()=='absolute':
          if 'relative' in self.portrait_types.keys():
              del(self.portrait_types['relative'])
        elif portrait_type.lower()=='relative':
          if not isinstance(parameter,str):
                raise 'Parameter must be a string'
          if not isinstance(values,(list,tuple)):
                raise 'values must be a list or tuple'
          self.portrait_types['relative']=[parameter,values]
        elif portrait_type.lower()=='difference':
          if not isinstance(parameter,str):
                raise 'Parameter must be a string'
          if not isinstance(values,(list,tuple)):
                raise 'values must be a list or tuple'
          self.portrait_types['difference']=[parameter,values]
        elif portrait_type.lower() in ['mean','average']:
          if not isinstance(parameter,str):
              raise 'Parameter must be a string'
          if not isinstance(values,(list,tuple)):
              raise 'values must be a list or tuple'
          self.portrait_types['mean']=[parameter,values]
        else:
            raise RuntimeError('Error type:"%s" not supported at this time' % (portrait_type))
        
    def dummy(self,parameter,which_dummy=''):
        ''' Sets a parameter as dummy, i.e. all possible values will be used'''
        val=getattr(self,which_dummy+'dummies')
        if not parameter in val:
            val.append(parameter)
            setattr(self,which_dummy+'dummies',val)
            setattr(self,parameter,None)

    def group(self,param1,param2):
        ''' sets 2 multiple values of parameters on the same axis'''
        added=0
        for i in range(len(self.grouped)):
            g=self.grouped[i]
            if param1 in g:
                if not param2 in g:
                    added=1
                    self.grouped[i].append(param2)
            elif param2 in g:
                added=1
                self.grouped[i].append(param1)
        if not added:
            self.grouped.append([param1,param2])
            
    def slave(self,master,slave):
        ''' defines a parameter as a slave of a master parameter'''
        if master in self.slaves.keys():
            v=self.slaves[master]
            if not slave in v:
                v.append(slave)
                self.dummy(slave,which_dummy='auto_')
                self.slaves[master]=v
        else:
            self.slaves[master]=[slave]
            self.dummy(slave,which_dummy='auto_')
                

    def alias(self,parameter,values):
        if isinstance(values,dict):
            self.aliased[parameter]=values
        else:
            oldvalue=getattr(self,parameter)
            if parameter in self.slaves.keys():
                ov=[]
                for n in oldvalue:
                    ov.append(n[0])
                oldvalue=nv
            n=len(oldvalue)
            if len(values)!=n:
                raise 'Error aliasing '+parameter+' you submitted '+str(len(values))+' aliases but it should be:'+str(n)
            dic={}
            for i in range(n):
                dic[oldvalue[i]]=values[i]
            self.aliased[parameter]=dic
            
    def makestring(self,parameter,value):
        if parameter in self.aliased.keys():
            dic=self.aliased[parameter]
            if value in dic.keys():
                return dic[value]
            else:
                return value
        else:
            return value
    
    
    def makeaxis(self,names,axis_length):
        """
        Create the axis with the names, etc.. .for portrait plot
        Usage:
        makeaxis(self,names,axis_length)
        Returns:
        a cdms axis
        """
        # Now creates the axis names
        t1,t2,t3=self.string_construct(names)
        
        sp1=t1.split()
        axis_names=[]
        for i in range(len(t2)):
            nm=''
            sp2=t3[i].split('%%%')
            for j in range(len(sp2)):
                if not sp1[j] in self.dummies and not sp2[j]=='NONE':
                    #print sp2,j
                    if not sp2[j][0]=='_':
                        nm+=' '+sp2[j]
                    else:
                        nm+=' '+sp2[j][1:]
            axis_names.append(nm)
        dic={}
        for i in range(len(axis_names)):
            dic[i]=axis_names[i]
        y=cdms2.createAxis(range(axis_length))
        y.names=repr(dic)
        nm=[]
        for t in sp1:
            if not t in self.dummies:
                nm.append(t)
        nm="___".join(nm)
        y.id=nm
        return y

    def rank(self,data,axis=0):
        if not axis in [0,1]:
            if not isinstance(axis,str):
                raise 'Ranking error, axis can only be 1 or 2 or name'
            else:
                nms=data.getAxisIds()
                for i in range(len(nms)):
                    nm=nms[i]
                    if axis in nm.split('___'):
                        axis=i
                if not axis in [0,1]:raise 'Ranking error, axis can only be 1 or 2 or name'
        if data.rank()>2:
            raise "Ranking error, array can only be 2D"

        if axis==1:
            data=MV2.transpose(data)
        a0=MV2.argsort(data.filled(1.E20),axis=0)
        n=a0.shape[0]
        b=MV2.zeros(a0.shape,MV2.float)
        sh=a0[1].shape
        for i in range(n):
            I=MV2.ones(sh)*i
            c=MV2.array(a0[i].filled(n-1))
            b=genutil.arrayindexing.set(b,c,I)
        
        m=data.mask
        if not m is None:
            b=MV2.masked_where(m,b)
        else:
            b=MV2.array(b)
        n=MV2.count(b,0)
        n.setAxis(0,b.getAxis(1))
        b,n=genutil.grower(b,n)
        b=100.*b/(n-1)
        b.setAxisList(data.getAxisList())
        if axis==1:
            b=MV2.transpose(b)
            data=MV2.transpose(data)
        return b
    
    def rank_nD(self,data,axis=0):
        if not axis in [0,1]:
            if not isinstance(axis,str):
                raise 'Ranking error, axis can only be 1 or 2 or name'
            else:
                nms=data.getAxisIds()
                for i in range(len(nms)):
                    nm=nms[i]
                    if axis in nm.split('___'):
                        axis=i
                if not axis in [0,1]:raise 'Ranking error, axis can only be 1 or 2 or name'

        if axis!=0:
            data=data(order=(str(axis)+'...'))
        a0=MV2.argsort(data.filled(1.E20),axis=0)
        n=a0.shape[0]
        b=MV2.zeros(a0.shape,MV2.float)
        sh=a0[1].shape
        for i in range(n):
            I=MV2.ones(sh)*i
            c=MV2.array(a0[i].filled(n-1))
            b=genutil.arrayindexing.set(b,c,I)
        m=data.mask
        if not m is None:
            b=MV2.masked_where(m,b)
        else:
            b=MV2.array(b)
        n=MV2.count(b,0)
        n.setAxisList(b.getAxisList()[1:])
        b,n=genutil.grower(b,n)
        b=100.*b/(n-1)
        b.setAxisList(data.getAxisList())
        if axis!=0:
            st=''
            for i in range(axis):
                st+=str(i+1)
            st+='0...'
            data=data(order=st)
            b=b(order=st)
        return b
        
    
    def get(self):
        if 'difference' in self.portrait_types.keys():
            d=self.portrait_types['difference']
            setattr(self,d[0],d[1][0])
            a1=self._get()
            setattr(self,d[0],d[1][1])
            a2=self._get()
            return a1-a2
        elif 'mean' in self.portrait_types.keys():
            d=self.portrait_types['mean']
            setattr(self,d[0],d[1][0])
            tmp+=self._get()
            for v in d[1][1:]:
                setattr(self,d[0],v)
                tmp+=self._get()
            return tmp/len(d[1])
        else:
            return self._get()
    def _get(self):
        if 'relative' in self.portrait_types.keys():
            d=self.portrait_types['relative']
            vals=d[1]
            real_value=getattr(self,d[0])
            real=self.__get()
            setattr(self,d[0],vals[0])
            a0=self.__get()
            sh=list(a0.shape)
            sh.insert(0,1)
            a0=MV2.reshape(a0,sh)
            for v in vals[1:]:
                setattr(self,d[0],v)
                tmp=self.__get()
                tmp=MV2.reshape(tmp,sh)
                a0=MV2.concatenate((a0,tmp))
            a0=MV2.sort(a0,0).filled()
            real2=real.filled()
            a0=MV2.reshape(a0,(a0.shape[0],sh[1]*sh[2]))
            real2=MV2.reshape(real2,(sh[1]*sh[2],))
            a0=MV2.transpose(a0)
            indices=[]
            for i in range(len(real2)):
                indices.append(MV2.searchsorted(a0[i],real2[i]))
            indices=MV2.array(indices)
            indices=MV2.reshape(indices,(sh[1],sh[2]))
            if not ((real.mask is None) or (real.mask is MV2.nomask)):
                indices=MV2.masked_where(real.mask,indices)
            a=MV2.masked_equal(a0,1.e20)
            a=MV2.count(a,1)
            a=MV2.reshape(a,indices.shape)
            indices=indices/a*100
            setattr(self,d[0],real_value)
            indices.setAxisList(real.getAxisList())
##             print indices.shape
            return indices
        else:
            return self.__get()
            
    def __get(self):
        nfree=0
        names=[]
        for p in self.parameters_list:
            if not p in self.dummies and not p in self.auto_dummies:
                v=getattr(self,p)
                if     v is None \
                       or \
                       (isinstance(v,(list,tuple)) and len(v)>1):
                    already=0
                    for pn in names:
                        if p==pn :
                            already=1
                        elif isinstance(pn,list):
                            if p in pn: already=1
                    if already==0:
                        nfree+=1
                        added=0
                        for g in self.grouped:
                            if p in g:
                                names.append(g)
                                added=1
                        if added==0:
                            names.append(p)

        if nfree!=2: raise 'Error MUST end up with 2 multiple values ! (we have '+str(nfree)+':'+str(names)+')'
        # Now determines length of each axis
        axes_length=[1,1]
        # First make sure with have 2 list of parameters
        for i in range(2):
            if not isinstance(names[i],list):
                names[i]=[names[i]]
            for n in names[i]:
                v=getattr(self,n)
                if v is None:
                    if n == 'component' :
                        axes_length[i]*=28
                    elif n == 'time_domain':
                        axes_length[i]*=19
                    else:
                        raise 'Error, '+n+' is not defined correctly, please specify which values you wish to extract'
                else:
                    axes_length[i]*=len(v)
        # Creates the dummy array
        output=MV2.ones((axes_length[0],axes_length[1]))
        # Now mask everywhere
        output=MV2.masked_equal(output,1)
        # Indices for filling
        i=0
        j=0
        # First creates the filler object and sets all the fixed values !
        F=StringConstructor(self.files_structure)
        # Ok let's fill it
        for p in self.parameters_list:
            if not p in self.dummies and not p in self.auto_dummies:
                v=getattr(self,p)
                if isinstance(v,(list,tuple)):
                    if len(v)==1:
                        v=v[0]
                        if p in self.slaves.keys():
                            vslvs=v[1:]
                            v=v[0]
                        setattr(F,p,v)
                        if p in self.slaves.keys():
                            slvs=self.slaves[p]
                            for js in range(len(slvs)):
                                s=slsvs[js]
                                setattr(F,s,vslvs[js])
                    else:
                        setattr(F,p,'*')
                else:
                    if p in self.slaves.keys():
                        vslvs=v[1:]
                        v=v[0]
                    setattr(F,p,v)
                    if p in self.slaves.keys():
                        slvs=self.slaves[p]
                        for js in range(len(slvs)):
                            s=slsvs[js]
                            setattr(F,s,vslvs[js])
            else:
                setattr(F,p,'*')
        
        #fnms=F()
        nms=names[0]+names[1]

        t1,t2,t3=self.string_construct(nms)
        output=output.ravel()
        sp1=t1.split()
        n=len(sp1)
        for i in range(len(t2)):
            sp2=t2[i].split()
            for j in range(n):
                v=sp2[j]
                if sp1[j]=='time_domain':
                    try:
                        v=int(v)
                    except:
                        pass
                if v == 'NONE':
                    v=''
                setattr(F,sp1[j],v)
            #print 'Search string is:',fnms
            #f=os.popen('ls '+F()).readlines()
            #ip,op,ep=os.popen3('ls '+F())
            if self.verbose : print 'command line:',F()
            #f=op.readlines()
            f=glob.glob(F())
            #print 'F is:',f
            files=[]
            for file in f:
                files.append(file)
                for e in self.exclude:
                    if file.find(e)>-1:
                        files.pop(-1)
                        break
            if self.verbose : print 'files:',files
            try:
                # now we get the one value needed in this file
                f=cdms2.open(files[0])
                V=f[F.statistic]
                component=F.component
                time_domain=F.time_domain
                if isinstance(component,str):
                    dic=eval(f.components)
                    for k in dic.keys():
                        if dic[k]==F.component:
                            component=k
                if isinstance(F.time_domain,str):
                    dic=eval(f.time_domain)
                    for k in dic.keys():
                        if dic[k]==F.time_domain:
                            time_domain=k
                value=V(time_domain=time_domain,component=component,squeeze=1)
                output[i]=value
                # In case sometihng goes wrong (like modle not processed or inexsitant for this var, etc...)
                f.close()
            except Exception,err:
                #print 'Error:',err
                pass
        output=MV2.reshape(output,(axes_length[0],axes_length[1]))
        output.id='portrait plot'

        yaxis=self.makeaxis(names[0],axes_length[0])
        xaxis=self.makeaxis(names[1],axes_length[1])
        output.setAxis(0,yaxis)
        output.setAxis(1,xaxis)
        
        # Makes the dim with the most element on the X axis
        if axes_length[0]>axes_length[1]: output=MV2.transpose(output)

        return output
            
    def decorate(self,output,ynm=None,xnm=None):
        x=cdms2.createAxis(range(len(xnm)))
        y=cdms2.createAxis(range(len(ynm)))
        
        try:
            del(x.name)
            del(y.name)
            del(out.name)
        except:
            pass

        nm='___'.join(xnm)
        x.id=nm
        dic={}
        for i in range(len(xnm)):
            dic[i]=xnm[i]
        x.names=repr(dic)
        nm='___'.join(ynm)
        y.id=nm
        output.setAxis(0,y)
        dic={}
        for i in range(len(ynm)):
            dic[i]=ynm[i]
        y.names=repr(dic)
        output.setAxis(1,x)
        
        return

    def plot(self,data=None,mesh=None,template=None,meshfill=None,x=None,bg=0,multiple=1.1):
        # Create the vcs canvas
        if x is None:
            x=vcs.init()

        ## Continents bug
        x.setcontinentstype(0)
        # gets the thing to plot !
        if data is None:
            data=self.get()
        

        # Do we use a predefined template ?
        if template is None:
            template=x.createtemplate()
            # Now sets all the things for the template...
            # Sets a bunch of template attributes to off
            for att in [
                'line1','line2','line3','line4',
                'box2','box3','box4',
                'min','max','mean',
                'xtic1','xtic2',
                'ytic1','ytic2',
                'xvalue','yvalue','zvalue','tvalue',
                'xunits','yunits','zunits','tunits',
                'source','title','dataname',
                ]:
                a=getattr(template,att)
                setattr(a,'priority',0)
            for att in [
                'xname','yname',
                ]:
                a=getattr(template,att)
                setattr(a,'priority',0)
            
            template.data.x1=self.PLOT_SETTINGS.x1
            template.data.x2=self.PLOT_SETTINGS.x2
            template.data.y1=self.PLOT_SETTINGS.y1
            template.data.y2=self.PLOT_SETTINGS.y2
            template.box1.x1=self.PLOT_SETTINGS.x1
            template.box1.x2=self.PLOT_SETTINGS.x2
            template.box1.y1=self.PLOT_SETTINGS.y1
            template.box1.y2=self.PLOT_SETTINGS.y2
            template.xname.y=self.PLOT_SETTINGS.y2+.02
            template.yname.x=self.PLOT_SETTINGS.x2+.01
            template.xlabel1.y=self.PLOT_SETTINGS.y1
            template.xlabel2.y=self.PLOT_SETTINGS.y2
            template.xlabel1.texttable=self.PLOT_SETTINGS.tictable
            template.xlabel2.texttable=self.PLOT_SETTINGS.tictable
            template.xlabel1.textorientation=self.PLOT_SETTINGS.xticorientation
            template.xlabel2.textorientation=self.PLOT_SETTINGS.xticorientation
            template.ylabel1.x=self.PLOT_SETTINGS.x1
            template.ylabel2.x=self.PLOT_SETTINGS.x2
            template.ylabel1.texttable=self.PLOT_SETTINGS.tictable
            template.ylabel2.texttable=self.PLOT_SETTINGS.tictable
            template.ylabel1.textorientation=self.PLOT_SETTINGS.yticorientation
            template.ylabel2.textorientation=self.PLOT_SETTINGS.yticorientation
            
            if self.PLOT_SETTINGS.xtic1y1 is not None:
                template.xtic1.y1=self.PLOT_SETTINGS.xtic1y1
                template.xtic1.priority=1
            if self.PLOT_SETTINGS.xtic1y2 is not None:
                template.xtic1.y2=self.PLOT_SETTINGS.xtic1y2
                template.xtic1.priority=1
            if self.PLOT_SETTINGS.xtic2y1 is not None:
                template.xtic2.y1=self.PLOT_SETTINGS.xtic2y1
                template.xtic2.priority=1
            if self.PLOT_SETTINGS.xtic2y2 is not None:
                template.xtic2.y2=self.PLOT_SETTINGS.xtic2y2
                template.xtic2.priority=1
            if self.PLOT_SETTINGS.ytic1x1 is not None:
                template.ytic1.x1=self.PLOT_SETTINGS.ytic1x1
                template.ytic1.priority=1
            if self.PLOT_SETTINGS.ytic1x2 is not None:
                template.ytic1.x2=self.PLOT_SETTINGS.ytic1x2
                template.ytic1.priority=1
            if self.PLOT_SETTINGS.ytic2x1 is not None:
                template.ytic2.priority=1
                template.ytic2.x1=self.PLOT_SETTINGS.ytic2x1
            if self.PLOT_SETTINGS.ytic2x2 is not None:
                template.ytic2.priority=1
                template.ytic2.x2=self.PLOT_SETTINGS.ytic2x2
            template.legend.x1=self.PLOT_SETTINGS.legend_x1
            template.legend.x2=self.PLOT_SETTINGS.legend_x2
            template.legend.y1=self.PLOT_SETTINGS.legend_y1
            template.legend.y2=self.PLOT_SETTINGS.legend_y2
            try:
             tmp = x.createtextorientation('crap22')
            except:
              tmp = x.gettextorientation('crap22')
            tmp.height = 12
            #tmp.halign = 'center' 
#           template.legend.texttable = tmp
            template.legend.textorientation = tmp
 
        else:
            if isinstance(template,vcs.template.P):
                tid=template.name
            elif isinstance(template,str):
                tid=template
            else:
                raise 'Error cannot understand what you mean by template='+str(template)
        
            template=x.createtemplate()

        # Do we use a predefined meshfill ?
        if meshfill is None:
            mtics={}
            for i in range(100):
                mtics[i-.5]=''
            icont = 1
            meshfill=x.createmeshfill()
            meshfill.xticlabels1=eval(data.getAxis(1).names)
            meshfill.yticlabels1=eval(data.getAxis(0).names)
            
            meshfill.datawc_x1=-.5
            meshfill.datawc_x2=data.shape[1]-.5
            meshfill.datawc_y1=-.5
            meshfill.datawc_y2=data.shape[0]-.5
            meshfill.mesh=self.PLOT_SETTINGS.draw_mesh
            meshfill.missing=self.PLOT_SETTINGS.missing_color
            meshfill.xticlabels2=mtics
            meshfill.yticlabels2=mtics
            if self.PLOT_SETTINGS.colormap is None:
                self.set_colormap(x)
            elif x.getcolormapname()!=self.PLOT_SETTINGS.colormap:
                x.setcolormap(self.PLOT_SETTINGS.colormap)
            
            if self.PLOT_SETTINGS.levels is None:
                min,max=vcs.minmax(data)
                if max!=0: max=max+.000001
                levs=vcs.mkscale(min,max)
            else:
                levs=self.PLOT_SETTINGS.levels

            if len(levs)>1:
                meshfill.levels=levs
                if self.PLOT_SETTINGS.fillareacolors is None:
                    cols=vcs.getcolors(levs,range(16,40),split=1)
                    meshfill.fillareacolors=cols
                else:
                    meshfill.fillareacolors=self.PLOT_SETTINGS.fillareacolors
            
##             self.setmeshfill(x,meshfill,levs)
##             if self.PLOT_SETTINGS.legend is None:
##                 meshfill.legend=vcs.mklabels(levs)
##             else:
##                 meshfill.legend=self.PLOT_SETTINGS.legend
            # Now creates the mesh associated
            n=int(multiple)
            ntot=int((multiple-n)*10+.1)
##             data=data
            sh=list(data.shape)
            sh.append(2)
            I=MV2.indices((sh[0],sh[1]))
            Y=I[0]
            X=I[1]
##             if ntot>1:
##                 meshfill.mesh='y'
            if ntot == 1:
                sh.append(4)
                M=MV2.zeros(sh)
                M[:,:,0,0]=Y-.5
                M[:,:,1,0]=X-.5
                M[:,:,0,1]=Y-.5
                M[:,:,1,1]=X+.5
                M[:,:,0,2]=Y+.5
                M[:,:,1,2]=X+.5
                M[:,:,0,3]=Y+.5
                M[:,:,1,3]=X-.5
                M=MV2.reshape(M,(sh[0]*sh[1],2,4))
            elif ntot==2:
                sh.append(3)
                M=MV2.zeros(sh)
                M[:,:,0,0]=Y-.5
                M[:,:,1,0]=X-.5
                M[:,:,0,1]=Y+.5-(n-1)
                M[:,:,1,1]=X-0.5+(n-1)
                M[:,:,0,2]=Y+.5
                M[:,:,1,2]=X+.5
                M=MV2.reshape(M,(sh[0]*sh[1],2,3))
            elif ntot==3:
                design=int((multiple-n)*100+.1)
                if design==33:
                    sh.append(3)
                    M=MV2.zeros(sh)
                    if n==1:
                        M[:,:,0,0]=Y-.5
                        M[:,:,1,0]=X-.5
                        M[:,:,0,1]=Y+.5
                        M[:,:,1,1]=X
                        M[:,:,0,2]=Y+.5
                        M[:,:,1,2]=X-.5
                    elif n==2:
                        M[:,:,0,0]=Y-.5
                        M[:,:,1,0]=X-.5
                        M[:,:,0,1]=Y+.5
                        M[:,:,1,1]=X
                        M[:,:,0,2]=Y-.5
                        M[:,:,1,2]=X+.5
                    elif n==3:
                        M[:,:,0,0]=Y+.5
                        M[:,:,1,0]=X+.5
                        M[:,:,0,1]=Y+.5
                        M[:,:,1,1]=X
                        M[:,:,0,2]=Y-.5
                        M[:,:,1,2]=X+.5
                    M=MV2.reshape(M,(sh[0]*sh[1],2,3))
                elif design==32:
                    sh.append(5)
                    M=MV2.zeros(sh)
                    M[:,:,0,0]=Y
                    M[:,:,1,0]=X
                    d=.5/MV2.sqrt(3.)
                    if n==1:
                        M[:,:,0,1]=Y+.5
                        M[:,:,1,1]=X
                        M[:,:,0,2]=Y+.5
                        M[:,:,1,2]=X-.5
                        M[:,:,0,3]=Y-d
                        M[:,:,1,3]=X-.5
                        # dummy point for n==1 or 3
                        M[:,:,0,4]=Y
                        M[:,:,1,4]=X
                    if n==2:
                        M[:,:,0,1]=Y-d
                        M[:,:,1,1]=X-.5
                        M[:,:,0,2]=Y-.5
                        M[:,:,1,2]=X-.5
                        M[:,:,0,3]=Y-.5
                        M[:,:,1,3]=X+.5
                        M[:,:,0,4]=Y-d
                        M[:,:,1,4]=X+.5
                    elif n==3:
                        M[:,:,0,1]=Y+.5
                        M[:,:,1,1]=X
                        M[:,:,0,2]=Y+.5
                        M[:,:,1,2]=X+.5
                        M[:,:,0,3]=Y-d
                        M[:,:,1,3]=X+.5
                        # dummy point for n==1 or 3
                        M[:,:,0,4]=Y
                        M[:,:,1,4]=X
                    M=MV2.reshape(M,(sh[0]*sh[1],2,5))
                else:
                    sh.append(5)
                    M=MV2.zeros(sh)
                    M[:,:,0,0]=Y
                    M[:,:,1,0]=X
                    d=1./3.
                    if n==1:
                        M[:,:,0,1]=Y+.5
                        M[:,:,1,1]=X
                        M[:,:,0,2]=Y+.5
                        M[:,:,1,2]=X-.5
                        M[:,:,0,3]=Y-d
                        
                        M[:,:,1,3]=X-.5
                        # dummy point for n==1 or 3
                        M[:,:,0,4]=Y
                        M[:,:,1,4]=X
                    if n==2:
                        M[:,:,0,1]=Y-d
                        M[:,:,1,1]=X-.5
                        M[:,:,0,2]=Y-.5
                        M[:,:,1,2]=X-.5
                        M[:,:,0,3]=Y-.5
                        M[:,:,1,3]=X+.5
                        M[:,:,0,4]=Y-d
                        M[:,:,1,4]=X+.5
                    elif n==3:
                        M[:,:,0,1]=Y+.5
                        M[:,:,1,1]=X
                        M[:,:,0,2]=Y+.5
                        M[:,:,1,2]=X+.5
                        M[:,:,0,3]=Y-d
                        M[:,:,1,3]=X+.5
                        # dummy point for n==1 or 3
                        M[:,:,0,4]=Y
                        M[:,:,1,4]=X                        
                    M=MV2.reshape(M,(sh[0]*sh[1],2,5))
            elif ntot==4:
                sh.append(3)
                M=MV2.zeros(sh)
                M[:,:,0,0]=Y
                M[:,:,1,0]=X
                if n==1:
                    M[:,:,0,1]=Y+.5
                    M[:,:,1,1]=X+.5
                    M[:,:,0,2]=Y+.5
                    M[:,:,1,2]=X-.5
                elif n==2:
                    M[:,:,0,1]=Y+.5
                    M[:,:,1,1]=X-.5
                    M[:,:,0,2]=Y-.5
                    M[:,:,1,2]=X-.5
                elif n==3:
                    M[:,:,0,1]=Y-.5
                    M[:,:,1,1]=X-.5
                    M[:,:,0,2]=Y-.5
                    M[:,:,1,2]=X+.5
                elif n==4:
                    M[:,:,0,1]=Y-.5
                    M[:,:,1,1]=X+.5
                    M[:,:,0,2]=Y+.5
                    M[:,:,1,2]=X+.5
                M=MV2.reshape(M,(sh[0]*sh[1],2,3))
        else:
            if isinstance(meshfill,vcs.meshfill.P):
                tid=mesh.id
            elif isinstance(meshfill,str):
                tid=mesh
            else:
                raise 'Error cannot understand what you mean by meshfill='+str(meshfill)
            meshfill=x.createmeshfill()

        if mesh is None:
            x.plot(MV2.ravel(data),M,template,meshfill,bg=bg)
        else:
            x.plot(MV2.ravel(data),mesh,template,meshfill,bg=bg)
            

        # Now prints the rest of the title, etc...
        # but only if n==1
        if n==1:
            axes_param=[]
            for a in data.getAxis(0).id.split('___'):
                axes_param.append(a)
            for a in data.getAxis(1).id.split('___'):
                axes_param.append(a)
            nparam=0
            for p in self.parameters_list:
                if not p in self.dummies and not p in self.auto_dummies and not p in axes_param:
                    nparam+=1
                    
            if self.verbose: print 'NPARAM:',nparam
            if nparam>0:
                for i in range(nparam):
                    j=MV2.ceil(float(nparam)/(i+1.))
                    if j<=i:
                        break
                npc=i # number of lines
                npl=int(j) # number of coulmns
                if npc*npl<nparam :
                    npl+=1
                # computes space between each line
                dl=(.95-template.data.y2)/npl
                dc=.9/npc
                npci=0 # counter for columns
                npli=0 # counter for lines
                for p in self.parameters_list:
                    if not p in self.dummies and not p in self.auto_dummies and not p in axes_param:
                        txt=x.createtext(None,self.PLOT_SETTINGS.parametertable.name,None,self.PLOT_SETTINGS.parameterorientation.name)
                        value=getattr(self,p)
                        if (isinstance(value,(list,tuple)) and len(value)==1):
                            txt.string=p+':'+str(self.makestring(p,value[0]))
                            display=1
                        elif isinstance(value,(str,int,float,long)):
                            txt.string=p+':'+str(self.makestring(p,value))
                            display=1
                        else:
                            display=0

                        if display:
                            # Now figures out where to put these...
                            txt.x=[(npci)*dc+dc/2.+.05]
                            txt.y=[1.-(npli)*dl-dl/2.]
                            npci+=1
                            if npci>=npc:
                                npci=0
                                npli+=1
                            if p in self.altered.keys():
                                dic=self.altered[p]
                                if dic['size'] is not None:
                                    txt.size=dic['size']
                                if dic['color'] is not None:
                                    txt.color=dic['color']
                                if dic['x'] is not none:
                                    txt.x=dic['x']
                                if dic['y'] is not none:
                                    txt.y=dic['y']
                            x.plot(txt,bg=bg,continents=0)
            if not self.PLOT_SETTINGS.logo is None:
                x.plot(self.PLOT_SETTINGS.logo,bg=bg,continents=0)
            if not self.PLOT_SETTINGS.time_stamp is None:
                import time
                sp=time.ctime().split()
                sp=sp[:3]+[sp[-1]]
                self.PLOT_SETTINGS.time_stamp.string=''.join(sp)
                x.plot(self.PLOT_SETTINGS.time_stamp,bg=bg,continents=0)

    def set_colormap(self,x):
        cols=(100,100,100,   0,0,0,   83.9216,83.9216,83.9216,   30.9804,30.9804,30.9804,   100,100,100,   100,100,0,        0,2.7451,100,   0,5.4902,100,   0,7.84314,100,   0,10.9804,100,   0,13.7255,100,   0,16.4706,100,         0,20.3922,100,   0,23.1373,100,   0,25.4902,100,   0,30.1961,100,   0,0,47.451,   10.5882,13.3333,54.5098,         21.5686,27.0588,61.5686,   32.549,40.7843,68.6274,   43.5294,54.5098,76.0784,   48.6275,60.7843,79.2157,   53.7255,67.451,82.7451,   58.8235,73.7255,86.2745,         64.3137,80.3922,89.4118,   69.4118,86.6667,92.9412,   74.5098,93.3333,96.4706,   80,100,100,   100,87.0588,85.098,   100,69.4118,67.8431,         100,52.1569,50.9804,   100,34.5098,33.7255,   100,17.2549,16.8627,   100,0,0,   87.451,0,0,   74.902,0,0,        62.7451,0,0,   50.1961,0,0,   37.6471,0,0,   25.4902,0,0,   100,100,100,   0,0,47.451,        0.392157,0.392157,47.451,   0.784314,0.784314,47.8431,   1.17647,1.17647,48.2353,   1.56863,1.56863,48.2353,   1.96078,1.96078,48.6275,   2.35294,2.7451,49.0196,        2.7451,3.13725,49.0196,   3.13725,3.52941,49.4118,   3.52941,3.92157,49.8039,   3.92157,4.31373,49.8039,   4.31373,5.09804,50.1961,   4.70588,5.4902,50.5882,        5.09804,5.88235,50.5882,   5.4902,6.27451,50.9804,   5.88235,6.66667,51.3725,   6.27451,7.45098,51.3725,   6.66667,7.84314,51.7647,   7.05882,8.23529,52.1569,        7.45098,8.62745,52.1569,   7.84314,9.01961,52.549,   8.23529,9.80392,52.9412,   8.62745,10.1961,52.9412,   9.01961,10.5882,53.3333,   9.41177,10.9804,53.7255,        9.80392,11.3725,53.7255,   10.1961,12.1569,54.1176,   10.5882,12.549,54.5098,   10.9804,12.9412,54.5098,   11.3725,13.3333,54.902,   11.7647,13.7255,55.2941,        12.1569,14.5098,55.2941,   12.549,14.902,55.6863,   13.3333,15.2941,56.0784,   13.7255,15.6863,56.4706,   14.1176,16.0784,56.4706,   14.5098,16.8627,56.8627,        14.902,17.2549,57.2549,   15.2941,17.6471,57.2549,   15.6863,18.0392,57.6471,   16.0784,18.4314,58.0392,   16.4706,19.2157,58.0392,   16.8627,19.6078,58.4314,        17.2549,20,58.8235,   17.6471,20.3922,58.8235,   18.0392,20.7843,59.2157,   18.4314,21.5686,59.6078,   18.8235,21.9608,59.6078,   19.2157,22.3529,60,        19.6078,22.7451,60.3922,   20,23.1373,60.3922,   20.3922,23.9216,60.7843,   20.7843,24.3137,61.1765,   21.1765,24.7059,61.1765,   21.5686,25.098,61.5686,        21.9608,25.4902,61.9608,   22.3529,26.2745,61.9608,   22.7451,26.6667,62.3529,   23.1373,27.0588,62.7451,   23.5294,27.451,62.7451,   23.9216,27.8431,63.1373,        24.3137,28.6275,63.5294,   24.7059,29.0196,63.5294,   25.098,29.4118,63.9216,   25.4902,29.8039,64.3137,   25.8824,30.1961,64.3137,   26.6667,30.9804,64.7059,        27.0588,31.3725,65.098,   27.451,31.7647,65.4902,   27.8431,32.1569,65.4902,   28.2353,32.549,65.8824,   28.6275,32.9412,66.2745,   29.0196,33.7255,66.2745,        29.4118,34.1176,66.6667,   29.8039,34.5098,67.0588,   30.1961,34.902,67.0588,   30.5882,35.2941,67.451,   30.9804,36.0784,67.8431,   31.3725,36.4706,67.8431,        31.7647,36.8627,68.2353,   32.1569,37.2549,68.6274,   32.549,37.6471,68.6274,   32.9412,38.4314,69.0196,   33.3333,38.8235,69.4118,   33.7255,39.2157,69.4118,        34.1176,39.6078,69.8039,   34.5098,40,70.1961,   34.902,40.7843,70.1961,   35.2941,41.1765,70.5882,   35.6863,41.5686,70.9804,   36.0784,41.9608,70.9804,        36.4706,42.3529,71.3726,   36.8627,43.1373,71.7647,   37.2549,43.5294,71.7647,   37.6471,43.9216,72.1569,   38.0392,44.3137,72.549,   38.4314,44.7059,72.549,        38.8235,45.4902,72.9412,   39.2157,45.8824,73.3333,   40,46.2745,73.7255,   40.3922,46.6667,73.7255,   40.7843,47.0588,74.1176,   41.1765,47.8431,74.5098,        41.5686,48.2353,74.5098,   41.9608,48.6275,74.902,   42.3529,49.0196,75.2941,   42.7451,49.4118,75.2941,   43.1373,50.1961,75.6863,   43.5294,50.5882,76.0784,        43.9216,50.9804,76.0784,   44.3137,51.3725,76.4706,   44.7059,51.7647,76.8627,   45.098,52.549,76.8627,   45.4902,52.9412,77.2549,   45.8824,53.3333,77.6471,        46.2745,53.7255,77.6471,   46.6667,54.1176,78.0392,   47.0588,54.902,78.4314,   47.451,55.2941,78.4314,   47.8431,55.6863,78.8235,   48.2353,56.0784,79.2157,        48.6275,56.4706,79.2157,   49.0196,57.2549,79.6078,   49.4118,57.6471,80,   49.8039,58.0392,80,   50.1961,58.4314,80.3922,   50.5882,58.8235,80.7843,        50.9804,59.6078,80.7843,   51.3725,60,81.1765,   51.7647,60.3922,81.5686,   52.1569,60.7843,81.5686,   52.549,61.1765,81.9608,   53.3333,61.9608,82.3529,        53.7255,62.3529,82.7451,   54.1176,62.7451,82.7451,   54.5098,63.1373,83.1373,   54.902,63.5294,83.5294,   55.2941,63.9216,83.5294,   55.6863,64.7059,83.9216,        56.0784,65.098,84.3137,   56.4706,65.4902,84.3137,   56.8627,65.8824,84.7059,   57.2549,66.2745,85.098,   57.6471,67.0588,85.098,   58.0392,67.451,85.4902,        58.4314,67.8431,85.8824,   58.8235,68.2353,85.8824,   59.2157,68.6274,86.2745,   59.6078,69.4118,86.6667,   60,69.8039,86.6667,   60.3922,70.1961,87.0588,        60.7843,70.5882,87.451,   61.1765,70.9804,87.451,   61.5686,71.7647,87.8431,   61.9608,72.1569,88.2353,   62.3529,72.549,88.2353,   62.7451,72.9412,88.6274,        63.1373,73.3333,89.0196,   63.5294,74.1176,89.0196,   63.9216,74.5098,89.4118,   64.3137,74.902,89.8039,   64.7059,75.2941,89.8039,   65.098,75.6863,90.1961,        65.4902,76.4706,90.5882,   65.8824,76.8627,90.5882,   66.6667,77.2549,90.9804,   67.0588,77.6471,91.3726,   67.451,78.0392,91.7647,   67.8431,78.8235,91.7647,        68.2353,79.2157,92.1569,   68.6274,79.6078,92.549,   69.0196,80,92.549,   69.4118,80.3922,92.9412,   69.8039,81.1765,93.3333,   70.1961,81.5686,93.3333,        70.5882,81.9608,93.7255,   70.9804,82.3529,94.1176,   71.3726,82.7451,94.1176,   71.7647,83.5294,94.5098,   72.1569,83.9216,94.902,   72.549,84.3137,94.902,        72.9412,84.7059,95.2941,   73.3333,85.098,95.6863,   73.7255,85.8824,95.6863,   74.1176,86.2745,96.0784,   74.5098,86.6667,96.4706,   74.902,87.0588,96.4706,        75.2941,87.451,96.8627,   75.6863,88.2353,97.2549,   76.0784,88.6274,97.2549,   76.4706,89.0196,97.6471,   76.8627,89.4118,98.0392,   77.2549,89.8039,98.0392,        77.6471,90.5882,98.4314,   78.0392,90.9804,98.8235,   78.4314,91.3726,98.8235,   78.8235,91.7647,99.2157,   79.2157,92.1569,99.6078,   80,92.9412,100)

        cols=MV2.reshape(cols,(len(cols)/3,3))

        for i in range(cols.shape[0]):
            co=x.getcolorcell(i)
            if (co[0]!=int(cols[i][0]) or co[1]!=int(cols[i][1]) or co[2]!=int(cols[i][2])):
                x.setcolorcell(i,int(cols[i][0]),int(cols[i][1]),int(cols[i][2]))
        pass
    
