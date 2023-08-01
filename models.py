from odoo import tools, models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date,datetime


class AccountMove(models.Model):
    _inherit = "account.move"

    autopay_journal_id = fields.Many2one(
            comodel_name='account.journal',
            string='Autopay Journal',
            domain=[('type','in',['bank','cash'])],
            copy=False
            )
    autopay_payment_id = fields.Many2one(
            'account.payment',
            'Autopay Payment',
            copy=False
            )

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for rec in self:
            if rec.move_type == 'in_invoice' and rec.autopay_journal_id:
                vals_payment = {
                        'partner_id': rec.partner_id.id,
                        'journal_id': rec.autopay_journal_id.id,
                        'date': str(date.today()),
                        'payment_type': 'outbound',
                        'partner_type': 'supplier',
                        'amount': rec.amount_total,
                        'ref': rec.display_name,
                        }
                payment_id = self.env['account.payment'].create(vals_payment)
                payment_id.action_post()
                rec.autopay_payment_id = payment_id.id
                aml_obj = self.env['account.move.line']
                for move_line in rec.line_ids:
                    if move_line.account_id.account_type == 'liability_payable':
                        aml_obj += move_line
                for move_line in payment_id.line_ids:
                    if move_line.account_id.account_type == 'liability_payable':
                        aml_obj += move_line
                aml_obj.reconcile()
        return res
