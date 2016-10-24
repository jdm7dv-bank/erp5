from AccessControl.users import BasicUser
if True:
    def getIdOrUserName(self):
        return self.getId() or self.getUserName()

    BasicUser.getIdOrUserName = getIdOrUserName

    def __str__(self):
        raise RuntimeError, 'use getIdOrUserName() instead of __str__().'

    BasicUser.__str__ = __str__
