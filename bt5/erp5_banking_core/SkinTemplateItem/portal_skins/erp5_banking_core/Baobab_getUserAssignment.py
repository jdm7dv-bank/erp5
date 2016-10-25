if user_id is None:
  person = context.portal_membership.getAuthenticatedMember().getUser().getUserValue()
else:
  person_list = [x for x in context.acl_users.searchUsers(login=user_id) if 'path' in x]
  if person_list:
    person, = person_list
    person = context.getPortalObject().restrictedTraverse(person['path'])
  else:
    person = None
if person is None:
  return None
assignment_list = person.contentValues(filter={'portal_type': 'Assignment'})
if not assignment_list:
  return None
valid_assignment = None
now = DateTime()
for assignment in assignment_list:
  if assignment.getValidationState() == 'open':
    stop = assignment.getStopDate()
    start = assignment.getStartDate()
    if (stop is None or stop > now) and (start is None or start < now):
      if valid_assignment is not None:
        raise ValueError('There are too many valid assignments for user %r' % (user_id, ))
      valid_assignment = assignment
return valid_assignment
