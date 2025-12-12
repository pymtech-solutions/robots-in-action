# -*- coding: utf-8 -*-
{
  "name": "Ps Floating Button",
  "version": '1.0',
  "category": "Tools",
  'summary': 'Button that will redirect to any url',
  'description': '''
 Button that will redirect to any url 
  ''',
  'author': 'Pymtech Solutions',
  'company': 'Pymtech Solutions',
  'maintainer': 'Pymtech Solutions',
  'website': '',
  "depends": ["web", "base", "mail"],
  "data": [		"views/res_config_settings_views.xml",
],
  "demo": [
  ],
  "assets": {
      'web.assets_backend': [
          'ps_floating_button/static/src/js/button.js',
          'ps_floating_button/static/src/xml/button.xml',
      ]
  },
  "license": "LGPL-3",
  "installable": True,
  "auto_install": False,
  "application": True
}