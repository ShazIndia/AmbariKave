#!/bin/sh
##############################################################################
#
# Copyright 2017 KPMG Advisory N.V. (unless otherwise stated)
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

#This is a Cloudbreak pre-recipe for the Ambari node.
#Used when deploying AmbariKave from local Git repo.
#Log at /var/log/recipes/pre-patchambari-git-{version}.log

#At every release, please update this variable.
HDP_STACK=2.6

yum -y install wget curl tar zip unzip gzip python
sudo tar -xzf /home/cloudbreak/kave-patch.tar.gz -C /var/lib \
--exclude KAVE/metainfo.xml \
--exclude KAVE/services/stack_advisor.py \
--exclude KAVE/repos
sudo rsync -r /var/lib/KAVE/ /var/lib/ambari-server/resources/stacks/HDP/$HDP_STACK

sudo python /home/cloudbreak/dist_kavecommon.py /var/lib/ambari-server/resources/stacks/HDP /var/lib/shared/kavecommon.py

systemctl stop ambari-server
systemctl start ambari-server
