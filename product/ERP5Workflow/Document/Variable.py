##############################################################################
#
# Copyright (c) 2006 Nexedi SARL and Contributors. All Rights Reserved.
#                    Romain Courteaud <romain@nexedi.com>
#               2015 Wenjie Zheng <wenjie.zheng@tiolive.com>
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from AccessControl import ClassSecurityInfo
from Products.CMFCore.Expression import Expression
from Products.DCWorkflow.Guard import Guard
from Products.ERP5Type import Permissions, PropertySheet
from Products.ERP5Type.id_as_reference import IdAsReferenceMixin
from Products.ERP5Type.XMLObject import XMLObject

class Variable(IdAsReferenceMixin("variable_", "prefix"), XMLObject):
    """
    A ERP5 Variable.
    """

    meta_type = 'ERP5 Variable'
    portal_type = 'Variable'
    add_permission = Permissions.AddPortalContent
    isPortalContent = 1
    isRADContent = 1

    info_guard = None
    description = ''
    for_catalog = 1
    for_status = 1
    default_value = ''
    default_expr = None  # Overrides default_value if set
    info_guard = None
    update_always = 1
    default_reference = ''
    # Declarative security
    security = ClassSecurityInfo()
    security.declareObjectProtected(Permissions.AccessContentsInformation)

    # Declarative properties
    property_sheets = (
               PropertySheet.Base,
               PropertySheet.XMLObject,
               PropertySheet.CategoryCore,
               PropertySheet.DublinCore,
               PropertySheet.Reference,
               PropertySheet.Variable,
    )

    def getDefaultExprText(self):
        if not self.default_expr:
            return ''
        else:
            return self.default_expr.text

    def generateInfoGuard(self):
        if self.info_guard == None:
          self.info_guard = Guard(permissions=self.getPermissionList(),
                        roles=self.getRoleList(),
                        groups=self.getGroupList(),
                        expr=self.getExpression())

        if self.info_guard.roles != self.getRoleList():
          self.info_guard.roles = self.getRoleList()
        elif self.info_guard.permissions != self.getPermissionList():
          self.info_guard.permissions = self.getPermissionList()
        elif self.info_guard.groups != self.getGroupList():
          self.info_guard.groups = self.getGroupList()
        elif self.info_guard.expr != self.getExpression():
          self.info_guard.expr = self.getExpression()

    def getInfoGuard(self):
        if self.info_guard is not None:
            self.generateGuard()
        return self.info_guard

    def getInfoGuardSummary(self):
        res = None
        if self.info_guard is not None:
            res = self.info_guard.getSummary()
        return res
