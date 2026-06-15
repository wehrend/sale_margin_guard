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
    )

    def _get_min_margin(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            'sale_margin_guard.min_sales_margin', default=15.0
        )
        return float(value) / 100.0

    def _has_low_margin(self):
        """Returns True if any order line is below the minimum margin threshold."""
        min_margin = self._get_min_margin()
        for line in self.order_line:
            if line.product_id and line.price_unit > 0:
                cost = line.product_id.standard_price
                margin = (line.price_unit - cost) / line.price_unit
                if margin < min_margin:
                    return True
        return False

    @api.depends('order_line.price_unit', 'order_line.product_id')
    def _compute_margin_alert(self):
        for order in self:
            order.margin_alert = order._has_low_margin()

    def action_confirm(self):
        if self._has_low_margin():
            if not self.env.user.has_group('sales_team.group_sale_manager'):
                self.write({'state': 'to_approve'})
                self.message_post(body=_("This order has been blocked due to a low margin. It requires Manager Approval."))
                return False

        return super(SaleOrder, self).action_confirm()

    def action_approve_margin(self):
        """Allow managers manual approval."""
        self.ensure_one()
        if not self.env.user.has_group('sales_team.group_sale_manager'):
            raise UserError(_("Only Sales Managers can approve this order."))

        self.message_post(body=_("Margin manually approved by %s.") % self.env.user.name)
        # Temporarily reset to draft so action_confirm can run its full logic
        # (stock moves, confirmation email, etc.) — not a visible state change
        self.write({'state': 'draft'})
        return super(SaleOrder, self).action_confirm()