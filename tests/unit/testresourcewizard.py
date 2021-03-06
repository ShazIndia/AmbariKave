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
import unittest
import base
import subprocess as sub
import os


class TestResourceWizard(unittest.TestCase):
    options_results_list = [([0.05, 4, 0, 0, 0, 0], """
For <= 100 GB static input data, consider a single large VM
------------------- Guess Reasonable Specs --------------------------------
        name  count  vcores  ram / GB  jbod_storage / TB  other_disk / GB
1   gateways      1       8        32                0.1              310"""),
                            ([0.3, 4, 0, 0, 0, 0], """
------------------- Guess Reasonable Specs --------------------------------
        name  count  vcores  ram / GB  jbod_storage / TB  other_disk / GB
1     ambari      1       2         6                0.0               50
2        ipa      1       1         3                0.0               20
3  datanodes      3       8        36                1.0               30
4  namenodes      2       8        32                0.0               70
5   gateways      1       8        32                0.1              330
       TOTAL      8      51       213                3.1              630
-----------------  Most relevant example blueprints  ----------------------
---- (don't forget to modify and test, especially modifying passwords) ----"""),
                            ([1, 1, 0, 0, 0, 0], """
------------------- Guess Reasonable Specs --------------------------------
        name  count  vcores  ram / GB  jbod_storage / TB  other_disk / GB
1     ambari      1       2         6                0.0               50
2        ipa      1       1         3                0.0               20
3  datanodes      3      16        72                3.0               30
4  namenodes      2       8        32                0.0               70
5   gateways      1       8        32                0.1              130
       TOTAL      8      75       321                9.1              430
-----------------  Most relevant example blueprints  ----------------------
---- (don't forget to modify and test, especially modifying passwords) ----"""),
                            ([1, 1, 1, 1, 1, 1, 1], """
------------------- Guess Reasonable Specs --------------------------------
        name  count  vcores  ram / GB  jbod_storage / TB  other_disk / GB
1     ambari      1       2         6                0.0               50
2        ipa      1       1         3                0.0               20
3  datanodes      3      16        72                3.0               30
4  namenodes      2       8        32                0.0               70
5   gateways      1       8        32                0.1              130
6      mongo      1       2         4                0.0              130
7  storm-wrk      1       4        16                0.0               30
8     nimbus      1       2         4                0.0               30
9        dev      1       2         8                0.1              130
10     jboss      1       2         4                0.0               20
       TOTAL     13      87       357                9.2              770
-----------------  Most relevant example blueprints  ----------------------
---- (don't forget to modify and test, especially modifying passwords) ----"""),
                            ([8, 8, 0, 0, 0, 0], """
------------------- Guess Reasonable Specs --------------------------------
        name  count  vcores  ram / GB  jbod_storage / TB  other_disk / GB
1     ambari      1       2         6                0.0               50
2        ipa      1       1         3                0.0               20
3  datanodes      4      64       256               16.0               30
4  namenodes      2      32       128                0.0               70
5   gateways      1      12        48                0.1              500
       TOTAL      9     335      1337               64.1              830
-----------------  Most relevant example blueprints  ----------------------
---- (don't forget to modify and test, especially modifying passwords) ----""")]

    def runTest(self):
        """
        Tests that verify the resource wizard behaves correctly
        """
        for opt, expect in self.options_results_list:
            print os.path.dirname(__file__) + '/../../deployment/resource_wizard.py'
            p = sub.Popen([os.path.dirname(__file__) + '/../../deployment/resource_wizard.py'],
                          stdout=sub.PIPE, stderr=sub.PIPE,
                          stdin=sub.PIPE)
            stdout, stderr = p.communicate('\n'.join([str(o) for o in opt]) + '\n')
            stat = p.returncode
            stdout = '\n'.join(stdout.strip().split('\n')[1:-1])
            expect = expect.strip()
            self.assertFalse(stat, stdout + '\n' + stderr)
            self.assertEquals(stdout, expect, " looking for \n\n " +
                              expect + " \n-----\n from options: \n\n" + opt.__str__()
                              + " \n-----\n found: \n\n" + stdout)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestResourceWizard())
    return suite


if __name__ == "__main__":
    base.run(suite())
