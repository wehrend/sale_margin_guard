# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

class TestMarginGuard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestMarginGuard, cls).setUpClass()
        
        # 1. Create test users
        cls.sales_manager = cls.env['res.users'].create({
            'name': 'Sales Manager',
            'login': 'manager',
            'email': 'manager@test.com',
        })
        cls.sales_manager.write({
            'group_ids': [
                (4, cls.env.ref('sales_team.group_sale_manager').id),
                (3, cls.env.ref('sales_team.group_sale_salesman').id),
            ]
        })
        
        cls.sales_rep = cls.env['res.users'].create({
            'name': 'Sales Rep',
            'login': 'rep',
            'email': 'rep@test.com',
        })
        cls.sales_rep.write({
            'group_ids': [
                (4, cls.env.ref('sales_team.group_sale_salesman').id),
                (3, cls.env.ref('sales_team.group_sale_manager').id),
            ]
        })

        # 2. Create test customer and test product
        cls.partner = cls.env['res.partner'].create({'name': 'Test B2B Customer'})
        
        # Product costs 100 EUR to purchase (standard_price)
        cls.product = cls.env['product.product'].create({
            'name': 'Test Premium Gadget',
            'standard_price': 100.0,
            'list_price': 150.0,
            'type': 'consu',
        })

        # 3. Set default threshold in system settings to 15%
        cls.env['ir.config_parameter'].sudo().set_param('sale_margin_guard.min_sales_margin', 15.0)

    def test_01_margin_above_threshold_confirms_immediately(self):
        """ Scenario 1: Margin is 20% (sale price 125, cost 100).
            The order must be confirmed immediately (state = sale). """
        order = self.env['sale.order'].with_user(self.sales_rep).create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 125.0, # Margin = (125-100)/125 = 20%
            })]
        })

        order._compute_margin_alert()
        self.assertFalse(order.margin_alert, "At 20% margin there should be no alert.")

        order.action_confirm()
        self.assertEqual(order.state, 'sale', "Order with sufficient margin should be confirmed directly.")

    def test_02_margin_below_threshold_blocks_and_awaits_approval(self):
        """ Scenario 2: Margin is 9% (sale price 110, cost 100).
            A regular salesperson must not confirm; state must become 'to_approve'. """
        order = self.env['sale.order'].with_user(self.sales_rep).create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 110.0, # Margin = (110-100)/110 = 9.09%
            })]
        })

        order._compute_margin_alert()
        self.assertTrue(order.margin_alert, "Below 15% margin the alert must trigger.")

        order.action_confirm()
        self.assertEqual(order.state, 'to_approve', "State must block and switch to 'Waiting Approval'.")

        # Manager steps in and approves
        order.with_user(self.sales_manager).action_approve_margin()
        self.assertEqual(order.state, 'sale', "The manager must be able to set the state to 'sale'.")

    def test_03_dynamic_configuration_change(self):
        """ Scenario 3: We raise the limit in settings to 30%.
            A price of 125 (previously allowed) must now be blocked. """
        self.env['ir.config_parameter'].sudo().set_param('sale_margin_guard.min_sales_margin', 30.0)

        order = self.env['sale.order'].with_user(self.sales_rep).create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 125.0, # Margin is 20%, but limit is now 30%!
            })]
        })

        order._compute_margin_alert()
        self.assertTrue(order.margin_alert, "With the limit raised to 30%, a 20% margin must trigger the alert.")
        
        order.action_confirm()
        self.assertEqual(order.state, 'to_approve', "Due to the raised limit this order must now be blocked.")