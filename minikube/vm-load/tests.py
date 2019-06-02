
import unittest
from unittest import mock
from subprocess import CalledProcessError
from pathlib import Path

import vmload

# https://fgimian.github.io/blog/2014/04/10/using-the-python-mock-library-to-fake-regular-functions-during-tests/


def os_call_test(commandarray):
    return "abcdef"

def os_call_listvms(commandarray):
    return """"<inaccessible>" {afd0bc47-85d2-4bfa-b574-b181622898c2}
"SimpleSecrets" {a55a7f30-1197-440e-9ce9-937f55a18de5}
"kafka" {dcce61e8-dac2-4f71-8233-a794511af457}
"main-app" {3f0914ef-7381-4a9f-96a2-38903ec7ecc3}
"rn-app_default_1557675375783_74941" {fcd4d918-7253-49cc-b53a-e3fe43327b5d}
"sandbox" {a53ea1a3-1ce8-460d-9c9d-7e622505d59e}
"""

def os_call_createmedium(commandarray):
    return "Medium created. UUID: 252b8747-f0fe-40b1-8042-f9d571d6c984"

def os_call_get_allowed_ostypes(commandarray):
    return """ID:          Other
Description: Other/Unknown
Family ID:   Other
Family Desc: Other
64 bit:      false

ID:          Other_64
Description: Other/Unknown (64-bit)
Family ID:   Other
Family Desc: Other
64 bit:      true 

"""

class TestVmLoad(unittest.TestCase):

    def test_os_call(self):
        with self.assertRaises(CalledProcessError):
            vmload.os_call(['cat', '1'])
        vmload.os_call(['echo', '0'])

    @mock.patch('vmload.os_call', side_effect=os_call_test)
    def test_mock(self, oscall_function):
        result = vmload.os_call(['ee'])
        self.assertEqual(result, "abcdef")

    @mock.patch('vmload.os_call', side_effect=os_call_listvms)
    def test_list_vms(self, oscall_function):
        result = vmload.list_vms()
        self.assertEqual(['<inaccessible>', 'SimpleSecrets', 'kafka', 'main-app', 'rn-app_default_1557675375783_74941', 'sandbox'], result)

    def test_vm_nopt_present(self):
        with self.assertRaises(SystemExit):
            vmload.check_vm_not_present(['vm1', 'vm2'], 'vm2')
        vmload.check_vm_not_present(['vm1', 'vm2'], 'vm3')

    def test_derive_dynamic_disc_path(self):
        result = vmload.derive_dynamic_disc_path('/etc/','ecr')
        self.assertEqual(Path('/etc/ecr/ecr.vdi'), result)

    def test_check_dynamic_disc_not_present(self):
        tmpfile = Path('/tmp/tmpfile.txt')
        if tmpfile.exists():
            tmpfile.unlink()
        vmload.check_dynamic_disc_not_present(tmpfile)
        with open(tmpfile, "w") as f:
            f.write("tmpfile")
        with self.assertRaises(ValueError):
            vmload.check_dynamic_disc_not_present(tmpfile)
        tmpfile.unlink()

    @mock.patch('vmload.os_call', side_effect=os_call_createmedium)
    def test_create_dynamic_disc(self, oscall_function):
        tmpfile = Path('/tmp/tmp/tmpfile.txt')
        if tmpfile.exists():
            tmpfile.unlink()
            if tmpfile.parent.exists():
                tmpfile.parent.rmdir()
        result = vmload.create_dynamic_disc(tmpfile, 10000)
        self.assertTrue(tmpfile.parent.exists())
        with self.assertRaises(ValueError):
            vmload.create_dynamic_disc(tmpfile, 1000)

    @mock.patch('vmload.os_call', side_effect=os_call_get_allowed_ostypes)
    def test_get_allowed_ostypes(self, oscall_function):
        result = vmload.get_allowed_ostypes()
        self.assertEqual(['Other', 'Other_64'], result)

    def create_vm(self):
        result = vmload.create_vm('name', 'ostype')