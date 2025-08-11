import json
import datetime
from odoo import http, fields
from odoo.http import request

import logging

_logger = logging.getLogger(__name__)

class PaymentRegistrationController(http.Controller):

    @http.route('/api/payment/verify/<token>', methods=['PUT'], type='http', auth='none', cors="*", csrf=False)
    def api_get_paydunya_by_token(self, token, **kw):
        """
        API unifiée pour vérifier et traiter les paiements PayDunya
        Utilise la méthode unifiée d'enregistrement de paiement avec factures d'acompte
        """

        try:
            # Parse request data
            data = json.loads(request.httprequest.data)
            url_facture = data.get('url_facture')
            customer_name = data.get('customer_name')
            customer_email = data.get('customer_email')
            customer_phone = data.get('customer_phone')
            token_status = data.get('token_status')
            payment_state = data.get('payment_state')
            payment_date = datetime.datetime.now()
            
            # Ensure we have admin privileges
            user = request.env['res.users'].sudo().browse(request.env.uid)
            if not user or user._is_public():
                admin_user = request.env.ref('base.user_admin')
                request.env = request.env(user=admin_user.id)
            
            # Find payment details
            payment_details = request.env['payment.details'].sudo().search([
                ('payment_token', '=', token)
            ], limit=1)
            
            if not payment_details:
                return self._make_response({'message': 'Paiement non trouvé'}, 404)
            
            # Get order and validate
            order = request.env['sale.order'].sudo().browse(payment_details.order_id)
            if not order.exists():
                return self._make_response({'message': 'Commande non trouvée'}, 404)
            
            # Check if payment already processed
            if payment_details.token_status and payment_details.payment_state == "completed":
                return self._make_response(self._order_to_dict(order), 200)
            
            # Validate payment state
            if payment_details.token_status or payment_state != "completed":
                return self._make_response({'message': 'Paiement non valide'}, 400)
            
            # Get required objects
            partner = order.partner_id
            company = request.env['res.company'].sudo().browse(1)
            total_amount = payment_details.amount
            
            # Calculate percentage for advance invoice
            percentage = (total_amount / order.amount_total) * 100 if order.amount_total > 0 else 100
            
            # Update order state
            order.write({'state': 'sale'})
            
            # Generate invoice URL
            facture_url = f"https://paydunya.com/checkout/receipt/{token}"
            
            # Process payment based on order type
            payment_result = None
            order_type = getattr(order, 'type_sale', 'order')
            
            
            if order_type == "order":
                if order.amount_residual <= 0:
                    payment_result = {'success': True, 'message': 'Commande déjà payée'}
                elif hasattr(order, 'advance_payment_status') and order.advance_payment_status == 'paid':
                    payment_result = {'success': True, 'message': 'Paiement déjà effectué'}
                else:
                    # Créer une facture d'acompte
                    invoice = self._create_advance_invoice(order, percentage)
                    if not invoice:
                        return self._make_response({'message': 'Erreur lors de la création de la facture d\'acompte'}, 400)
                    # Process payment
                    # payment_result = self._process_payment(order, invoice, total_amount, company)
                    payment_details.write({
                        'acompte_id' : invoice.id,
                    })
                    
            elif order_type == "creditorder":
                if order.amount_residual <= 0:
                    payment_result = {'success': True, 'message': 'Commande crédit déjà payée'}
                else:
                    # Créer une facture d'acompte pour commande crédit
                    invoice = self._create_advance_invoice(order, percentage)
                    if not invoice:
                        return self._make_response({'message': 'Erreur lors de la création de la facture d\'acompte'}, 400)
                    
                    payment_details.write({
                        'acompte_id' : invoice.id,
                    })
                    

                    # Process payment
                    # payment_result = self._process_payment(order, invoice, total_amount, company)
            
            # Vérifier le résultat du paiement
           
            
            # Update payment details
            payment_details.write({
                'token_status': True,
                'url_facture': url_facture or facture_url,
                'customer_name': customer_name,
                'customer_email': customer_email,
                'customer_phone': customer_phone,
                'payment_date': payment_date,
                'payment_state': "completed"
            })
            
            # Commit the transaction
            request.env.cr.commit()
            
            # Préparer la réponse avec les détails du paiement
            response_data = self._order_to_dict(order)
            # if payment_result.get('payment_id'):
            #     response_data['payment_details'] = {
            #         'payment_id': payment_result['payment_id'],
            #         'invoice_id': payment_result.get('invoice_id'),
            #         'amount': payment_result.get('amount', total_amount),
            #         'percentage': round(percentage, 2),
            #         'message': payment_result.get('message')
            #     }
            
            return self._make_response(response_data, 200)
            
        except ValueError as ve:
            request.env.cr.rollback()
            return self._make_response({'message': str(ve)}, 400)
            
        except Exception as e:
            _logger.exception("PayDunya payment processing error: %s", str(e))
            request.env.cr.rollback()
            return self._make_response({
                'message': 'Erreur interne du serveur',
                'error': str(e)
            }, 400)

    def _create_advance_invoice(self, order, percentage):
        """
        Crée une facture d'acompte en utilisant l'assistant Odoo
        
        Args:
            order: Objet sale.order
            percentage: Pourcentage de l'acompte
        
        Returns:
            account.move: Facture d'acompte créée
        """
        try:
            # # Vérifier s'il existe déjà une facture d'acompte pour ce pourcentage
            # existing_advance_invoice = order.invoice_ids.filtered(
            #     lambda inv: inv.state == 'posted' and 
            #                hasattr(inv, 'is_advance_invoice') and 
            #                inv.is_advance_invoice and 
            #                inv.payment_state != 'paid'
            # )
            
            # if existing_advance_invoice:
            #     return existing_advance_invoice[0]

            # S'assurer que la commande est confirmée
            if order.state not in ['sale', 'done']:
                order.action_confirm()

            # Définir le contexte avec les commandes sélectionnées AVANT de créer l'assistant
            context = {
                'active_ids': [order.id],
                'active_model': 'sale.order',
                'active_id': order.id,
                'default_advance_payment_method': 'percentage',
            }
            
            # Créer l'assistant de facture d'acompte avec le contexte approprié
            advance_payment_wizard = request.env['sale.advance.payment.inv'].sudo().with_context(context).create({
                'advance_payment_method': 'percentage',  # Méthode par pourcentage
                'amount': percentage,  # Pourcentage de l'acompte
            })
            
            # Vérifier que l'assistant a bien récupéré la commande
            if not advance_payment_wizard.sale_order_ids:
                # Forcer l'assignation de la commande si elle n'est pas automatiquement détectée
                advance_payment_wizard.sale_order_ids = [(6, 0, [order.id])]
            
            # Vérifier à nouveau
            if not advance_payment_wizard.sale_order_ids:
                _logger.error("Impossible d'assigner la commande %s à l'assistant d'acompte", order.name)
                return None
            
            # Créer la facture d'acompte
            result = advance_payment_wizard.create_invoices()
            
            # Récupérer la facture créée
            if isinstance(result, dict) and 'res_id' in result:
                invoice_id = result['res_id']
                invoice = request.env['account.move'].sudo().browse(invoice_id)
            else:
                # Chercher la dernière facture créée pour cette commande
                invoice = order.invoice_ids.filtered(
                    lambda inv: inv.state == 'draft'
                ).sorted('create_date', reverse=True)[:1]
            
            if invoice:
                # Valider la facture si elle n'est pas déjà validée
                if invoice.state == 'draft':
                    invoice.action_post()
                _logger.info("Facture d'acompte créée: %s pour commande %s (%.2f%%)", 
                           invoice.name, order.name, percentage)
                return invoice
            else:
                _logger.error("Impossible de créer la facture d'acompte pour la commande %s", order.name)
                return None

        except Exception as e:
            _logger.exception("Erreur lors de la création de la facture d'acompte: %s", str(e))
            # Fallback: créer une facture d'acompte manuellement
            return self._create_manual_advance_invoice(order, percentage)
        

    def _get_advance_account(self):
        """
        Récupère le compte comptable pour les acomptes
        
        Returns:
            account.account: Compte d'acompte
        """
        try:
            # Chercher le compte d'acompte client (généralement 419000 ou similaire)
            advance_account = request.env['account.account'].sudo().search([
                ('code', 'like', '419%'),  # Compte d'acompte client
                ('company_id', '=', request.env.company.id)
            ], limit=1)
            
            if not advance_account:
                # Fallback: chercher un compte de type "current_liabilities"
                advance_account = request.env['account.account'].sudo().search([
                    ('account_type', '=', 'current_liabilities'),
                    ('company_id', '=', request.env.company.id)
                ], limit=1)
            
            if not advance_account:
                # Dernier recours: utiliser le compte de revenus par défaut
                advance_account = request.env['account.account'].sudo().search([
                    ('account_type', '=', 'income'),
                    ('company_id', '=', request.env.company.id)
                ], limit=1)
            
            return advance_account
            
        except Exception as e:
            _logger.exception("Erreur lors de la récupération du compte d'acompte: %s", str(e))
            return request.env['account.account'].sudo().search([
                ('company_id', '=', request.env.company.id)
            ], limit=1)

    def _get_advance_product(self):
        """
        Récupère ou crée le produit pour les acomptes
        
        Returns:
            product.product: Produit d'acompte
        """
        try:
            # Chercher le produit d'acompte existant
            advance_product = request.env['product.product'].sudo().search([
                ('name', 'ilike', 'acompte'),
                ('type', '=', 'service')
            ], limit=1)
            
            if not advance_product:
                # Créer le produit d'acompte s'il n'existe pas
                advance_product = request.env['product.product'].sudo().create({
                    'name': 'Acompte',
                    'type': 'service',
                    'invoice_policy': 'order',
                    'list_price': 0.0,
                    'taxes_id': [(6, 0, [])],  # Pas de taxes sur les acomptes
                    'property_account_income_id': self._get_advance_account().id,
                })
                _logger.info("Produit d'acompte créé: %s", advance_product.name)
            
            return advance_product
            
        except Exception as e:
            _logger.exception("Erreur lors de la récupération du produit d'acompte: %s", str(e))
            # Retourner un produit par défaut en cas d'erreur
            return request.env['product.product'].sudo().search([], limit=1)

    def _process_payment(self, order, invoice, amount, company):
        """
        Traite le paiement pour la facture d'acompte
        
        Args:
            order: Commande de vente
            invoice: Facture d'acompte
            amount: Montant du paiement
            company: Société
            
        Returns:
            dict: Résultat du traitement
        """
        try:
            # Récupérer le journal de paiement
            journal = request.env['account.journal'].sudo().search([
                ('code', '=', 'CSH1'), 
                ('company_id', '=', company.id)
            ], limit=1)

            if not journal:
                journal = request.env['account.journal'].sudo().search([
                    ('type', 'in', ['cash', 'bank']),
                    ('company_id', '=', company.id)
                ], limit=1)

            payment_method_line = request.env['account.payment.method.line'].sudo().search([
                ('journal_id', '=', journal.id),
                ('payment_method_id.payment_type', '=', 'inbound')
            ], limit=1)
            
            # Enregistrer le paiement
            payment = self._register_payment(order, invoice, amount, journal.id, payment_method_line.id)
            
            if not payment:
                return {'success': False, 'error': 'Erreur lors de l\'enregistrement du paiement'}
            
            # Réconcilier le paiement avec la facture
            # self._reconcile_payment_with_invoice(payment, invoice)
            
            return {
                'success': True,
                'payment_id': payment.id,
                'invoice_id': invoice.id,
                'amount': amount,
                'message': 'Paiement d\'acompte enregistré avec succès'
            }
            
        except Exception as e:
            _logger.exception("Erreur lors du traitement du paiement: %s", str(e))
            return {'success': False, 'error': str(e)}

    def _reconcile_payment_with_invoice(self, payment, invoice):
        """
        Réconcilie le paiement avec la facture
        
        Args:
            payment: Objet account.payment
            invoice: Objet account.move
        """
        try:
            # Récupérer les lignes à réconcilier
            invoice_lines = invoice.line_ids.filtered(
                lambda line: line.account_id.account_type == 'asset_receivable' and not line.reconciled
            )
            # Si la version d'Odoo est antérieure à 15.0, utiliser account_internal_type au lieu de account_type
            if not invoice_lines:
                invoice_lines = invoice.line_ids.filtered(
                    lambda line: line.account_id.internal_type == 'receivable' and not line.reconciled
                )
            
            payment_lines = payment.move_id.line_ids.filtered(
                lambda line: line.account_id.account_type == 'asset_receivable'
            )
            # Si la version d'Odoo est antérieure à 15.0, utiliser account_internal_type au lieu de account_type
            if not payment_lines:
                payment_lines = payment.move_id.line_ids.filtered(
                    lambda line: line.account_id.internal_type == 'receivable'
                )
            # Réconcilier
            lines_to_reconcile = invoice_lines + payment_lines
            if lines_to_reconcile:
                lines_to_reconcile.reconcile()
                _logger.info("Paiement %s réconcilié avec facture d'acompte %s", payment.name, invoice.name)
            else:
                _logger.warning("Aucune ligne à réconcilier trouvée pour le paiement %s et la facture %s", 
                        payment.name, invoice.name)
                
        except Exception as e:
            _logger.exception("Erreur lors de la réconciliation du paiement: %s", str(e))
            return None

    def _register_payment(self, order, invoice, amount, journal_id, payment_method_line_id=None):
        """
        Enregistre un paiement sur la facture.
        
        Args:
            order: Commande de vente
            invoice: objet account.move
            amount: montant du paiement
            journal_id: ID du journal (ex: banque)
            
        Returns:
            account.payment
        """
        try:
            payment_obj = request.env['account.payment'].create({
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': invoice.partner_id.id,
                'amount': amount,
                'journal_id': journal_id,
                'payment_method_line_id': payment_method_line_id or request.env['account.payment.method.line'].search([('name', '=', 'Manual'), ('payment_method_id.payment_type', '=', 'inbound')], limit=1).id,
                'date': fields.Date.today(),
                'ref': f"Acompte {invoice.name}",
                'sale_id': order.id,
                'is_reconciled': True,
            })
            payment_obj.action_post()
            return payment_obj
        except Exception as e:
            _logger.exception("Erreur lors de l'enregistrement du paiement : %s", str(e))
            return None

    def _make_response(self, data, status_code=200):
        """Helper method to create consistent HTTP responses"""
        return request.make_response(
            json.dumps(data),
            headers=[('Content-Type', 'application/json')],
            status=status_code
        )
        
    def _order_to_dict(self, order):
        """Convert order to dictionary for API response"""
        invoice_data = []
        if order.invoice_ids:
            for invoice in order.invoice_ids:
                invoice_data.append({
                    'id': invoice.id,
                    'name': invoice.name,
                    'state': invoice.state,
                    'amount_total': invoice.amount_total,
                    'payment_state': invoice.payment_state if hasattr(invoice, 'payment_state') else 'unknown',
                    'is_advance_invoice': getattr(invoice, 'is_advance_invoice', False),
                })
        return {
            'id': order.id,
            'type_sale': order.type_sale,
            'name': order.name,
            'partner_id': order.partner_id.id,
            'currency_id': order.currency_id.id,
            'company_id': order.company_id.id,
            'state': order.state,
            'amount_total': order.amount_total,
            'invoice_status': order.invoice_status,
            'advance_payment_status': order.advance_payment_status,
            'invoices': invoice_data
        }



