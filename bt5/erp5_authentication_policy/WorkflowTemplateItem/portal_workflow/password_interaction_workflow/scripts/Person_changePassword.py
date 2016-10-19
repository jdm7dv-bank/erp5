from DateTime import DateTime
portal = context.getPortalObject()
person = state_change['object']

# check preferences and save only if set

if portal.portal_preferences.getPreferredNumberOfLastPasswordToCheck() or \
    portal.portal_preferences.getPreferredMaxPasswordLifetimeDuration() is not None:
  # save password and modification date
  current_password = person.getPassword()
  if current_password is not None:
    password_event = portal.system_event_module.newContent(portal_type = 'Password Event',
                                                           source_value = person,
                                                           destination_value = person,
                                                           password = current_password)
    password_event.confirm()
    # Person_isPasswordExpired cache the wrong result if document is not in catalog.
    # As the document is created in the same transaction, it is possible to force reindexation
    password_event.immediateReindexObject()
