##############################################################################
#
# Copyright 2016 KPMG Advisory N.V. (unless otherwise stated)
#
# Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
##############################################################################
"""
This wonderful script is going to help me create and test 100 different regular expressions
"""
import re
import  os
import glob
import subprocess

# % TODO: Pick this up from a parameter!
ipa_hostname = 'ambari.kave.io'

ignore_files = ['cacerts', 'jisfreq.py', 'euctwfreq.py',
                'big5freq.py', 'cacert.pem', 'unistring.py']
ignore_dirs = ['/etc/pki/pki-tomcat/ca/archives']
skip_endings = ['so', 'pyc', 'pem', 'cert', 'bin', 'exe', 'sh', 'pyo', 'bak', 'bkp', 'ipabkp']
ignore_matches = ["#ServerName www.example.com:8443"]

comment_in_manually = ["#CONNECTOR_PORT", "# pki_https_port", "# pki_http_port", "#CONNECTOR_PORT"]

ignore_file_matches = {}
match_files = []


start_insecure = '8080'
start_secure = '8443'
pki_insecure_port = '8081'
pki_secure_port = '8444'

sed_searches = {start_insecure:  '[0-9][0-9][0-9][0-9]',
                start_secure:  '[0-9][0-9][0-9][0-9]'}
sed_escapes = '\\/().*[]|'
print sed_escapes
sed_replaces = {start_insecure:  pki_insecure_port, start_secure:  pki_secure_port}

dir_search = ["/etc/sysconfig", "/etc/httpd", "/etc/tomcat", "/etc/pki",
              "/etc/pki-tomcat", "/usr/lib/python*/site-packages/ipa*", "/usr/lib/python*/site-packages/pki*"]

# os : fullpath file : original_line : replace_line
test_file_match_list = {"centos7" : {}}

# %TODO: something with the comment lines! To find them with the grep



def find_all_matches(search):
    """
    Iterate through a search path, find all strings matching 8080 or 8443
    return the files/line-numbers/line-content so long as they dont'appear in
    the ignore_files or ignore_matches
    """
    found = []
    for adir in search:
        for sdir in glob.glob(adir):
            print sdir
            if not os.path.exists(sdir):
                continue
            if sdir in ignore_dirs:
                continue
            for root, dirs, files in os.walk(sdir):
                if root in ignore_dirs:
                    continue
                for afile in files:
                    if afile in ignore_files:
                        #print "ignoring", afile
                        continue
                    if '.' in afile and afile.split('.')[-1] in skip_endings:
                        continue
                    if not os.path.isfile(root + '/' + afile):
                        print "nofile", afile
                        continue
                    if not os.access(root + '/' + afile, os.R_OK):
                        #print "unreadable", afile
                        continue
                    try:
                        #print "trying", afile
                        with open(root + '/' + afile) as fp:
                            for i, line in enumerate(fp):
                                line = line.replace('\n','')
                                if start_insecure in line or start_secure in line:
                                    if line in ignore_matches:
                                        continue
                                    if afile in ignore_file_matches and line in ignore_file_matches[afile]:
                                        continue
                                    found.append((root + '/' + afile, i + 1, line))
                    except IOError, UnicodeDecodeError:
                        continue
    return found

def commentstrip(line):
    if line.strip().startswith('#'):
        for fc in comment_in_manually:
            if line.strip().startswith(fc):
                line = line.replace("# ","").replace("#","")
    return line

def sed_from_matches(matches):
    """
    Take a list of strings, and return a list of strings with all the sed replaces
    """
    ret = []
    for line in matches:
        iret = line + ''
        for sesc in sed_escapes:
            print 'replacing ', sesc
            iret = iret.replace(sesc,'\\'+sesc)
            print iret
        search = iret + ''
        for searchk , searchv in sed_searches.iteritems():
            search = search.replace(searchk,searchv)
        search = search.replace("\n","")
        addl = (len(search.lstrip()) != len(search) )
        addr = (len(search.rstrip()) != len(search) )
        search = '\s*'.join(search.split())
        if addl:
            search = '\s*' + search
        if addr:
            search = search + '\s*'
        replace = iret + ''
        for replacek , replacev in sed_replaces.iteritems():
            replace = replace.replace(replacek,replacev)
        replace = replace.replace("\n","")
        replace = commentstrip(replace)
        ret.append((search,replace))
    return ret

print sed_from_matches(['   http://test.test  '])[0][0]

def create_match_dictionary(saveas=None):
    c7_dict = {}
    for filename, linenum, line in find_all_matches(dir_search):
        search, replace = sed_from_matches([line])[0]
        expected = line.replace(start_secure, pki_secure_port)
        expected = expected.replace(start_insecure, pki_insecure_port)
        expected = commentstrip(expected)
        try:
            c7_dict[filename].append((linenum, line, search, replace, expected))
        except KeyError:
            c7_dict[filename] = [(linenum, line, search, replace, expected)]
    if saveas is not None:
        import json
        with open(saveas,'w') as fp:
            json.dump(c7_dict, fp)
    return c7_dict

def apply_regex_from_json(regexdict):
    for afile, lines in  regexdict:
        for linenum, original, search, replace, expected in lines:
            if not os.path.exists(afile+'.bak'):
                process = subprocess.Popen(['cp','-f', afile, afile+'.bak'])
            command = ['sed', '-i','s/' + search + '/' + replace, afile]
            print command
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = process.communicate()

# Need function that detects if the line is where I expected it to be!
# Need function that checks if the outcome was as expected
# Need function that detects if two json dicts are equal
# need dynamic port in the JSON file, something like {{pki_... port}}, like a template...

#print c7_dict
print create_match_dictionary("test_match.json")
import json
loaded = {}
with open(os.path.dirname(__file__) + 'centos7_server.py') as fp:
    loaded = json.load(fp)
apply_regex_from_json(fp)
import sys

sys.exit()

secure_port ='8445'
insecure_port ='8081'

sed_port_replaces = \
         {
         "/root/test_regex/test_regularexpression/services_base.py":
                         [
                         "s/\s*'pki-tomcatd@pki-tomcat.service'\s*:\s*\[[0-9][0-9][0-9][0-9]\,\s*[0-9][0-9][0-9][0-9]\]/    'pki-tomcatd@pki-tomcat.service': [%s, %s]/" % (
                         insecure_port, secure_port),
                         "s/\s*'pki-tomcat'\s*:\s*\[[0-9][0-9][0-9][0-9]\,\s*[0-9][0-9][0-9][0-9]\]/    'pki-tomcat': [%s, %s]/" % (
                         insecure_port, secure_port),
                         "s/\s*'pki-tomcatd'\s*:\s*\[[0-9][0-9][0-9][0-9]\,\s*[0-9][0-9][0-9][0-9]\]/    'pki-tomcatd': [%s, %s]/" % (
                         insecure_port, secure_port)],


         "/etc/sysconfig/pki/tomcat/pki-tomcat/pki-tomcat" :
                        ["s/\s*PKI_UNSECURE_PORT\s*=\s*[0-9][0-9][0-9][0-9]$/PKI_UNSECURE_PORT=%s/" %insecure_port],

         "/etc/sysconfig/pki-tomcat" :
                        ["s/\s*#\s*Connector\s*port\s*is\s*[0-9][0-9][0-9][0-9]/# Connector port is %s/" %insecure_port],


         "/etc/pki/pki-tomcat/tomcat.conf" :
                        ["s/\s*#\s*Connector\s*port\s*is\s*[0-9][0-9][0-9][0-9]/# Connector port is %s/" %insecure_port],
         "/etc/sysconfig/tomcat" :
                        ["s/\s*#\s*Connector\s*port\s*is\s*[0-9][0-9][0-9][0-9]/# Connector port is %s/" %insecure_port],

             "/root/test_regex/test_regularexpression/server.xml" :
                        ["s/\s*<Connector\s*port=\s*\"[0-9][0-9][0-9][0-9]\"\s*protocol\s*=\"HTTP\/1\.1\"/<Connector port=\"%s\" protocol=\"HTTP\/1\.1\"/" %insecure_port,
                         "s/\s*Define\s*a\s*non-SSL\s*HTTP\/\s*1\.1\s*Connector\s*on\s*port\s*[0-9][0-9][0-9][0-9]/Define a non-SSL HTTP\/1\.1 Connector on port %s/" %insecure_port,
                   "s/\s*redirectPort\s*=\"[0-9][0-9][0-9][0-9]\"\s*\/>/               redirectPort=\"%s\" \/>" %secure_port,
                   "s/\s*<Connector port=\"[0-9][0-9][0-9][0-9]\"\s*protocol\s*=\"AJP\/1\.3\"\s*redirectPort=\"[0-9][0-9][0-9][0-9]\"\s*\/>/    <Connector port=\"8009\" protocol=\"AJP\/1\.3\" redirectPort=\"%s\" \/>" %secure_port,

                         "s/\s*port=\s*\"[0-9][0-9][0-9][0-9]\"\s*protocol\s*=\"HTTP\/1\.1\"/               port=\"%s\"\s*protocol\s*=\"HTTP\/1\.1\"/" %insecure_port],


         "/root/test_regex/test_regularexpression/default.cfg" :
                    ["s/\s*#\s*pki_https_port\s*=[0-9][0-9][0-9][0-9]$/  pki_https_port=%s/" %secure_port,
               "s/\s*#\s*pki_http_port\s*=[0-9][0-9][0-9][0-9]$/  pki_http_port=%s/" %insecure_port,
               "s/\s*pki_security_domain_https_port\s*=\s*'[0-9][0-9][0-9][0-9]'$/pki_security_domain_https_port=%s/g" %secure_port],

         "/root/test_regex/test_regularexpression/services.py" :
                         ["s/\s*port\s*=\s*[0-9][0-9][0-9][0-9]\/                port = %s/" %secure_port],


         "/root/test_regex/test_regularexpression/CS.cfg.ipabkp" :
                         ["s/\s*http.port\s*=\s*[0-9][0-9][0-9][0-9]$/http.port=%s/" %insecure_port,
                          "s/\s*pkicreate.unsecure_port\s*=\s*[0-9][0-9][0-9][0-9]$/pkicreate.unsecure_port=%s/" %insecure_port,
                          "s/\s*service.unsecurePort\s*=\s*[0-9][0-9][0-9][0-9]$/service.unsecurePort=%s/" %insecure_port,
                          "s/\s*https.port\s*=\s*[0-9][0-9][0-9][0-9]$/https.port=%s/" %secure_port,
                          "s/\s*pkicreate.admin_secure_port\s*=\s*[0-9][0-9][0-9][0-9]$/pkicreate.admin_secure_port=%s/" %secure_port,
                          "s/\s*pkicreate.agent_secure_port\s*=\s*[0-9][0-9][0-9][0-9]$/pkicreate.agent_secure_port=%s/" %secure_port,
                          "s/\s*pkicreate.ee_secure_client_auth_port\s*=\s*[0-9][0-9][0-9][0-9]$/pkicreate.ee_secure_client_auth_port=%s/" %secure_port,
                          "s/\s*pkicreate.ee_secure_port\s*=\s*[0-9][0-9][0-9][0-9]$/pkicreate.ee_secure_port=%s/" %secure_port,
                          "s/\s*pkicreate.secure_port\s*=\s*[0-9][0-9][0-9][0-9]$/pkicreate.secure_port=%s/" %secure_port,
                          "s/\s*service.clientauth_securePort\s*=\s*[0-9][0-9][0-9][0-9]$/service.clientauth_securePort=%s/" %secure_port,
                          "s/\s*service.clientauth_securePort\s*=\s*[0-9][0-9][0-9][0-9]$/service.clientauth_securePort=%s/" %secure_port,
                          "s/\s*service.non_clientauth_securePort\s*=\s*[0-9][0-9][0-9][0-9]$/service.non_clientauth_securePort=%s/" %secure_port,
                          "s/\s*service.securePort\s*=\s*[0-9][0-9][0-9][0-9]$/service.securePort=%s/" %secure_port,
                          "s/\s*ca.Policy.rule.AuthInfoAccessExt.ad0\_location\s*=\s*http:\/\/\s*ambari.kave.io\s*\:\s*[0-9][0-9][0-9][0-9]/ca.Policy.rule.AuthInfoAccessExt.ad0_location_location=http:\/\/ambari.kave.io:%s/" %insecure_port],


         "/root/test_regex/test_regularexpression/CS.cfg" :
                         ["s/\s*http.port\s*=\s*[0-9][0-9][0-9][0-9]$/http.port=%s/" %insecure_port,
                          "s/\s*pkicreate.unsecure_port\s*=\s*[0-9][0-9][0-9][0-9]$/pkicreate.unsecure_port=%s/" %insecure_port,
                          "s/\s*service.unsecurePort\s*=\s*[0-9][0-9][0-9][0-9]$/service.unsecurePort=%s/" %insecure_port,
                          "s/\s*https.port\s*=\s*[0-9][0-9][0-9][0-9]$/https.port=%s/" %secure_port,
                          "s/\s*pkicreate.admin_secure_port\s*=\s*[0-9][0-9][0-9][0-9]$/pkicreate.admin_secure_port=%s/" %secure_port,
                          "s/\s*pkicreate.agent_secure_port\s*=\s*[0-9][0-9][0-9][0-9]$/pkicreate.agent_secure_port=%s/" %secure_port,
                          "s/\s*pkicreate.ee_secure_client_auth_port\s*=\s*[0-9][0-9][0-9][0-9]$/pkicreate.ee_secure_client_auth_port=%s/" %secure_port,
                          "s/\s*pkicreate.ee_secure_port\s*=\s*[0-9][0-9][0-9][0-9]$/pkicreate.ee_secure_port=%s/" %secure_port,
                          "s/\s*pkicreate.secure_port\s*=\s*[0-9][0-9][0-9][0-9]$/pkicreate.secure_port=%s/" %secure_port,
                          "s/\s*service.clientauth_securePort\s*=\s*[0-9][0-9][0-9][0-9]$/service.clientauth_securePort=%s/" %secure_port,
                          "s/\s*service.clientauth_securePort\s*=\s*[0-9][0-9][0-9][0-9]$/service.clientauth_securePort=%s/" %secure_port,
                          "s/\s*service.non_clientauth_securePort\s*=\s*[0-9][0-9][0-9][0-9]$/service.non_clientauth_securePort=%s/" %secure_port,
                          "s/\s*service.securePort\s*=\s*[0-9][0-9][0-9][0-9]$/service.securePort=%s/" %secure_port,
                          "s/\s*ca.Policy.rule.AuthInfoAccessExt.ad0\_location\s*=\s*http:\/\/\s*ambari.kave.io\s*\:\s*[0-9][0-9][0-9][0-9]/ca.Policy.rule.AuthInfoAccessExt.ad0_location_location=http:\/\/ambari.kave.io:%s/" %insecure_port],

         "/root/test_regex/test_regularexpression/cainstance.py" :

                         ["s/\s*Check\s*that\s*dogtag\s*port\s*([0-9][0-9][0-9][0-9])/    Check that dogtag port (%s)/" %secure_port,
                          "s/\s*return\s*not\s*ipautil.host\_\port\_\s*open(None\,\s*[0-9][0-9][0-9][0-9])/    return not ipautil.host_port_open(None, %s)/" %secure_port,
                          "s/\s*api.Backend.ra\_\s*certprofile.override\_\port\s*=\s*[0-9][0-9][0-9][0-9]$/    api.Backend.ra_certprofile.override_port = %s/" %secure_port
                         ],
          "/root/test_regex/test_regularexpression/setupAgent.py" :
                         ["s/\s*server_port\s*=\s*[0-9][0-9][0-9][0-9]$/  server_port = %s/" %insecure_port],
         "/root/test_regex/test_regularexpression/httpinstance.py" :
                        ["s/\s*if\s*installutils.update_\s*file(paths.HTTPD_NSS_CONF,\s*'[0-9][0-9][0-9][0-9]',/        if   installutils.update_file(paths.HTTPD_NSS_CONF, \'%s\',/" %secure_port],

         "/root/test_regex/test_regularexpression/dogtag.py" :
                        ["s/\s*UNSECURE_PORT\s*=\s*[0-9][0-9][0-9][0-9]$/    UNSECURE_PORT = %s/" %insecure_port,
                        "s/\s*EE_SECURE_PORT\s*=\s*[0-9][0-9][0-9][0-9]$/    EE_SECURE_PORT = %s/" %secure_port,
                        "s/\s*AGENT_SECURE_PORT\s*=\s*[0-9][0-9][0-9][0-9]$/    AGENT_SECURE_PORT = %s/" %secure_port],

         "/root/test_regex/test_regularexpression/serverConfiguration.py" :
                        ["s/\s*CLIENT_API_PORT\s*=\s*\"[0-9][0-9][0-9][0-9]\"$/CLIENT_API_PORT = \"%s\"/" %insecure_port,
                        "s/\s*DEFAULT_SSL_API_PORT\s*=\s*[0-9][0-9][0-9][0-9]$/DEFAULT_SSL_API_PORT = %s/" %secure_port],

         "/root/test_regex/test_regularexpression/pkiconfig.py" :
                        ["s/\s*PKI_DEPLOYMENT_DEFAULT_TOMCAT_HTTP_PORT\s*=\s*[0-9][0-9][0-9][0-9]$/PKI_DEPLOYMENT_DEFAULT_TOMCAT_HTTP_PORT = %s/" %insecure_port,
                        "s/\s*PKI_DEPLOYMENT_DEFAULT_TOMCAT_HTTPS_PORT\s*=\s*[0-9][0-9][0-9][0-9]$/PKI_DEPLOYMENT_DEFAULT_TOMCAT_HTTPS_PORT = %s/" %secure_port],

         "/root/test_regex/test_regularexpression/pkiparser.py" :
                        ["s/\s*default_http_port\s*=\s*'[0-9][0-9][0-9][0-9]'$/        default_http_port =\'%s\'/" %insecure_port,
                        "s/\s*default_https_port\s*=\s*'[0-9][0-9][0-9][0-9]'$/        default_https_port = \'%s\'/" %secure_port],
         "/root/test_regex/test_regularexpression/pkiparser.py.orig" :
                        ["s/\s*default_http_port\s*=\s*'[0-9][0-9][0-9][0-9]'$/        default_http_port =\'%s\'/" %insecure_port,
                        "s/\s*default_https_port\s*=\s*'[0-9][0-9][0-9][0-9]'$/        default_https_port = \'%s\'/" %secure_port],
         "/root/test_regex/test_regularexpression/client.py" :
                        ["s/\s*def\s*\_\_init\_\_(self,\s*protocol\s*=\s*'http',\s*hostname\s*=\s*'localhost',\s*port\s*=\s*'[0-9][0-9][0-9][0-9]',/    def __init__(self, protocol='http', hostname='localhost', port=\'%s\',/" %insecure_port],

         "/root/test_regex/test_regularexpression/cert.py" :
                        ["s/\s*connection\s*=\s*client.PKIConnection('https',\s*'localhost',\s*'[0-9][0-9][0-9][0-9]',\s*'ca')/    connection = client.PKIConnection('https', 'localhost', \'%s\', 'ca')/" %secure_port],

         "/root/test_regex/test_regularexpression/nssdb.py" :
                        ["s/\s*keystroke\s*+=\s*'http:\/\/\s*server.example.com\s*\:\s*[0-9][0-9][0-9][0-9]/        keystroke += \'http:\/\/server.example.com:%s/" %insecure_port],

         "/root/test_regex/test_regularexpression/profile.py" :
                        ["s/\s*connection\s*=\s*client.PKIConnection('https',\s*'localhost',\s*'[0-9][0-9][0-9][0-9]',\s*'ca')/    connection = client.PKIConnection('https', 'localhost', \'%s\', 'ca')/" %secure_port
                     ]}




for f,s in sed_port_replaces.iteritems():
    fs=glob.glob(f)
    for fi in fs:
        for si in s:
            command = ['sed', '-i',si,fi]
            print command
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = process.communicate()
