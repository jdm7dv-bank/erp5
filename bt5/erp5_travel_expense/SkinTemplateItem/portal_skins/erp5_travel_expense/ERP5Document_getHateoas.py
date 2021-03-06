from ZTUtils import make_query
import json
from base64 import urlsafe_b64encode, urlsafe_b64decode
from DateTime import DateTime
if REQUEST is None:
  REQUEST = context.REQUEST
  # raise Unauthorized
if response is None:
  response = REQUEST.RESPONSE

url_template_dict = {
  "form_action": "%(traversed_document_url)s/%(action_id)s",
  "traverse_generator": "%(root_url)s/%(script_id)s?mode=traverse" + \
                       "&relative_url=%(relative_url)s&view=%(view)s",
  "traverse_template": "%(root_url)s/%(script_id)s?mode=traverse" + \
                       "{&relative_url,view}",
  "search_template": "%(root_url)s/%(script_id)s?mode=search" + \
                     "{&query,select_list*,limit*,sort_on*}",
  "custom_search_template": "%(root_url)s/%(script_id)s?mode=search" + \
                     "&relative_url=%(relative_url)s" \
                     "&form_relative_url=%(form_relative_url)s" \
                     "&list_method=%(list_method)s" \
                     "&default_param_json=%(default_param_json)s" \
                     "{&query,select_list*,limit*,sort_on*}",
  "custom_search_template_no_editable": "%(root_url)s/%(script_id)s?mode=search" + \
                     "&relative_url=%(relative_url)s" \
                     "&list_method=%(list_method)s" \
                     "&default_param_json=%(default_param_json)s" \
                     "{&query,select_list*,limit*,sort_on*}",
  "new_content_action": "%(root_url)s/%(script_id)s?mode=newContent",
  "bulk_action": "%(root_url)s/%(script_id)s?mode=bulk",
  # XXX View is set by default to empty
  "document_hal": "%(root_url)s/%(script_id)s?mode=traverse" + \
                  "&relative_url=%(relative_url)s",
  "jio_get_template": "urn:jio:get:%(relative_url)s",
  "jio_search_template": "urn:jio:allDocs?%(query)s"
}

default_document_uri_template = url_template_dict["jio_get_template"]

def getRealRelativeUrl(document):
  return '/'.join(portal.portal_url.getRelativeContentPath(document))

def getFormRelativeUrl(form):
  return portal.portal_catalog(
    portal_type="ERP5 Form",
    uid=form.getUid(),
    id=form.getId(),
    limit=1,
    select_dict={'relative_url': None}
  )[0].relative_url

def getFieldDefault(traversed_document, field, key, value=None):
  # REQUEST.get(field.id, field.get_value("default"))
  return traversed_document.Field_getDefaultValue(field, key, value, REQUEST)

def renderField(traversed_document, field, form_relative_url, value=None, meta_type=None, key=None):
  if meta_type is None:
    meta_type = field.meta_type
  if key is None:
    key = field.generate_field_key()

  if meta_type == "ProxyField":
    result = renderField(traversed_document, field, form_relative_url, value, meta_type=field.getRecursiveTemplateField().meta_type, key=key)
  elif meta_type == "ListField":
    result = {
      "type": meta_type,
      "key": key,
      "editable": field.get_value("editable"),
      "css_class": field.get_value("css_class"),
      "hidden": field.get_value("hidden"),
      "description": field.get_value("description"),
      "title": field.get_value("title"),
      "required": field.get_value("required"),
      # XXX Message can not be converted to json as is
      "items": field.get_value("items"),
    }
    result["default"] = getFieldDefault(traversed_document, field, result["key"], value)
  elif meta_type == "RadioField":
    result = {
      "type": meta_type,
      "key": key,
      "editable": field.get_value("editable"),
      "css_class": field.get_value("css_class"),
      "hidden": field.get_value("hidden"),
      "description": field.get_value("description"),
      "title": field.get_value("title"),
      "required": field.get_value("required"),
      "items": field.get_value("items"),
      "select_first_item": field.get_value("first_item"),
      "orientation": field.get_value("orientation"),
    }
    result["default"] = getFieldDefault(traversed_document, field, result["key"], value)
  elif meta_type in ("ParallelListField", "MultiListField"):
    result = {
      "type": meta_type,
      "key": key,
      "editable": field.get_value("editable"),
      "css_class": field.get_value("css_class"),
      "hidden": field.get_value("hidden"),
      "description": field.get_value("description"),
      "title": field.get_value("title"),
      "required": field.get_value("required"),
      # XXX Message can not be converted to json as is
      "items": field.get_value("items"),
    }
    result["default"] = getFieldDefault(traversed_document, field, result["key"], value)
    result["sub_select_key"] = traversed_document.Field_getSubFieldKeyDict(field, 'default:list', key=result["key"])
    result["sub_input_key"] = "default_" + traversed_document.Field_getSubFieldKeyDict(field, 'default:list:int', key=result["key"])
  elif meta_type in ("StringField", "FloatField", "EmailField", "TextAreaField",
                     "LinesField", "ImageField", "FileField", "IntegerField",
                     "PasswordField", "EditorField"):
    result = {
      "type": meta_type,
      "key": key,
      "editable": field.get_value("editable"),
      "css_class": field.get_value("css_class"),
      "hidden": field.get_value("hidden"),
      "description": field.get_value("description"),
      "title": field.get_value("title"),
      "required": field.get_value("required"),
    }
    result["default"] = getFieldDefault(traversed_document, field, result["key"], value)
    if meta_type == "FloatField":
      result["precision"] = field.get_value("precision")
    if meta_type == "ImageField":
      options = {}
      options['display'] = field.get_value('image_display')
      options['format'] = field.get_value('image_format')
      options['quality'] = field.get_value('image_quality')
      pre_converted_only = field.get_value('image_pre_converted_only')
      if pre_converted_only:
        options['pre_converted_only'] = pre_converted_only
      parameters = '&'.join(['%s=%s' % (k, v) for k, v in options.items() \
                            if v])
      if parameters:
        result["default"] = '%s?%s' % (result["default"], parameters)

  elif meta_type == "DateTimeField":
    result = {
      "type": meta_type,
      "key": key,
      "editable": field.get_value("editable"),
      "css_class": field.get_value("css_class"),
      "hidden": field.get_value("hidden"),
      "description": field.get_value("description"),
      "title": field.get_value("title"),
      "required": field.get_value("required"),
      "date_only": field.get_value("date_only"),
      "ampm_time_style": field.get_value("ampm_time_style"),
      "timezone_style": field.get_value("timezone_style"),
      "allow_empty_time": field.get_value('allow_empty_time'),
      "hide_day": field.get_value('hide_day'),
      "hidden_day_is_last_day": field.get_value('hidden_day_is_last_day'),
    }
    date_value = getFieldDefault(traversed_document, field, result["key"], value)
    if same_type(date_value, DateTime()):
      # Serialize DateTime
      date_value = date_value.rfc822()
    result["default"] = date_value
    for subkey in ("year", "month", "day", "hour", "minute", "ampm", "timezone"):
      result["subfield_%s_key" % subkey] = traversed_document.Field_getSubFieldKeyDict(field, subkey, key=result["key"])

  elif meta_type in ("RelationStringField", "MultiRelationStringField"):
    portal_type_list = field.get_value('portal_type')
    if portal_type_list:
      portal_type_list = [x[0] for x in portal_type_list]

      # ported from Base_jumpToRelatedDocument\n
      base_category = field.get_value('base_category')
      kw = {}
      for k, v in field.get_value('parameter_list'):
        kw[k] = v

      accessor_name = 'get%sValueList' % \
        ''.join([part.capitalize() for part in base_category.split('_')])
      jump_reference_list = getattr(traversed_document, accessor_name)(
        portal_type=[x[0] for x in field.get_value('portal_type')],

        filter=kw
      )
    query = url_template_dict["jio_search_template"] % {
      "query": make_query({"query": sql_catalog.buildQuery(
        {"portal_type": portal_type_list}
      ).asSearchTextExpression(sql_catalog)})
    }
    result = {
      "portal_types": portal_type_list,
      "query": query,
      "catalog_index": field.get_value('catalog_index'),
      "allow_jump": field.get_value('allow_jump'),
      "allow_creation": field.get_value('allow_creation'),
      "type": meta_type,
      "key": key,
      "editable": field.get_value("editable"),
      "css_class": field.get_value("css_class"),
      "hidden": field.get_value("hidden"),
      "description": field.get_value("description"),
      "title": field.get_value("title"),
      "required": field.get_value("required")
    }
    result["default"] = getFieldDefault(traversed_document, field, result["key"], value)
    result["relation_field_id"] = traversed_document.Field_getSubFieldKeyDict(
      field,
      "relation",
      key=result["key"]
    )
    result["relation_item_key"] = traversed_document.Field_getSubFieldKeyDict(
      field,
      "item", key=result["key"]
    )

    if jump_reference_list:
      url = [jump_reference.getRelativeUrl() for jump_reference in jump_reference_list]
      uid = [jump_reference.getUid() for jump_reference in jump_reference_list]
      result["relation_item_relative_url"] = url
      result["relation_item_uid"] = uid

  elif meta_type == "CheckBoxField":
    result = {
      "type": meta_type,
      "key": key,
      "editable": field.get_value("editable"),
      "css_class": field.get_value("css_class"),
      "hidden": field.get_value("hidden"),
      "description": field.get_value("description"),
      "title": field.get_value("title")
    }
    result["default"] = getFieldDefault(traversed_document, field, result["key"], value)
  elif meta_type == "MultiCheckBoxField":
    result = {
      "type": meta_type,
      "key": key,
      "editable": field.get_value("editable"),
      "css_class": field.get_value("css_class"),
      "hidden": field.get_value("hidden"),
      "description": field.get_value("description"),
      "title": field.get_value("title"),
      "required": field.get_value("required"),
      # XXX Message can not be converted to json as is
      "items": field.get_value("items"),
    }
    result["default"] = getFieldDefault(traversed_document, field, result["key"], value)
  elif meta_type == "GadgetField":
    result = {
      "type": meta_type,
      "key": key,
      "editable": field.get_value("editable"),
      "css_class": field.get_value("css_class"),
      "hidden": field.get_value("hidden"),
      "description": field.get_value("description"),
      "title": field.get_value("title"),
      "url": field.get_value("gadget_url"),
      "sandbox": field.get_value("js_sandbox"),
    }
    result["default"] = getFieldDefault(traversed_document, field, result["key"], value)
  elif meta_type == "ListBox":
    # XXX Not implemented
    column_list = field.get_value("columns")
    search_column_list = field.get_value('search_columns')
    editable_column_list = field.get_value('editable_columns')

    # XXX 
#     list_method = getattr(traversed_document, traversed_document.Listbox_getListMethodName(field))
    # portal_types = [x[1] for x in field.get_value('portal_types')]
    portal_types = field.get_value('portal_types')
    default_params = dict(field.get_value('default_params'))
    # How to implement pagination?
    # default_params.update(REQUEST.form)
    lines = field.get_value('lines')
    list_method_name = traversed_document.Listbox_getListMethodName(field)
    list_method_query_dict = dict(
      portal_type=[x[1] for x in portal_types], **default_params
    )
    list_method_custom = None

    if (editable_column_list):
      list_method_custom = url_template_dict["custom_search_template"] % {
        "root_url": site_root.absolute_url(),
        "script_id": script.id,
        "relative_url": traversed_document.getRelativeUrl().replace("/", "%2F"),
        "form_relative_url": "%s/%s" % (form_relative_url, field.id),
        "list_method": list_method_name,
        "default_param_json": urlsafe_b64encode(json.dumps(list_method_query_dict))
      }
      list_method_query_dict = {}
    elif (list_method_name == "portal_catalog"):
      pass
    elif (list_method_name == "searchFolder"):
      list_method_query_dict["parent_uid"] = traversed_document.getUid()
    else:
      list_method_custom = url_template_dict["custom_search_template_no_editable"] % {
        "root_url": site_root.absolute_url(),
        "script_id": script.id,
        "relative_url": traversed_document.getRelativeUrl().replace("/", "%2F"),
        "list_method": list_method_name,
        "default_param_json": urlsafe_b64encode(json.dumps(list_method_query_dict))
      }
      list_method_query_dict = {}

#     row_list = list_method(limit=lines, portal_type=portal_types,
#                            **default_params)
#     line_list = []
#     for row in row_list:
#       document = row.getObject()
#       line = {
#         "url": url_template_dict["document_hal"] % {
#           "root_url": site_root.absolute_url(),
#           "relative_url": document.getRelativeUrl(),
#           "script_id": script.id
#         }
#       }
#       for property, title in columns:
#         prop = document.getProperty(property)
#         if same_type(prop, DateTime()):
#           prop = "XXX Serialize DateTime"  
#         line[title] = prop
#         line["_relative_url"] = document.getRelativeUrl()
#       line_list.append(line)

    result = {
      "type": meta_type,
      "editable": field.get_value("editable"),
      # "column_list": [x[1] for x in columns],
      "column_list": column_list,
      "search_column_list": search_column_list,
      "editable_column_list": editable_column_list,
      "show_anchor": field.get_value("anchor"),
#       "line_list": line_list,
      "title": field.get_value("title"),
      "key": key,
      "portal_type": portal_types,
      "lines": lines,
      "default_params": default_params,
      "list_method": list_method_name
    }
    if (list_method_custom is not None):
      result["list_method_template"] = list_method_custom

    result["query"] = url_template_dict["jio_search_template"] % {
        "query": make_query({"query": sql_catalog.buildQuery(
          list_method_query_dict
        ).asSearchTextExpression(sql_catalog)})
      }
  else:
    # XXX Not implemented
    result = {
      "type": meta_type,
      "_debug": "Unsupported field type",
      "title": field.get_value("title"),
      "key": key,
    }
  return result


def renderForm(traversed_document, form, response_dict):
  REQUEST.set('here', traversed_document)
  field_errors = REQUEST.get('field_errors', {})

  #hardcoded
  if form.pt == 'form_dialog':
    action_to_call = "Base_callDialogMethod"
  else:
    action_to_call = form.action

  # Form action
  response_dict['_actions'] = {
    'put': {
      "href": url_template_dict["form_action"] % {
        "traversed_document_url": site_root.absolute_url() + "/" + traversed_document.getRelativeUrl(),
        "action_id": action_to_call
      },
      "action": form.action,
      "method": form.method,
    }
  }
  # Form traversed_document
  response_dict['_links']['traversed_document'] = {
    "href": default_document_uri_template % {
      "root_url": site_root.absolute_url(),
      "relative_url": traversed_document.getRelativeUrl(),
      "script_id": script.id
    },
    "name": traversed_document.getRelativeUrl(),
    "title": traversed_document.getTitle()
  }

  form_relative_url = getFormRelativeUrl(form)
  response_dict['_links']['form_definition'] = {
#     "href": default_document_uri_template % {
#       "root_url": site_root.absolute_url(),
#       "script_id": script.id,
#       "relative_url": getFormRelativeUrl(form)
#     },
    "href": default_document_uri_template % {
      "relative_url": form_relative_url
    },
    'name': form.id
  }

  for group in form.Form_getGroupTitleAndId():

    if group['gid'].find('hidden') < 0:
#       field_list = []
      for field in form.get_fields_in_group(group['goid']):
#         field_list.append((field.id, renderRawField(field)))
        if field.get_value("enabled"):
          try:
            response_dict[field.id] = renderField(traversed_document, field, form_relative_url)
            if field_errors.has_key(field.id):
              response_dict[field.id]["error_text"] = field_errors[field.id].error_text
          except AttributeError:
            # Do not crash if field configuration is wrong.
            pass

  #       for field_group in field.form.get_groups():
  #         traversed_document.log("Field group: " + field_group)
  #         traversed_document.log(field_group)
  #         for field_property in field.form.get_fields_in_group(field_group):
  # #           traversed_document.log("Field attribute: " + field_property.id)
  # #           field.get_value(field_property.id)
  #           traversed_document.log(field_property)

#       group_list.append((group['gid'], field_list))

  response_dict["form_id"] = {
    "type": "StringField",
    "key": "form_id",
    "default": form.id,
    "editable": 0,
    "css_class": "",
    "hidden": 1,
    "description": "",
    "title": "form_id",
    "required": 1,
  }

#   response_dict["group_list"] = group_list
# rendered_response_dict["_embedded"] = {
#   "form": raw_response_dict
# }


# XXX form action update, etc
def renderRawField(field):
  meta_type = field.meta_type

  return {
    "meta_type": field.meta_type
  }


  if meta_type == "MethodField":
    result = {
      "meta_type": field.meta_type
    }
  else:
    result = {
      "meta_type": field.meta_type,
      "_values": field.values,
      # XXX TALES expression is not JSON serializable by default
      # "_tales": field.tales
      "_overrides": field.overrides
    }
  if meta_type == "ProxyField":
    result['_delegated_list'] = field.delegated_list
#     try:
#       result['_delegated_list'].pop('list_method')
#     except KeyError:
#       pass

  # XXX ListMethod is not JSON serialized by default
  try:
    result['_values'].pop('list_method')
  except KeyError:
    pass
  try:
    result['_overrides'].pop('list_method')
  except KeyError:
    pass
  return result


def renderFormDefinition(form, response_dict):
  group_list = []
  for group in form.Form_getGroupTitleAndId():

    if group['gid'].find('hidden') < 0:
      field_list = []

      for field in form.get_fields_in_group(group['goid'], include_disabled=1):
        field_list.append((field.id, renderRawField(field)))

      group_list.append((group['gid'], field_list))
  response_dict["group_list"] = group_list
  response_dict["title"] = form.getTitle()
  response_dict["pt"] = form.pt
  response_dict["action"] = form.action


mime_type = 'application/hal+json'
portal = context.getPortalObject()
sql_catalog = portal.portal_catalog.getSQLCatalog()

# Calculate the site root to prevent unexpected browsing
is_web_mode = (context.REQUEST.get('current_web_section', None) is not None) or (hasattr(context, 'isWebMode') and context.isWebMode())
# is_web_mode =  traversed_document.isWebMode()
if is_web_mode:
  site_root = context.getWebSectionValue()
  view_action_type = site_root.getLayoutProperty("configuration_view_action_category", default='object_view')
else:
  site_root = portal
  view_action_type = "object_view"

context.Base_prepareCorsResponse(RESPONSE=response)

# Check if traversed_document is the site_root
if relative_url:
  temp_traversed_document = site_root.restrictedTraverse(relative_url, None)
  if (temp_traversed_document is None):
    response.setStatus(404)
    return ""
else:
  temp_traversed_document = context
temp_is_site_root = (temp_traversed_document.getPath() == site_root.getPath())
temp_is_portal = (temp_traversed_document.getPath() == portal.getPath())

def calculateHateoas(is_portal=None, is_site_root=None, traversed_document=None, REQUEST=None,
                     response=None, view=None, mode=None, query=None,
                     select_list=None, limit=None, form=None,
                     relative_url=None, restricted=None, list_method=None,
                     default_param_json=None, form_relative_url=None):

  if relative_url:
    try:
      traversed_document = site_root.restrictedTraverse(str(relative_url))
      view = str(view)
      is_site_root = False
    except:
      raise NotImplementedError(relative_url)
  result_dict = {
    '_debug': mode,
    '_links': {
      "self": {
        # XXX Include query parameters
        # FIXME does not work in case of bulk queries
        "href": traversed_document.Base_getRequestUrl()
      },
      # Always inform about site root
      "site_root": {
        "href": default_document_uri_template % {
          "root_url": site_root.absolute_url(),
          "relative_url": site_root.getRelativeUrl(),
          "script_id": script.id
        },
        "name": site_root.getTitle(),
      },
      # Always inform about portal
      "portal": {
        "href": default_document_uri_template % {
          "root_url": portal.absolute_url(),
          # XXX the portal has an empty getRelativeUrl. Make it still compatible
          # with restrictedTraverse
          "relative_url": portal.getId(),
          "script_id": script.id
        },
        "name": portal.getTitle(),
      }
    }
  }
  
  
  if (restricted == 1) and (portal.portal_membership.isAnonymousUser()):
    response.setStatus(401)
  
  elif mime_type != traversed_document.Base_handleAcceptHeader([mime_type]):
    response.setStatus(406)
    return ""
  
  
  elif (mode == 'root') or (mode == 'traverse'):
    #################################################
    # Raw document
    #################################################
    if (REQUEST is not None) and (REQUEST.other['method'] != "GET"):
      response.setStatus(405)
      return ""
    # Default properties shared by all ERP5 Document and Site
    action_dict = {}
  #   result_dict['_relative_url'] = traversed_document.getRelativeUrl()
    result_dict['title'] = traversed_document.getTitle()
  
    # Add a link to the portal type if possible
    if not is_portal:
      result_dict['_links']['type'] = {
        "href": default_document_uri_template % {
          "root_url": site_root.absolute_url(),
          "relative_url": portal.portal_types[traversed_document.getPortalType()]\
                            .getRelativeUrl(), 
          "script_id": script.id
        },
        "name": traversed_document.getPortalType(),
      }
      
    # Return info about container
    if not is_portal:
      container = traversed_document.getParentValue()
      if container != portal:
        # Jio does not support fetching the root document for now
        result_dict['_links']['parent'] = {
          "href": default_document_uri_template % {
            "root_url": site_root.absolute_url(),
            "relative_url": container.getRelativeUrl(), 
            "script_id": script.id
          },
          "name": container.getTitle(),
        }
  
    # XXX Loop on form rendering
    erp5_action_dict = portal.Base_filterDuplicateActions(
      portal.portal_actions.listFilteredActionsFor(traversed_document))
  
    embedded_url = None
    # XXX See ERP5Type.getDefaultViewFor
    for erp5_action_key in erp5_action_dict.keys():
      erp5_action_list = []
      for view_action in erp5_action_dict[erp5_action_key]:
        # Action condition is probably checked in Base_filterDuplicateActions
        erp5_action_list.append({
          'href': '%s' % view_action['url'],
          'name': view_action['id'],
          'title': view_action['title']
        })
        # Try to embed the form in the result
        if (view == view_action['id']):
          embedded_url = '%s' % view_action['url']
          
        if (erp5_action_key in (view_action_type, "view", "workflow", "object_new_content_action")):
          erp5_action_list[-1]['href'] = url_template_dict["traverse_generator"] % {
                "root_url": site_root.absolute_url(),
                "script_id": script.id,
                "relative_url": traversed_document.getRelativeUrl().replace("/", "%2F"),
                "view": erp5_action_list[-1]['name']
              }
  
      if erp5_action_list:
        if len(erp5_action_list) == 1:
          erp5_action_list = erp5_action_list[0]
          
        if erp5_action_key == view_action_type:
          # Configure view tabs on server level
          result_dict['_links']["view"] = erp5_action_list
          
        # XXX Put a prefix to prevent conflict
        result_dict['_links']["action_" + erp5_action_key] = erp5_action_list
  
  #   for view_action in erp5_action_dict.get('object_view', []):
  #     traversed_document.log(view_action)
  #     # XXX Check the action condition
  # #     if (view is None) or (view != view_action['name']):
  #     object_view_list.append({
  #       'href': '%s' % view_action['url'],
  #       'name': view_action['name']
  #     })
  
  
  #   if (renderer_form is not None):
  #     traversed_document_property_dict, renderer_form_json = traversed_document.Base_renderFormAsSomething(renderer_form)
  #     result_dict['_embedded'] = {
  #       'object_view': renderer_form_json
  #     }
  #     result_dict.update(traversed_document_property_dict)
  
    # XXX XXX XXX XXX
    if (embedded_url is not None):
      # XXX Try to fetch the form in the traversed_document of the document
      # Of course, this code will completely crash in many cases (page template
      # instead of form, unexpected action TALES expression). Happy debugging.
      # renderer_form_relative_url = view_action['url'][len(portal.absolute_url()):]
      form_id = embedded_url.split('?', 1)[0].split("/")[-1]
      # renderer_form = traversed_document.restrictedTraverse(form_id, None)
      # XXX Proxy field are not correctly handled in traversed_document of web site
      renderer_form = getattr(traversed_document, form_id)
  #     traversed_document.log(form_id)
      if (renderer_form is not None):
        embedded_dict = {
          '_links': {
            'self': {
              'href': embedded_url
            }
          }
        }
        # Put all query parameters (?reset:int=1&workflow_action=start_action) in request to mimic usual form display
        query_split = embedded_url.split('?', 1)
        if len(query_split) == 2:
          for query_parameter in query_split[1].split("&"):
            query_key, query_value = query_parameter.split("=")
            REQUEST.set(query_key, query_value)
  
        renderForm(traversed_document, renderer_form, embedded_dict)
        result_dict['_embedded'] = {
          '_view': embedded_dict
          # embedded_action_key: embedded_dict
        }
  #       result_dict['_links']["_view"] = {"href": embedded_url}
  
        # Include properties in document JSON
        # XXX Extract from renderer form?
        """
        for group in renderer_form.Form_getGroupTitleAndId():
          for field in renderer_form.get_fields_in_group(group['goid']):
            field_id = field.id
  #           traversed_document.log(field_id)
            if field_id.startswith('my_'):
              property_name = field_id[len('my_'):]
  #             traversed_document.log(property_name)
              property_value = traversed_document.getProperty(property_name, d=None)
              if (property_value is not None):
                if same_type(property_value, DateTime()):
                  # Serialize DateTime
                  property_value = property_value.rfc822()
                result_dict[property_name] = property_value 
                """
  
    ##############
    # XXX Custom slapos code
    ##############
    if is_site_root:
  
      result_dict['default_view'] = 'view'
      REQUEST.set("X-HATEOAS-CACHE", 1)
  
      # Global action users for the jIO plugin
      # XXX Would be better to not hardcode them but put them as portal type
      # "actions" (search could be on portal_catalog document, traverse on all
      # documents, newContent on all, etc)
  #     result_dict['_links']['object_search'] = {
  #       'href': '%s/ERP5Site_viewSearchForm?portal_skin=Hal' % absolute_url,
  #       'name': 'Global Search'
  #     }
      result_dict['_links']['raw_search'] = {
        "href": url_template_dict["search_template"] % {
          "root_url": site_root.absolute_url(),
          "script_id": script.id
        },
        'name': 'Raw Search',
        'templated': True
      }
      result_dict['_links']['traverse'] = {
        "href": url_template_dict["traverse_template"] % {
          "root_url": site_root.absolute_url(),
          "script_id": script.id
        },
        'name': 'Traverse',
        'templated': True
      }
      action_dict['add'] = {
        "href": url_template_dict["new_content_action"] % {
          "root_url": site_root.absolute_url(),
          "script_id": script.id
        },
        'method': 'POST',
        'name': 'New Content',
      }
      action_dict['bulk'] = {
        "href": url_template_dict["bulk_action"] % {
          "root_url": site_root.absolute_url(),
          "script_id": script.id
        },
        'method': 'POST',
        'name': 'Bulk'
      }
  
      # Handle also other kind of users: instance, computer, master
      person = portal.ERP5Site_getAuthenticatedMemberPersonValue()
      if person is not None:
        result_dict['_links']['me'] = {
          "href": default_document_uri_template % {
            "root_url": site_root.absolute_url(),
            "relative_url": person.getRelativeUrl(), 
            "script_id": script.id
          },
  #         '_relative_url': person.getRelativeUrl()
        }
  
    else:
      traversed_document_portal_type = traversed_document.getPortalType()
      if traversed_document_portal_type == "ERP5 Form":
        renderFormDefinition(traversed_document, result_dict)
        REQUEST.set("X-HATEOAS-CACHE", 1)
  
    # Define document action
    if action_dict:
      result_dict['_actions'] = action_dict
  
  
  elif mode == 'search':
    #################################################
    # Portal catalog search
    #################################################
    if REQUEST.other['method'] != "GET":
      response.setStatus(405)
      return ""
  
    if query == "__root__":
      # XXX Hardcoded behaviour to get root object with jIO
      sql_list = [site_root]
  
    elif query == "__portal__":
      # XXX Hardcoded behaviour to get portal object with jIO
      sql_list = [portal]
  
  #     document = site_root
  #     document_result = {
  # #       '_relative_url': site_root.getRelativeUrl(),
  #       '_links': {
  #         'self': {
  #           "href": default_document_uri_template % {
  #             "root_url": site_root.absolute_url(),
  #             "relative_url": document.getRelativeUrl(), 
  #             "script_id": script.id
  #           },
  #         },
  #       }
  #     }
  #     for select in select_list:
  #       document_result[select] = document.getProperty(select, d=None)
  #     result_dict['_embedded'] = {"contents": [document_result]}
    else:
  #     raise NotImplementedError("Unsupported query: %s" % query)
      
  
  #   # XXX
  #   length = len('/%s/' % portal.getId())
  #   # context.log(portal.portal_catalog(full_text=query, limit=limit, src__=1))
  #   context.log(query)
      catalog_kw = {}
      if (default_param_json is not None):
        catalog_kw = json.loads(urlsafe_b64decode(default_param_json))
      if (list_method is None):
        callable_list_method = portal.portal_catalog
      else:
        callable_list_method = getattr(traversed_document, list_method)

      tmp_sort_on = ()
      if sort_on is not None:
        for grain in sort_on:
          if grain != "":
            tmp_sort_on += (tuple([x for x in grain.split(",")]),)

      if query:
        sql_list = callable_list_method(full_text=query, limit=limit, sort_on=tmp_sort_on, **catalog_kw)
      else:
        sql_list = callable_list_method(limit=limit, sort_on=tmp_sort_on, **catalog_kw)

    result_list = []
  
  #   if (select_list is None):
  #     # Only include links
  #     for sql_document in sql_list:
  #       document = sql_document.getObject()
  #       result_list.append({
  #         "href": default_document_uri_template % {
  #           "root_url": site_root.absolute_url(),
  #           "relative_url": document.getRelativeUrl(), 
  #           "script_id": script.id
  #         },
  #       })
  #     result_dict['_links']['contents'] = result_list
  # 
  #   else:
  
    # Cast to list if only one element is provided
    editable_field_dict = {}
    if select_list is None:
      select_list = []
    elif same_type(select_list, ""):
      select_list = [select_list]
  
    if select_list:
      if (form_relative_url is not None):
        listbox_field = portal.restrictedTraverse(form_relative_url)
        listbox_field_id = listbox_field.id
        # XXX Proxy field are not correctly handled in traversed_document of web site
        listbox_form = getattr(traversed_document, listbox_field.aq_parent.id)
        for select in select_list:
          # See Listbox.py getEditableField method
          if listbox_form.has_field("%s_%s" % (listbox_field_id, select), include_disabled=1):
            editable_field_dict[select] = listbox_form.get_field("%s_%s" % (listbox_field_id, select), include_disabled=1)

    # CUSTOMIZATION FOR TRAVEL EXPENSE APP########################
    person = portal.ERP5Site_getAuthenticatedMemberPersonValue()
    for sql_document in sql_list:
      try:
        document = sql_document.getObject()
        # CUSTOMIZATION FOR TRAVEL EXPENSE APP########################
        if getattr(document, 'isVisibleInHtml5AppFlag', None) is not None and not document.isVisibleInHtml5AppFlag():
          continue
        elif document.portal_type.endswith('Record') and document.getSimulationState() == 'cancelled':
          continue
        elif document.portal_type.endswith('Record') and not person in document.getContributorValueList():
	  continue
        ###############################################
      except AttributeError, e:
        # XXX ERP5 Site is not an ERP5 document
        document = sql_document
      document_uid = document.getUid()
      document_result = {
  #       '_relative_url': sql_document.path[length:],
        '_links': {
          'self': {
            "href": default_document_uri_template % {
              "root_url": site_root.absolute_url(),
              # XXX ERP5 Site is not an ERP5 document
              "relative_url": getRealRelativeUrl(document) or document.getId(), 
              "script_id": script.id
            },
          },
        }
      }
      if editable_field_dict:
        document_result['listbox_uid:list'] = {
          'key': "%s_uid:list" % listbox_field_id,
          'value': document_uid
        }
      for select in select_list:
        if editable_field_dict.has_key(select):
          REQUEST.set('cell', document)
  
          if ('default' in editable_field_dict[select].tales):
            tmp_value = None
          else:
            tmp_value = document.getProperty(select, d=None)
  
          property_value = renderField(traversed_document, editable_field_dict[select], form_relative_url,
                                       tmp_value,
                                       key='field_%s_%s' % (editable_field_dict[select].id,
                                       document_uid))
          REQUEST.other.pop('cell', None)
        else:
          property_value = document.getProperty(select, d=None)
        if property_value is not None:
          if same_type(property_value, DateTime()):
            # Serialize DateTime
            property_value = property_value.rfc822()
          document_result[select] = property_value
      result_list.append(document_result)
    result_dict['_embedded'] = {"contents": result_list}
  
    result_dict['_query'] = query
    result_dict['_limit'] = limit
    result_dict['_select_list'] = select_list
  
  elif mode == 'form':
    #################################################
    # Calculate form value
    #################################################
    if REQUEST.other['method'] != "POST":
      response.setStatus(405)
      return ""
  
    renderForm(traversed_document, form, result_dict)
  
  elif mode == 'newContent':
    #################################################
    # Create new document
    #################################################
    if REQUEST.other['method'] != "POST":
      response.setStatus(405)
      return ""
    portal_type = REQUEST.form["portal_type"]
    parent_relative_url = REQUEST.form["parent_relative_url"]
    # First, try to validate the data on a temp document
    parent = portal.restrictedTraverse(parent_relative_url)
    # module = portal.getDefaultModule(portal_type=portal_type)
    document = parent.newContent(
      portal_type=portal_type
    )
    # http://en.wikipedia.org/wiki/Post/Redirect/Get
    response.setStatus(201)
    response.setHeader("X-Location",
      default_document_uri_template % {
        "root_url": site_root.absolute_url(),
        "relative_url": document.getRelativeUrl(),
        "script_id": script.id
      })
    return ''
  
  elif mode == 'bulk':
    #################################################
    # Return multiple documents in one request
    #################################################
    if REQUEST.other['method'] != "POST":
      response.setStatus(405)
      return ""
    result_dict["result_list"] = [calculateHateoas(mode="traverse", **x) for x in json.loads(bulk_list)]
  
  else:
    raise NotImplementedError("Unsupported mode %s" % mode)
  
  return result_dict

response.setHeader('Content-Type', mime_type)
hateoas = calculateHateoas(is_portal=temp_is_portal, is_site_root=temp_is_site_root,
                           traversed_document=temp_traversed_document,
                           REQUEST=REQUEST, response=response, view=view, mode=mode,
                           query=query, select_list=select_list, limit=limit, form=form,
                           restricted=restricted, list_method=list_method,
                           default_param_json=default_param_json,
                           form_relative_url=form_relative_url)
if hateoas == "":
  return hateoas
else:
  return json.dumps(hateoas, indent=2)
