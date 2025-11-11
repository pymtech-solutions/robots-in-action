# -*- coding: utf-8 -*-
{
    'name': 'Ps Clickable Tags',
    'version': '1.0',
    'summary': 'Brief description of the module',
    'description': '''
        Detailed description of the module
    ''',
    'category': 'Uncategorized',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'mail'],
    'data': [
    ],

    'assets': {
        'web.assets_backend':
            [
                'ps_clickable_tags/static/src/js/many2many_tags_fields.js',
            ]
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}