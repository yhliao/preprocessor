import sys, os, errno
import re
from preprocessor.parse_specs import parse_specfile
from datetime import datetime
import subprocess

class preprocessor:

   def __init__(self,templatefile,specfile,verbose=True):
      self.blocks = {}
      self.verbose = verbose
      self.update_spec(specfile)
      self.template = ""
      if templatefile==[] and verbose:
         print ("preprocessor: template file not specified when initializing")
      else:
         self.update_template(templatefile)
      self.logflag = False

   def update_template(self,templatefile):
      if type(templatefile) is str:
         self.template = open(templatefile,"r").read()
      else:
         self.template = ""
         for tf in templatefile:
            self.template += open(tf,"r").read()

   def update_spec(self,specfile):
      if type(specfile) is str:
         specfile = [specfile]

      for sf in specfile:
         ## self.blocks = { blocknames: DataFrames_from_block }
         parse_specfile(sf,self.blocks,self.verbose)

         ## For logging the changes
         diffP = subprocess.Popen(["diff",sf,sf + ".bkup"],
                                  stdout=subprocess.PIPE,stderr=subprocess.PIPE)
         (stdout, stderr) = diffP.communicate() 
         with open("../simlog.log","a+") as simlog:
            simlog.write("{0} {1} parsed and preprocessed...\n".format
                         (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),sf))
            simlog.write(stdout.decode('utf-8'))

         subprocess.call(["cp","-f",sf,sf + ".bkup"])

   def filter_entry(self,sec_name,key,keep_regex):
      filtered_block = self.blocks[sec_name].\
                          set_index(key).\
                          filter(regex=keep_regex, axis=0)

      self.blocks[sec_name] = filtered_block.reset_index()

   def inner_join(self,origblock,otherblock,on,verbose=False):
      df_origin = self.blocks[origblock]
      df_other  = self.blocks[otherblock].set_index(on)
      df_joined = df_origin.join(df_other,on=on,how='inner')
      if verbose:
         print ("Joined", origblock, ':')
         print (df_joined)
      self.blocks[origblock] = df_joined
      
   def _traverse_group_tree(self,sec_names,func,*args):
      def spec_traverse_next(spec_key,sec_names,value,level):
         if level == len(sec_names):
            assert len(value) == len(spec_key)
            ## Build the namedict at the leaves
            namedict = dict(zip(spec_key,value))
            func(namedict,*args)
         elif level >= 0:
            ## Recursion through the blocks tree to 
            ## build complete namedict 
            for spec in self.blocks[sec_names[level]].iterrows():
               rowvalue = spec[1].to_list()

               spec_traverse_next(spec_key,sec_names,
                                  value+rowvalue,level+1)
         else:
            raise AssertionError

      spec_key = []
      for name in sec_names:
         spec_key += self.blocks[name].columns.tolist()

      spec_traverse_next(spec_key,sec_names,[],0)

   def log_create(self,logfile,entrytemplate):
      self.logfile = open(logfile,"w")
      self.entrytemplate = entrytemplate
      self.logflag = True
   def log_close(self):
      self.logfile.close()
      self.logflag = False

   def create_group(self,sec_names,nametemplate):
      def _build_file(namedict,nametemplate,verbose):
            ofname = nametemplate.format(**namedict)

            try:
               of=open(ofname,"w")
            except FileNotFoundError:
               dirname = ofname[:ofname.rfind('/')]
               print ("Preprocessor --- Creating Directory", dirname)
               os.makedirs(dirname)
               of=open(ofname,"w")

            outputstr = self.template
            for key,value in namedict.items():
               toreplace = "@{}@".format(key)
               outputstr = outputstr.replace(toreplace,value)
            if verbose:
               print ("Writing file",ofname)
            of.write(outputstr)
            if self.logflag:
               logentry = self.entrytemplate.format(**namedict)
               self.logfile.write(logentry + "\n")
            of.close()

      self._traverse_group_tree(sec_names,_build_file,nametemplate
                               ,self.verbose)
      
   def create_links(self,sec_names,sourcetemplate,desttemplate):

      def _build_link(namedict,sourcetemplate,desttemplate,verbose):
         source_name = sourcetemplate.format(**namedict)
         dest_name   = desttemplate.format(**namedict)

         try:
            os.symlink(source_name,dest_name)
         except FileNotFoundError:
            dirname = dest_name[:dest_name.rfind('/')]
            print ("Preprocessor --- Creating Directory", dirname)
            os.makedirs(dirname)
            os.symlink(source_name,dest_name)
         except FileExistsError:
           os.remove(dest_name)
           os.symlink(source_name,dest_name)
         if verbose:
            print ("Linked {0} -> {1}".format(dest_name,source_name))
      self._traverse_group_tree(sec_names,_build_link,
                                sourcetemplate,desttemplate,
                                self.verbose)

   def get_values(self,sec_names,key):
      array = []
      for name in sec_names:
         value = self.blocks[name][key].tolist()
         array += value
      return array

   def get_specdict(self,sec_names,key,value):
      for sec_name in sec_names:
         targetblock = self.blocks[sec_name]
         matchedrow  = targetblock[targetblock[key]==value]

         if matchedrow.shape[0] != 0:
            return matchedrow.to_dict('records')[0]
