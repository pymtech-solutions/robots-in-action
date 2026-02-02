# -*- coding: utf-8 -*-
{
    'name': 'Ps School Ria',
    'version': '1.0',
    'summary': 'Brief description of the module',
    'description': '''
        Detailed description of the module
    ''',
    'category': 'Uncategorized',
    'author': 'Pymtech solutions',
    'company': 'Pymtech solutions',
    'maintainer': 'Pymtech solutions',
    'depends': ['base', 'hr', 'contacts', 'product', 'mail', 'calendar', 'web', 'ps_colegio'],
    'data': [
        'security/ir.model.access.csv',
        'security/school_security.xml',
        'report/school_grade_report.xml',
        'views/school_grade_views.xml',
		'views/res_partner_views.xml',
],
    'assets': {
        'web.report_assets_common': [
            'ps_school_ria/static/img/robots.png',
        ],
    },

    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}