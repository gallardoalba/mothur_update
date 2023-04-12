#!/usr/bin/python

import os
import subprocess
import requests
import urllib.request
import tempfile
import json
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

mothur_commands_folder = "/home/laptop/Galaxy/mothur_analysis/mothur/source/commands"
mothur_repo = "https://github.com/galaxyproject/tools-iuc/tree/main/tools/mothur"
prefix_addr = "https://raw.githubusercontent.com/galaxyproject/tools-iuc/main/tools/mothur/"
xml_folder ="./mothur_files"
output_files = "./output_files"


def dictionary_mothur(path):
    exclude = ["nocommands.cpp","quitcommand.cpp","helpcommand.cpp","newcommandtemplate.cpp","systemcommand.cpp"]
    files = [os.path.join(mothur_commands_folder,x) for x in os.listdir(path) if "cpp" in x and x not in exclude]
    raw_outputs = ""
    commands = {}
    for i in files:
        rawdata = open(i).readlines()
        function = [x for x in rawdata if 'helpString += "The' in x][0].strip().split(" ")[3]
        lines = [x for x in rawdata if 'CommandParameter ' in x]
        raw_parameters = [x for x in open(i).readlines() if 'CommandParameter ' in x]
        parameters = []
        for l in raw_parameters:
            index1 = l.index("(")
            index2 = l.index(",")
            parameter = l[index1+1:index2].strip('"')
            parameters.append(parameter)
        commands[function]=sorted(parameters)
    return(commands)
              

def parse_html(html):
    elem = BeautifulSoup(html, features="html.parser")
    text = ''
    for e in elem.descendants:
        if isinstance(e, str):
            text += e.strip()
        elif e.name in ['a']:
            text += '\n'
    return text

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

def dictionary_galaxy(files):
    temp_dictionary = {}
    for i in range(len(files)):
        command = files[i][:-4]
        xml_file = os.path.join(xml_folder,files[i])
        mytree = ET.parse(xml_file)
        myroot = mytree.getroot()
        parameters = []
        for level in myroot:
            for param in level.findall(".//param"):
                if 'argument' in param.attrib.keys():
                    parameters.append(param.attrib["argument"])
                elif 'name' in param.attrib.keys():
                    parameters.append(param.attrib["name"])

        temp_dictionary[command] = sorted(parameters)
    return(temp_dictionary)


        
def main():
    files = download_xml_wrappers(mothur_repo)
    commands_mothur = dictionary_mothur(mothur_commands_folder)
    commands_galaxy = dictionary_galaxy(files)
    if not os.path.isdir(output_files):
        os.makedirs(output_files)
    out_json_mothur = os.path.join(output_files,"mothur_commands.json")
    out_json_galaxy = os.path.join(output_files,"galaxy_commands.json")
    with open(out_json_mothur,"w") as out:
        json.dump(commands_mothur,out)
    with open(out_json_galaxy,"w") as out:
        json.dump(commands_galaxy,out)


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


    
if __name__ == "__main__":
    main()
