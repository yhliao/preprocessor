import sys
import re
from preprocessor.parse_specs import parse_specfile
from datetime import datetime
import subprocess

## Helper function to replace @key@ in template string with values of
def replace_spec(inputstr,Key,Value):
   outputstr = inputstr
   for key,value in zip(Key,Value):
      toreplace = "@{}@".format(key)
      outputstr = outputstr.replace(toreplace,value)
   return outputstr

class preprocessor:

   def __init__(self,templatefile,specfile):
      self.blocks = {}
      self.update_spec(specfile)
      self.update_template(templatefile)

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
         parse_specfile(sf,self.blocks)

         ## For logging the changes
         diffP = subprocess.Popen(["diff",sf,sf + ".bkup"],
                                  stdout=subprocess.PIPE,stderr=subprocess.PIPE)
         (stdout, stderr) = diffP.communicate() 
         with open("../simlog.log","a+") as simlog:
            simlog.write("{0} {1} parsed and preprocessed...\n".format
                         (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),sf))
            simlog.write(stdout.decode('utf-8'))
         print(stderr)

         subprocess.call(["cp","-f",sf,sf + ".bkup"])

   def filter_entry(self,sec_name,key,keep_regex):
      filtered_block = self.blocks[sec_name].\
                          set_index(key).\
                          filter(regex=keep_regex, axis=0)

      self.blocks[sec_name] = filtered_block.reset_index()

   def inner_join(self,origblock,otherblock,on):
      df_origin = self.blocks[origblock]
      df_other  = self.blocks[otherblock].set_index(on)
      df_joined = df_origin.join(df_other,on=on,how='inner')
      self.blocks[origblock] = df_joined
      
   def create_group(self,sec_names,nametemplate):

      def spec_traverse_next(spec_key,sec_names,value,level):
         if level == len(sec_names):
            assert len(value) == len(spec_key)

            ## Build the namedict at the leaves and output a file
            namedict = dict(zip(spec_key,value))
            ofname = nametemplate.format(**namedict)
            print ("Writing file",ofname)
            with open(ofname,"w") as of:
               outputstr = replace_spec(self.template,
                                        spec_key,value)
               of.write(outputstr)
               of.close()
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

   def get_values(self,sec_names,key):
      array = []
      for name in sec_names:
         value = self.blocks[name][key].tolist()
         array += value
      return array

