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
import os

from resource_management import *
import kavecommon as kc
from resource_management.core.base import Fail


class Jenkins(Script):
    config_file_path = '/etc/sysconfig/jenkins'

    def install(self, env):
        import params

        env.set_params(params)
        self.install_packages(env)
        dlname = 'jenkins-' + str(params.download_version) + '-1.1.noarch.rpm'
        kc.copy_cache_or_repo(dlname, arch='noarch', alternates='http://pkg.jenkins-ci.org/redhat/' + dlname)
        Execute('rpm -qa | grep -qw jenkins || yum -y install ' + dlname)

        self.configure(env)
        # wget all requested plugins
        for plugin in params.plugins.split(','):
            plugin = plugin.strip()
            if not len(plugin):
                continue
            extsources = ["http://updates.jenkins-ci.org/latest/" + plugin + h for h in [".hpi", ".jpi"]]
            mirrorsources = []
            for mirror in kc.mirrors():
                mirrorsources = mirrorsources + \
                    [kc.repo_url('jenkins_plugins/' + plugin + h, arch='noarch', repo=mirror) for h in [".hpi", ".jpi"]]
            intsources = [kc.repo_url('jenkins_plugins/' + plugin + h, arch='noarch') for h in [".hpi", ".jpi"]]
            source = kc.failover_source(mirrorsources + intsources + extsources)
            dest = params.JENKINS_HOME + "/plugins/" + source.split('/')[-1]
            Execute(kc.copymethods(source, dest))

        File(params.JENKINS_HOME + '/config.xml',
             content=Template("config.xml.j2"),
             mode=0644
             )
        kc.chown_r(params.JENKINS_HOME + '/config.xml', params.JENKINS_USER)
        Execute('chkconfig jenkins on')
        self.start(env)
        # using curl to create username password for jenkinsl
        curl_command = ('curl -d "username=' + params.JENKINS_ADMIN
                        + '&password1=' + params.JENKINS_ADMIN_PASSWORD
                        + '&email=' + params.JENKINS_ADMIN_EMAIL + '&password2='
                        + params.JENKINS_ADMIN_PASSWORD + '&fullname='
                        + params.JENKINS_ADMIN + '&Submit=Sign%20up" "http://'
                        + params.hostname + ':' + str(params.JENKINS_PORT) + '/securityRealm/createAccount"')
        try:
            Execute(curl_command)
        except Fail as ex:
            print "the curl command met with failure the first time,,,trying in another 60 secs"
            print ex
            import time
            time.sleep(60)
            Execute(curl_command)

    def start(self, env):
        self.configure(env)
        Execute('service jenkins start')

    def stop(self, env):
        Execute('service jenkins stop')

    def restart(self, env):
        self.configure(env)
        Execute('service jenkins restart')

    def status(self, env):
        Execute('service jenkins status')

    def configure(self, env):
        # stop service if running
        # recreate from templates
        # restart
        # read previous jenkins home and jenkins user ...
        orig_juser = "jenkins"
        orig_jhome = "/var/lib/jenkins"
        if os.path.exists(self.config_file_path):
            f = open(self.config_file_path)
            ls = f.readlines()
            f.close()
            for l in ls:
                if l.startswith("JENKINS_USER"):
                    orig_juser_parse = l.split("=")[-1].strip().replace('"', '')
                    if len(orig_juser_parse):
                        orig_juser = orig_juser_parse
                elif l.startswith("JENKINS_HOME"):
                    orig_jhome_parse = l.split("=")[-1].strip().replace('"', '')
                    if len(orig_jhome_parse):
                        orig_jhome = orig_jhome_parse

        import params
        env.set_params(params)
        # If jenkins user has changed, create the new user
        if params.JENKINS_USER != orig_juser:
            Execute('useradd ' + params.JENKINS_USER)
        # If jenkins home has changed, create the new directory
        if params.JENKINS_HOME != orig_jhome and not os.path.exists(params.JENKINS_HOME):
            Execute('mkdir -p ' + params.JENKINS_HOME)
        # If jenkins home has changed, mv contents of jenkins home directory
        if params.JENKINS_HOME != orig_jhome and os.path.exists(orig_jhome):
            import glob

            if len(glob.glob(orig_jhome + '/*')):
                Execute('mv ' + orig_jhome + '/* ' + params.JENKINS_HOME + "/")
        if not os.path.exists(params.JENKINS_HOME + '/plugins'):
            Execute('mkdir -p ' + params.JENKINS_HOME + '/plugins')

        File(self.config_file_path,
             content=Template("jenkins.j2"),
             mode=0600
             )
        kc.chmod_up(self.config_file_path, "a+rx")
        kc.chmod_up(params.JENKINS_HOME, "a+rx")
        kc.chown_r(self.config_file_path, params.JENKINS_USER)
        kc.chown_r(params.JENKINS_HOME, params.JENKINS_USER)


if __name__ == "__main__":
    Jenkins().execute()
