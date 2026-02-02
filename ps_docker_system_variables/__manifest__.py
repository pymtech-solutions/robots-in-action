# -*- coding: utf-8 -*-
{
    'name': 'Ps Docker System Variables',
    'version': '1.0',
    'summary': 'Set necessary system variables for Docker environment',
    'description': '''
            This module sets the necessary system variables for Docker environment. These variables are essential for the proper functioning of the Odoo Docker installation.
    ''',
    'category': 'Utilities',
    'author': 'Pymtech Solutions',
    'company': 'Pymtech Solutions',
    'maintainer': 'Pymtech Solutions',
    'depends': ['base', 'mail'],
    'data': [
        'data/system_variables_data.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
