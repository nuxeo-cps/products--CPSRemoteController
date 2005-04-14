# $id$

from Testing import ZopeTestCase
from Products.ExternalMethod.ExternalMethod import ExternalMethod
from Products.CPSDefault.tests import CPSTestCase

ZopeTestCase.installProduct('CPSRemoteController')

CPSTestCase.setupPortal()

CPSRemoteControllerTestCase = CPSTestCase.CPSTestCase
