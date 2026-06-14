# -*- coding: utf-8 -*-
{
    'name': 'Sales Order Margin Guard',
    'version': '1.0',
    'summary': 'Automated approval workflow for sales orders with critical profit margins.',
    'sequence': 15,
    'description': """
Sales Order Margin Guard
========================
This module introduces a business logic safety barrier for Sales Orders.
If a sales representative enters item prices that result in a profit margin 
below 15% (compared to the product's cost price), the system automatically:

* Blocks immediate confirmation of the Sales Order.
* Moves the order state into a new 'Waiting Approval' status.
* Restricts confirmation to users within the Sales Manager security group.
* Highlights low-margin quotes in the list view for quick visual identification.
    """,
    'category': 'Sales/Sales',
    'author': 'Sven Wehrend',
    'website': 'https://github.com/wehrend/sale_margin_guard',
    'depends': [
        'base',
        'product',
        'sale',
        'sale_management',
    ],
    'data': [
        'views/sale_order_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}