#!/usr/bin/python

import os
import subprocess
import requests
import urllib.request
import tempfile
import json
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import re
from itertools import combinations
from galaxy.util.xml_macros import load

#mothur_commands_folder = "/home/laptop/Galaxy/mothur_analysis/mothur-1.39.5/source/commands"
mothur_commands_folder = "/home/laptop/Galaxy/mothur_analysis/mothur-1.48.0/source/commands"
#mothur_commands_folder = "/home/laptop/Galaxy/tools-iuc/tools/mothur"
#mothur_repo = "https://github.com/galaxyproject/tools-iuc/tree/main/tools/mothur"
#prefix_addr = "https://raw.githubusercontent.com/galaxyproject/tools-iuc/main/tools/mothur/"
xml_folder = "/home/laptop/Galaxy/tools-iuc/tools/mothur"
output_files = "./output_files"

translator = {"f":"false","t":"true","F":"false","T":"true"}

datainput = '<!--param argument="{}" type="data" format="{}" multiple="{}" optional="{}" label="{}"/-->\n'
valueinput = '<!--param argument="{}" type="{}" value="{}" optional="{}" label="{}"/-->\n'
boolinput = '<!--param argument="{}" type="boolean" truevalue="true" falsevalue="false" checked="{}" label="{}"/-->\n'

def dictionary_mothur(path):
    temp_dictionary = {}
    exclude = ["nocommands.cpp","quitcommand.cpp","helpcommand.cpp","newcommandtemplate.cpp","systemcommand.cpp","getcommandinfocommand.cpp"]
    files = [os.path.join(mothur_commands_folder,x) for x in os.listdir(path) if "cpp" in x and x not in exclude]
    raw_outputs = ""
    for i in files:
        rawdata = open(i).readlines()        
        command = [x for x in rawdata if 'helpString += "The' in x][0].strip().split(" ")[3]
        lines = [x for x in rawdata if 'CommandParameter ' in x]
        raw_parameters = [x for x in open(i).readlines() if 'CommandParameter ' in x]
        parameters = {}
        var_types = {"\tint":"integer","\tfloat":"float","\tdouble":"float"}
        for l in raw_parameters:
            index1 = l.index("(")
            index2 = l.index(",")
            option_name = l[index1+1:index2].strip('"')
            index3 = l.index(")")
            options = [x.strip(' \"') for x in  l[index2+2:index3].split(",")]
            options_selector = ""
            option_datatype = []
            if options[0] == 'InputTypes':
                option_type = "data"
                option_datatype = [x for x in list(set(options[3].split("-")+options[4].split("-"))) if x != "none"]
            elif options[0] == "Number":
                if len(option_name) > 3:
                    pattern = "|".join([option_name[x:y] for x, y in combinations(range(len(option_name) + 1), r = 2) if len(option_name[x:y]) >3 ])
                else:
                    pattern = option_name
                rexp = re.compile(r".*{}.*".format(pattern))
                header_file = i.replace("cpp","h")
                if os.path.isfile(header_file):
                    with open(header_file) as tmp:
                        for line in tmp:
                            match = re.findall(rexp,line)
                            if match and line.split(" ")[0] in var_types.keys():
                                option_type = var_types[line.split(" ")[0]]
                                break
                else:
                    option_type = ""
            elif options[0] == "String":  option_type="text"
            elif options[0] == "Boolean": option_type="boolean"
            elif options[0] == "Multiple":
                option_type="select"
                options_selector = options[1].split("-")
            else:
                option_type = ""
            if options[2] in translator.keys():
                option_default = translator[options[2]]
            else:
                option_default = options[2]
            inverse = {"false":"true","true":"false","":""}
            # This needs to be checked
            if len(options) == 10:
                option_optional = inverse[options[9].strip()]
                option_multiple = options[8]
            elif len(options) == 9:
                option_optional = inverse[options[8].strip()]
                option_multiple = options[7]
            elif option_name == "processors":
                option_optional = "true"
                option_multiple = "false"
            #else:
                #print(option_name)
                #raise Exception("[x] Error during paramter parsing")


            if options_selector != "":
                parameters[option_name] = {"type":option_type,
                                           "default":option_default,
                                           "datatype":option_datatype,
                                           "multiple":option_multiple,
                                           "optional":option_optional,
                                           "selector":options_selector
                }
            else:
                parameters[option_name] = {"type":option_type,
                                           "default":option_default,
                                           "datatype":option_datatype,
                                           "multiple":option_multiple,
                                           "optional":option_optional,
                }

        temp_dictionary[command] = parameters
    return(temp_dictionary)
"""              
def get_xml_urls(url):
    reqs = requests.get(url)
    soup = BeautifulSoup(reqs.text, 'html.parser')
    urls = []
    for link in soup.find_all('a'):
        urls.append(link.get('href'))
    filtered = [prefix_addr + x.split("/")[-1] for x in urls if "xml" in x]
    return(filtered)

def download(url, folder):
    filename = url.split("/")[-1]
    output_path = os.path.join(folder,filename)
    with open(output_path, "wb") as file:
        response = requests.get(url)
        file.write(response.content)

def download_xml_wrappers(mothur_repo):
    urls = get_xml_urls(mothur_repo)
    if not os.path.isdir(xml_folder):
        os.makedirs(xml_folder)
        for url in urls:
            download(url,xml_folder)
    files = os.listdir(xml_folder)
    return(files)
"""
def dictionary_galaxy(files):
    temp_dictionary = {}
    for i in range(len(files)):
        command = files[i][:-4]
        xml_file = os.path.join(xml_folder,files[i])
        mytree = load(xml_file)
        myroot = mytree.getroot()
        parameters = {}
        for level in myroot:
            for param in level.findall(".//param"):
                if 'argument' in param.attrib.keys() and 'type' in param.attrib.keys():
                    option_name = param.attrib["argument"]
                    option_type = param.attrib["type"]
                    if option_type == "data":
                        option_datatype = param.attrib["format"].split(",")
                    else:
                        option_datatype = []
                    if 'value' in param.attrib.keys():
                        option_default = param.attrib["value"]
                    else:
                        option_default= ""
                    if 'optional' in param.attrib.keys():
                        option_optional = param.attrib["optional"].capitalize()
                    else:
                        option_optional = "false"
                    if 'multiple' in param.attrib.keys():
                        option_multiple = param.attrib["multiple"].capitalize()
                    else:
                        option_multiple = "false"
                    if option_type == "boolean":
                        if 'checked' in param.attrib.keys():
                            option_default = param.attrib["checked"]
                        else:
                            option_default = ""
                    parameters[option_name] = {"type":option_type,
                                               "default":option_default,
                                               "datatype":option_datatype,
                                               "multiple":option_multiple,
                                               "optional":option_optional}

                elif 'name' in param.attrib.keys() and 'type' in param.attrib.keys():
                    option_name = param.attrib["name"]
                    option_type = param.attrib["type"]
                    if option_type == "data":
                        option_datatype = param.attrib["format"].split(",")
                    else:
                        option_datatype = []
                    if 'value' in param.attrib.keys():
                        option_default = param.attrib["value"]
                    else:
                        option_default= ""
                    if 'optional' in param.attrib.keys():
                        option_optional = param.attrib["optional"].capitalize()
                    else:
                        option_optional = "false"
                    if 'multiple' in param.attrib.keys():
                        option_multiple = param.attrib["multiple"].capitalize()
                    else:
                        option_multiple = "false"
                    if option_type == "boolean":
                        if 'checked' in param.attrib.keys():
                            option_default = param.attrib["checked"]
                    else:
                        option_default = ""
                    parameters[option_name] = {"type":option_type,
                                               "default":option_default,
                                               "datatype":option_datatype,
                                               "multiple":option_multiple,
                                               "optional":option_optional}

        temp_dictionary[command] = parameters
    return(temp_dictionary)
        
def main():
    files = [x for x in os.listdir(xml_folder) if ".xml" in x]
    commands_mothur = dictionary_mothur(mothur_commands_folder)
    #commands_mothur_sorted = json.dumps(commands_mothur,sort_keys=True)
    commands_galaxy = dictionary_galaxy(files)
    #commands_galaxy_sorted = json.dumps(commands_galaxy,sort_keys=True)
    if not os.path.isdir(output_files):
        os.makedirs(output_files)
    out_json_mothur = os.path.join(output_files,"mothur_commands.json")
    out_json_galaxy = os.path.join(output_files,"galaxy_commands.json")
    pprint_cmmd = "cat {} | python -m json.tool > {}"
    with open(out_json_mothur,"w") as out:
        json.dump(commands_mothur,out)
    out_ppjson_mothur = os.path.join(output_files,"mothur_commands_formatted.json")
    subprocess.Popen(pprint_cmmd.format(out_json_mothur,out_ppjson_mothur), shell=True)

    with open(out_json_galaxy,"w") as out:
        json.dump(commands_galaxy,out)
    out_ppjson_galaxy = os.path.join(output_files,"galaxy_commands_formatted.json")
    subprocess.Popen(pprint_cmmd.format(out_json_galaxy,out_ppjson_galaxy), shell=True)
    
    mothur_keys = commands_mothur.keys()
    galaxy_keys = commands_galaxy.keys()
    ## Missing commands:
    missing_commands = mothur_keys - galaxy_keys
    output_missing = os.path.join(output_files,"missing_commands.txt")
    with open(output_missing,"w") as out:
        for i in list(missing_commands): out.write(i+"\n")
    ## Deprecated commands
    deprecated_commands = galaxy_keys - mothur_keys
    output_deprecated = os.path.join(output_files,"deprecated_commands.txt")
    with open(output_deprecated,"w") as out:
        for i in list(deprecated_commands): out.write(i+"\n")
    # Common commands
    common_commands = list(set(galaxy_keys) & set(mothur_keys))
    output_commons = os.path.join(output_files,"common_commands.txt")
    with open(output_commons,"w") as out:
        for i in list(common_commands): out.write(i+"\n")
    
    #Compare paraters
    #################
    missing_parameters = os.path.join(output_files,"missing_parameters.txt")
    default_parameters = os.path.join(output_files,"default_parameters.txt")

    exclude = ["inputdir","outputdir","processors",
               # filenames included under different ids
               ########################################
               "count","name","file", "corraxes", "constaxonomy", "shared", "otucorr", # included with other files
               "ffasta","rfasta","fqfile","rqfile","allfiles", #not used in make.contigs
               "fasta","qfile", "fastq", "phylip","column","oldfasta", # datatype inputs
               "group", "dist", "taxonomy", # included with general name
               "sabund", "repname","relabund", "rabund", "list", # input types, included in single inputs
                "biom", # input included with different name
               # not documented parameters
               ###########################
               "islist", #not documented https://github.com/mothur/mothur/issues/839
               "strand", #not documented  https://github.com/mothur/mothur/issues/839
               "minsmoothid", # commented help in source code https://github.com/mothur/mothur/blob/master/source/commands/chimerauchimecommand.cpp#L95
               "uchimealns", # additionl output file, not necessary
               "shortcuts", #not documented https://github.com/mothur/mothur/issues/839
                "flow", # command not docummented in sortsetcommands.cpp
               "adjust", #not documented https://github.com/mothur/mothur/issues/839
               "timing", #not documented https://github.com/mothur/mothur/issues/839
               "showabund", #not documented https://github.com/mothur/mothur/issues/839
               "ranktec", #commented in source code
               "nlogs", #commented in source code
               "svmnorm", #commented in source code
               "classes", #commented in source code
               "wilcsamename", # commented in source code
               "subject", # commented in source code
               "subclass", # commented in source code
                "random", # not documented in parsimonycommand.cpp
               "map", # not documented in renameseqscommand.cpp
                "ordergroup", # commented in sharedcommand.cpp (make.shared.xml)
               # not required
               ##############
               "output",
                "blastlocation", # not required in Galaxy
                "quiet",
                "stdout",
                "aligned", # hardcoded in seqs.error.xml
                "version",
                "verbose",
                # not included
                ##########
               "compress", #indicate that the output should be compressed
               "alignreport",
               "seed",
               "rseed",
               "subsample", # not used in rarefaction.shared.xml
               "report", "reference", # input types skipped in seq.errors.xml
               "all", #used true by default, collect command splitted in two
               "DNA", # included as option in selector
               "protein", # included as option in selector

    ]

    ## check missing parameters
    ###########################
    with open(missing_parameters,"w") as out:
        counter=0
        for command in sorted(common_commands):
            params_mothur = [x for x in sorted(list(commands_mothur[command].keys())) if x not in exclude]
            params_galaxy = sorted(list(commands_galaxy[command].keys()))
            diff = list(set(params_mothur) - set(params_galaxy))
            if diff:    
                out.write("\n[x] {} Command: {}\n".format(counter,command))
                out.write("[x] Differences: {}\n\n".format(diff))
                for i in diff:
                    if commands_mothur[command][i]["type"] == "data":
                        out.write(datainput.format(i,",".join([x for x in commands_mothur[command][i]["datatype"]]),commands_mothur[command][i]["multiple"],commands_mothur[command][i]["optional"],i))
                    elif commands_mothur[command][i]["type"] == "boolean":
                        out.write(boolinput.format(i,commands_mothur[command][i]["default"],i))
                    elif commands_mothur[command][i]["type"] in ["integer","float"]:
                        out.write(valueinput.format(i,commands_mothur[command][i]["type"],commands_mothur[command][i]["default"],commands_mothur[command][i]["optional"],i))
                counter+=1

    # check default values
    ######################
    with open(default_parameters,"w") as out:
        counter=0
        for i in sorted(common_commands):
            common_parameters =  list(set(commands_galaxy[i].keys()) & set(commands_mothur[i].keys()))
            for j in common_parameters:
                diff_type = commands_galaxy[i][j]["type"] != commands_mothur[i][j]["type"]
                diff_default = commands_galaxy[i][j]["default"] != commands_mothur[i][j]["default"]
                if diff_type or diff_default and commands_galaxy[i][j]["optional"] == "false":
                    out.write("\n\n[-] Command: {}\tParameter: {}".format(i,j))
                    if commands_galaxy[i][j]["type"] != commands_mothur[i][j]["type"]:
                        out.write("\n\t[x] Difference in types")
                        out.write("\n\t\tGalaxy: {}\tMothur: {}".format(commands_galaxy[i][j]["type"],commands_mothur[i][j]["type"]))
                    if commands_galaxy[i][j]["default"] != commands_mothur[i][j]["default"]:
                        out.write("\n\t[x] Difference in default values")
                        out.write("\n\t\tGalaxy: {}\tMothur: {}".format(commands_galaxy[i][j]["default"],commands_mothur[i][j]["default"]))
                    #pass
                #print(commands_mothur[command][i])
                #if commands_mothur[command][i]["type"] == "data":
                #    out.write(datainput.format(i,",".join([x for x in commands_mothur[command][i]["datatype"]]),commands_mothur[command][i]["multiple"],i))
                #elif commands_mothur[command][i]["type"] == "boolean":
                #    out.write(boolinput.format(i,translator[commands_mothur[command][i]["default"]],i))
                #elif commands_mothur[command][i]["type"] in ["integer","float"]:
                #    out.write(valueinput.format(i,commands_mothur[command][i]["type"],commands_mothur[command][i]["default"],commands_mothur[command][i]["optional"],i))
            counter+=1

    # include missing command
    #########################

    counter = 0
    for command in sorted(common_commands):
        outputfile = os.path.join(xml_folder,command+".xml")
        counter+=1
        params_mothur = [x for x in sorted(list(commands_mothur[command].keys())) if x not in exclude]
        params_galaxy = sorted(list(commands_galaxy[command].keys()))
        diff = list(set(params_mothur) - set(params_galaxy))
        if diff:
            toolpath = os.path.join(xml_folder,command+".xml")
            content = (open(toolpath).readlines())
            i1 = [x for x in range(len(content)) if ")'" in content[x]][0]
            for i in range(len(diff)):
                if commands_mothur[command][diff[i]]["type"] not in ["data","boolean","integer","float"]:continue
                commandblock = '##\t,{}=${}\n'.format(diff[i],diff[i])
                content.insert(i1,commandblock)
                i2 = [x for x in range(len(content)) if "</inputs>" in content[x]][0]
                if commands_mothur[command][diff[i]]["type"] == "data":
                    inputblock = datainput.format(diff[i],",".join([x for x in commands_mothur[command][diff[i]]["datatype"]]),commands_mothur[command][diff[i]]["multiple"],commands_mothur[command][diff[i]]["optional"],diff[i])
                    content.insert(i2,"\t\t"+inputblock)
                elif commands_mothur[command][diff[i]]["type"] == "boolean":
                    inputblock = boolinput.format(diff[i],commands_mothur[command][diff[i]]["default"],diff[i])
                    content.insert(i2,"\t\t"+inputblock)
                elif commands_mothur[command][diff[i]]["type"] in ["integer","float"]:
                    inputblock = valueinput.format(diff[i],commands_mothur[command][diff[i]]["type"],commands_mothur[command][diff[i]]["default"],commands_mothur[command][diff[i]]["optional"],diff[i])
                    content.insert(i2,"\t\t"+inputblock)
                
            output = "".join(content)
            open(outputfile,"w").write(output)



if __name__ == "__main__":
    main()

