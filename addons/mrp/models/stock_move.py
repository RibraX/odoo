# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, exceptions, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round
from odoo.addons import decimal_precision as dp


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    workorder_id = fields.Many2one('mrp.workorder', 'Work Order')
    production_id = fields.Many2one('mrp.production', 'Production Order')
    lot_produced_id = fields.Many2one('stock.production.lot', 'Finished Lot')
<<<<<<< HEAD
    lot_produced_qty = fields.Float('Quantity Finished Product', help="Informative, not used in matching")
=======
    lot_produced_qty = fields.Float(
        'Quantity Finished Product', digits=dp.get_precision('Product Unit of Measure'),
        help="Informative, not used in matching")
    quantity = fields.Float('To Do', default=1.0, digits=dp.get_precision('Product Unit of Measure'))
    quantity_done = fields.Float('Done', digits=dp.get_precision('Product Unit of Measure'))
    product_id = fields.Many2one(
        'product.product', 'Product',
        readonly=True, related="move_id.product_id", store=True)
>>>>>>> 24b677a3597beaf0e0509fd09d8f71c7803d8f09
    done_wo = fields.Boolean('Done for Work Order', default=True, help="Technical Field which is False when temporarily filled in in work order")  # TDE FIXME: naming
    done_move = fields.Boolean('Move Done', related='move_id.is_done', store=True)  # TDE FIXME: naming

    def _get_similar_move_lines(self):
        lines = super(StockMoveLine, self)._get_similar_move_lines()
        if self.move_id.production_id:
            finished_moves = self.move_id.production_id.move_finished_ids
            finished_move_lines = finished_moves.mapped('move_line_ids')
            lines |= finished_move_lines.filtered(lambda ml: ml.product_id == self.product_id and (ml.lot_id or ml.lot_name))
        if self.move_id.raw_material_production_id:
            raw_moves = self.move_id.raw_material_production_id.move_raw_ids
            raw_moves_lines = raw_moves.mapped('move_line_ids')
            raw_moves_lines |= self.move_id.active_move_line_ids
            lines |= raw_moves_lines.filtered(lambda ml: ml.product_id == self.product_id and (ml.lot_id or ml.lot_name))
        return lines

    @api.multi
    def write(self, vals):
        for move_line in self:
            if move_line.production_id and 'lot_id' in vals:
                move_line.production_id.move_raw_ids.mapped('move_line_ids')\
                    .filtered(lambda r: r.done_wo and not r.done_move and r.lot_produced_id == move_line.lot_id)\
                    .write({'lot_produced_id': vals['lot_id']})
            production = move_line.move_id.production_id or move_line.move_id.raw_material_production_id
            if production and move_line.state == 'done' and any(field in vals for field in ('lot_id', 'location_id', 'qty_done')):
                move_line._log_message(production, move_line, 'mrp.track_production_move_template', vals)
        return super(StockMoveLine, self).write(vals)


class StockMove(models.Model):
    _inherit = 'stock.move'

    created_production_id = fields.Many2one('mrp.production', 'Created Production Order')
    production_id = fields.Many2one(
        'mrp.production', 'Production Order for finished products')
    raw_material_production_id = fields.Many2one(
        'mrp.production', 'Production Order for raw materials')
    unbuild_id = fields.Many2one(
        'mrp.unbuild', 'Unbuild Order')
    consume_unbuild_id = fields.Many2one(
        'mrp.unbuild', 'Consume Unbuild Order')
    operation_id = fields.Many2one(
        'mrp.routing.workcenter', 'Operation To Consume')  # TDE FIXME: naming
    workorder_id = fields.Many2one(
        'mrp.workorder', 'Work Order To Consume')
    # Quantities to process, in normalized UoMs
<<<<<<< HEAD
    active_move_line_ids = fields.One2many('stock.move.line', 'move_id', domain=[('done_wo', '=', True)], string='Lots')
=======
    quantity_available = fields.Float(
        'Quantity Available', compute="_qty_available",
        digits=dp.get_precision('Product Unit of Measure'))
    quantity_done_store = fields.Float('Quantity done store', digits=0)
    quantity_done = fields.Float(
        'Quantity', compute='_qty_done_compute', inverse='_qty_done_set',
        digits=dp.get_precision('Product Unit of Measure'))
    move_lot_ids = fields.One2many('stock.move.lots', 'move_id', string='Lots')
    active_move_lot_ids = fields.One2many('stock.move.lots', 'move_id', domain=[('done_wo', '=', True)], string='Lots')
>>>>>>> 24b677a3597beaf0e0509fd09d8f71c7803d8f09
    bom_line_id = fields.Many2one('mrp.bom.line', 'BoM Line')
    unit_factor = fields.Float('Unit Factor')
    is_done = fields.Boolean(
        'Done', compute='_compute_is_done',
        store=True,
        help='Technical Field to order moves')
    needs_lots = fields.Boolean('Tracking', compute='_compute_needs_lots')
    order_finished_lot_ids = fields.Many2many('stock.production.lot', compute='_compute_order_finished_lot_ids')
    finished_lots_exist = fields.Boolean('Finished Lots Exist', compute='_compute_order_finished_lot_ids')

    @api.depends('active_move_line_ids.qty_done', 'active_move_line_ids.product_uom_id')
    def _compute_done_quantity(self):
        super(StockMove, self)._compute_done_quantity()

    @api.depends('raw_material_production_id.move_finished_ids.move_line_ids.lot_id')
    def _compute_order_finished_lot_ids(self):
        for move in self:
            if move.raw_material_production_id.move_finished_ids:
                finished_lots_ids = move.raw_material_production_id.move_finished_ids.mapped('move_line_ids.lot_id').ids
                if finished_lots_ids:
                    move.order_finished_lot_ids = finished_lots_ids
                    move.finished_lots_exist = True
                else:
                    move.finished_lots_exist = False

    @api.depends('product_id.tracking')
    def _compute_needs_lots(self):
        for move in self:
<<<<<<< HEAD
            move.needs_lots = move.product_id.tracking != 'none'
=======
            if move.has_tracking != 'none' or move.sudo().move_lot_ids.mapped('lot_id'):
                move.quantity_done = sum(move.move_lot_ids.filtered(lambda x: x.done_wo).mapped('quantity_done')) #TODO: change with active_move_lot_ids?
            else:
                move.quantity_done = move.quantity_done_store
>>>>>>> 24b677a3597beaf0e0509fd09d8f71c7803d8f09

    @api.depends('raw_material_production_id.is_locked', 'picking_id.is_locked')
    def _compute_is_locked(self):
        super(StockMove, self)._compute_is_locked()
        for move in self:
            if move.raw_material_production_id:
                move.is_locked = move.raw_material_production_id.is_locked

    def _get_move_lines(self):
        self.ensure_one()
        if self.raw_material_production_id:
            return self.active_move_line_ids
        else:
            return super(StockMove, self)._get_move_lines()

    @api.depends('state')
    def _compute_is_done(self):
        for move in self:
            move.is_done = (move.state in ('done', 'cancel'))

    @api.model
    def default_get(self, fields_list):
        defaults = super(StockMove, self).default_get(fields_list)
        if self.env.context.get('default_raw_material_production_id'):
            production_id = self.env['mrp.production'].browse(self.env.context['default_raw_material_production_id'])
            if production_id.state == 'done':
                defaults['state'] = 'done'
                defaults['product_uom_qty'] = 0.0
                defaults['additional'] = True
        return defaults

    def _action_assign(self):
        res = super(StockMove, self)._action_assign()
        for move in self.filtered(lambda x: x.production_id or x.raw_material_production_id):
            if move.move_line_ids:
                move.move_line_ids.write({'production_id': move.raw_material_production_id.id,
                                               'workorder_id': move.workorder_id.id,})
        return res

    def _action_cancel(self):
        if any(move.quantity_done and (move.raw_material_production_id or move.production_id) for move in self):
            raise exceptions.UserError(_('You cannot cancel a manufacturing order if you have already consumed material.\
             If you want to cancel this MO, please change the consumed quantities to 0.'))
        return super(StockMove, self)._action_cancel()

<<<<<<< HEAD
    def _action_confirm(self, merge=True):
=======
    @api.multi
    def create_lots(self):
        lots = self.env['stock.move.lots']
        for move in self:
            unlink_move_lots = move.move_lot_ids.filtered(lambda x : (x.quantity_done == 0) and x.done_wo)
            unlink_move_lots.sudo().unlink()
            group_new_quant = {}
            old_move_lot = {}
            for movelot in move.move_lot_ids:
                key = (movelot.lot_id.id or False)
                old_move_lot.setdefault(key, []).append(movelot)
            for quant in move.reserved_quant_ids:
                key = (quant.lot_id.id or False)
                quantity = move.product_id.uom_id._compute_quantity(quant.qty, move.product_uom)
                if group_new_quant.get(key):
                    group_new_quant[key] += quantity
                else:
                    group_new_quant[key] = quantity
            for key in group_new_quant:
                quantity = group_new_quant[key]
                if old_move_lot.get(key):
                    if old_move_lot[key][0].quantity == quantity:
                        continue
                    else:
                        old_move_lot[key][0].quantity = quantity
                else:
                    vals = {
                        'move_id': move.id,
                        'product_id': move.product_id.id,
                        'workorder_id': move.workorder_id.id,
                        'production_id': move.raw_material_production_id.id,
                        'quantity': quantity,
                        'lot_id': key,
                    }
                    lots.create(vals)
        return True

    @api.multi
    def _create_extra_move(self):
        ''' Creates an extra move if necessary depending on extra quantities than foreseen or extra moves'''
        self.ensure_one()
        quantity_to_split = 0
        uom_qty_to_split = 0
        extra_move = self.env['stock.move']
        rounding = self.product_uom.rounding
        link_procurement = False
        # If more produced than the procurement linked, you should create an extra move
        if self.procurement_id and self.production_id and float_compare(self.production_id.qty_produced, self.procurement_id.product_qty, precision_rounding=rounding) > 0:
            done_moves_total = sum(self.production_id.move_finished_ids.filtered(lambda x: x.product_id == self.product_id and x.state == 'done').mapped('product_uom_qty'))
            # If you depassed the quantity before, you don't need to split anymore, but adapt the quantities
            if float_compare(done_moves_total, self.procurement_id.product_qty, precision_rounding=rounding) >= 0:
                quantity_to_split = 0
                if float_compare(self.product_uom_qty, self.quantity_done, precision_rounding=rounding) < 0:
                    self.product_uom_qty = self.quantity_done #TODO: could change qty on move_dest_id also (in case of 2-step in/out)
            else:
                quantity_to_split = done_moves_total + self.quantity_done - self.procurement_id.product_qty
                uom_qty_to_split = self.product_uom_qty - (self.quantity_done - quantity_to_split)#self.product_uom_qty - (self.procurement_id.product_qty + done_moves_total)
                if float_compare(uom_qty_to_split, quantity_to_split, precision_rounding=rounding) < 0:
                    uom_qty_to_split = quantity_to_split
                self.product_uom_qty = self.quantity_done - quantity_to_split
        # You split also simply  when the quantity done is bigger than foreseen
        elif float_compare(self.quantity_done, self.product_uom_qty, precision_rounding=rounding) > 0:
            quantity_to_split = self.quantity_done - self.product_uom_qty
            uom_qty_to_split = quantity_to_split # + no need to change existing self.product_uom_qty 
            link_procurement = True
        if quantity_to_split:
            extra_move = self.copy(default={'quantity_done': quantity_to_split, 'product_uom_qty': uom_qty_to_split, 'production_id': self.production_id.id, 
                                            'raw_material_production_id': self.raw_material_production_id.id, 
                                            'procurement_id': link_procurement and self.procurement_id.id or False})
            extra_move.action_confirm()
            if self.has_tracking != 'none':
                qty_todo = self.quantity_done - quantity_to_split
                for movelot in self.move_lot_ids.filtered(lambda x: x.done_wo):
                    if movelot.quantity_done and movelot.done_wo:
                        if float_compare(qty_todo, movelot.quantity_done, precision_rounding=rounding) >= 0:
                            qty_todo -= movelot.quantity_done
                        elif float_compare(qty_todo, 0, precision_rounding=rounding) > 0:
                            #split
                            remaining = movelot.quantity_done - qty_todo
                            movelot.quantity_done = qty_todo
                            movelot.copy(default={'move_id': extra_move.id, 'quantity_done': remaining})
                            qty_todo = 0
                        else:
                            movelot.move_id = extra_move.id
            else:
                self.quantity_done -= quantity_to_split
        return extra_move

    @api.multi
    def move_validate(self):
        ''' Validate moves based on a production order. '''
        moves = self._filter_closed_moves()
        quant_obj = self.env['stock.quant']
        moves_todo = self.env['stock.move']
        moves_to_unreserve = self.env['stock.move']
        # Create extra moves where necessary
        for move in moves:
            # Here, the `quantity_done` was already rounded to the product UOM by the `do_produce` wizard. However,
            # it is possible that the user changed the value before posting the inventory by a value that should be
            # rounded according to the move's UOM. In this specific case, we chose to round up the value, because it
            # is what is expected by the user (if i consumed/produced a little more, the whole UOM unit should be
            # consumed/produced and the moves are split correctly).
            rounding = move.product_uom.rounding
            move.quantity_done = float_round(move.quantity_done, precision_rounding=rounding, rounding_method ='UP')
            if move.quantity_done <= 0:
                continue
            moves_todo |= move
            moves_todo |= move._create_extra_move()
        # Split moves where necessary and move quants
        for move in moves_todo:
            rounding = move.product_uom.rounding
            if float_compare(move.quantity_done, move.product_uom_qty, precision_rounding=rounding) < 0:
                # Need to do some kind of conversion here
                qty_split = move.product_uom._compute_quantity(move.product_uom_qty - move.quantity_done, move.product_id.uom_id)
                new_move = move.split(qty_split)
                # If you were already putting stock.move.lots on the next one in the work order, transfer those to the new move
                move.move_lot_ids.filtered(lambda x: not x.done_wo or x.quantity_done == 0.0).write({'move_id': new_move})
                self.browse(new_move).quantity_done = 0.0
            main_domain = [('qty', '>', 0)]
            preferred_domain = [('reservation_id', '=', move.id)]
            fallback_domain = [('reservation_id', '=', False)]
            fallback_domain2 = ['&', ('reservation_id', '!=', move.id), ('reservation_id', '!=', False)]
            preferred_domain_list = [preferred_domain] + [fallback_domain] + [fallback_domain2]
            if move.has_tracking == 'none':
                quants = quant_obj.quants_get_preferred_domain(move.product_qty, move, domain=main_domain, preferred_domain_list=preferred_domain_list)
                self.env['stock.quant'].quants_move(quants, move, move.location_dest_id, owner_id=move.restrict_partner_id.id)
            else:
                for movelot in move.active_move_lot_ids:
                    if float_compare(movelot.quantity_done, 0, precision_rounding=rounding) > 0:
                        if not movelot.lot_id:
                            raise UserError(_('You need to supply a lot/serial number.'))
                        qty = move.product_uom._compute_quantity(movelot.quantity_done, move.product_id.uom_id)
                        quants = quant_obj.quants_get_preferred_domain(qty, move, lot_id=movelot.lot_id.id, domain=main_domain, preferred_domain_list=preferred_domain_list)
                        self.env['stock.quant'].quants_move(quants, move, move.location_dest_id, lot_id = movelot.lot_id.id, owner_id=move.restrict_partner_id.id)
            moves_to_unreserve |= move
            # Next move in production order
            if move.move_dest_id and move.move_dest_id.state not in ('done', 'cancel'):
                move.move_dest_id.action_assign()
        moves_to_unreserve.quants_unreserve()
        moves_todo.write({'state': 'done', 'date': fields.Datetime.now()})
        return moves_todo

    @api.multi
    def action_done(self):
        production_moves = self.filtered(lambda move: (move.production_id or move.raw_material_production_id) and not move.scrapped)
        production_moves.move_validate()
        return super(StockMove, self-production_moves).action_done()

    @api.multi
    def split_move_lot(self):
        ctx = dict(self.env.context)
        self.ensure_one()
        view = self.env.ref('mrp.view_stock_move_lots')
        serial = (self.has_tracking == 'serial')
        only_create = False  # Check picking type in theory
        show_reserved = any([x for x in self.move_lot_ids if x.quantity > 0.0])
        ctx.update({
            'serial': serial,
            'only_create': only_create,
            'create_lots': True,
            'state_done': self.is_done,
            'show_reserved': show_reserved,
        })
        if ctx.get('w_production'):
            action = self.env.ref('mrp.act_mrp_product_produce').read()[0]
            action['context'] = ctx
            return action
        result = {
            'name': _('Register Lots'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.move',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': ctx,
        }
        return result

    @api.multi
    def save(self):
        return True

    @api.multi
    def action_confirm(self):
>>>>>>> 24b677a3597beaf0e0509fd09d8f71c7803d8f09
        moves = self.env['stock.move']
        for move in self:
            moves |= move.action_explode()
        # we go further with the list of ids potentially changed by action_explode
        return super(StockMove, moves)._action_confirm(merge=merge)

    def action_explode(self):
        """ Explodes pickings """
        # in order to explode a move, we must have a picking_type_id on that move because otherwise the move
        # won't be assigned to a picking and it would be weird to explode a move into several if they aren't
        # all grouped in the same picking.
        if not self.picking_type_id:
            return self
        bom = self.env['mrp.bom'].sudo()._bom_find(product=self.product_id, company_id=self.company_id.id)
        if not bom or bom.type != 'phantom':
            return self
        phantom_moves = self.env['stock.move']
        processed_moves = self.env['stock.move']
        factor = self.product_uom._compute_quantity(self.product_uom_qty, bom.product_uom_id) / bom.product_qty
        boms, lines = bom.sudo().explode(self.product_id, factor, picking_type=bom.picking_type_id)
        for bom_line, line_data in lines:
            phantom_moves += self._generate_move_phantom(bom_line, line_data['qty'])

        for new_move in phantom_moves:
            processed_moves |= new_move.action_explode()
#         if not self.split_from and self.procurement_id:
#             # Check if procurements have been made to wait for
#             moves = self.procurement_id.move_ids
#             if len(moves) == 1:
#                 self.procurement_id.write({'state': 'done'})
        if processed_moves and self.state == 'assigned':
            # Set the state of resulting moves according to 'assigned' as the original move is assigned
            processed_moves.write({'state': 'assigned'})
        # delete the move with original product which is not relevant anymore
        self.sudo().unlink()
        return processed_moves

    def _generate_move_phantom(self, bom_line, quantity):
        if bom_line.product_id.type in ['product', 'consu']:
            return self.copy(default={
                'picking_id': self.picking_id.id if self.picking_id else False,
                'product_id': bom_line.product_id.id,
                'product_uom': bom_line.product_uom_id.id,
                'product_uom_qty': quantity,
                'state': 'draft',  # will be confirmed below
                'name': self.name,
            })
        return self.env['stock.move']

    def _generate_consumed_move_line(self, qty_to_add, final_lot, lot=False):
        if lot:
            ml = self.move_line_ids.filtered(lambda ml: ml.lot_id == lot and not ml.lot_produced_id)
        else:
            ml = self.move_line_ids.filtered(lambda ml: not ml.lot_id and not ml.lot_produced_id)
        if ml:
            new_quantity_done = (ml.qty_done + qty_to_add)
            if new_quantity_done >= ml.product_uom_qty:
                ml.write({'qty_done': new_quantity_done, 'lot_produced_id': final_lot.id})
            else:
                new_qty_reserved = ml.product_uom_qty - new_quantity_done
                default = {'product_uom_qty': new_quantity_done,
                           'qty_done': new_quantity_done,
                           'lot_produced_id': final_lot.id}
                ml.copy(default=default)
                ml.with_context(bypass_reservation_update=True).write({'product_uom_qty': new_qty_reserved, 'qty_done': 0})
        else:
            vals = {
                'move_id': self.id,
                'product_id': self.product_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'product_uom_qty': 0,
                'product_uom_id': self.product_uom.id,
                'qty_done': qty_to_add,
                'lot_produced_id': final_lot.id,
            }
            if lot:
                vals.update({'lot_id': lot.id})
            self.env['stock.move.line'].create(vals)


class PushedFlow(models.Model):
    _inherit = "stock.location.path"

    def _prepare_move_copy_values(self, move_to_copy, new_date):
        new_move_vals = super(PushedFlow, self)._prepare_move_copy_values(move_to_copy, new_date)
        new_move_vals['production_id'] = False

        return new_move_vals
