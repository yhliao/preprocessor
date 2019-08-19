import sys
import re
from preprocessor.parse_specs import parse_specfile
from datetime import datetime
import subprocess

def replace_spec(inputstr,Key,Value):
   outputstr = inputstr
   for key,value in zip(Key,Value):
      toreplace = "@{}@".format(key)
      outputstr = outputstr.replace(toreplace,value)
   return outputstr

class preprocessor:

   def __init__(self,templatefile,specfile):
      self.template = open(templatefile,"r").read()
      self.keys = {}
      self.specs = {}
      self.update_spec(specfile)

   def update_template(self,templatefile):
      self.template = open(templatefile,"r").read()

   def update_spec(self,specfile):
      self.keys.clear()
      self.specs.clear()
      if type(specfile) is str:
         specfile = [specfile]

      for sf in specfile:
         parse_specfile(sf,self.keys,self.specs)
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
      loc_entry = self.keys[sec_name].index(key)
      assert loc_entry >= 0

      speclist = self.specs[sec_name]
      speclist_filtered = []
      for pattern in keep_regex:
         prog = re.compile(pattern)
         speclist_filtered += list(filter(
                                   lambda x: prog.fullmatch(x[loc_entry]),
                                   speclist))
         
      self.specs[sec_name] = speclist_filtered
   
   def create_group(self,sec_names,nametemplate):

      def spec_traverse_next(spec_key,sec_names,value,level):
         if level == len(sec_names):
            assert len(value) == len(spec_key)

            namedict = dict(zip(spec_key,value))
            ofname = nametemplate.format(**namedict)
            print ("Writing file",ofname)
            with open(ofname,"w") as of:
               outputstr = replace_spec(self.template,
                                        spec_key,value)
               of.write(outputstr)
               of.close()
         elif level >= 0:
            for spec in self.specs[sec_names[level]]:
               spec_traverse_next(spec_key,sec_names,
                                  value+spec,level+1)
         else:
            raise AssertionError

      spec_key = []
      for name in sec_names:
         spec_key += self.keys[name]

      spec_traverse_next(spec_key,sec_names,[],0)

   def get_values(self,sec_names,key):
      array = []
      for name in sec_names:
         spec_keys = self.keys[name]
         spec_values = self.specs[name]
         idx = spec_keys.index(key)

         for value in spec_values:
            array.append (value[idx])
      return array

