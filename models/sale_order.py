# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # new state for approval process
    state = fields.Selection(selection_add=[
        ('to_approve', 'Waiting Approval')
    ], ondelete={'to_approve': 'set default'})

    margin_alert = fields.Boolean(
        string="Low Margin Alert", 
        compute="_compute_margin_alert", 
        store=True
    )

    @api.depends('order_line.price_unit', 'order_line.product_id')
    def _compute_margin_alert(self):
        for order in self:
            alert = False
            for line in order.order_line:
                # block division by zero and check only real products
                if line.product_id and line.price_unit > 0:
                    # fetch standard price from product
                    cost = line.product_id.standard_price
                    margin = (line.price_unit - cost) / line.price_unit
                    
                    if margin < 0.15:
                        alert = True
                        break
            order.margin_alert = alert

    def action_confirm(self):
        if self.margin_alert and self.state != 'to_approve':
            if not self.env.user.has_group('sales_team.group_sale_manager'):
                self.write({'state': 'to_approve'})
                self.message_post(body=_("This order has been blocked for confirmation due to a low margin (&lt; 15%). It requires Manager Approval."))
                return False
                
        return super(SaleOrder, self).action_confirm()

    def action_approve_margin(self):
        """ Allow managers manuall approval"""
        self.ensure_one()
        if not self.env.user.has_group('sales_team.group_sale_manager'):
            raise UserError(_("Only Sales Managers can approve this order."))
        
        self.message_post(body=_("Margin manually approved by %s.") % self.env.user.name)
        return super(SaleOrder, self).action_confirm()