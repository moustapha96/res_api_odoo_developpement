
from odoo import http
from odoo.http import request
import json
import difflib
from collections import defaultdict
import werkzeug.wrappers
import datetime
import logging



_logger = logging.getLogger(__name__)


# Réutiliser l'encodeur JSON personnalisé
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)


class ProductDeduplicationController(http.Controller):
    """
    Contrôleur pour la déduplication des produits dans Odoo.
    Permet de détecter et fusionner les produits similaires avec 95% de ressemblance.
    """

    def _calculate_similarity(self, name1, name2):
        """Calcule la similarité entre deux noms de produits"""
        if not name1 or not name2:
            return 0.0
        
        # Normaliser les noms (minuscules, suppression des espaces multiples)
        name1_clean = ' '.join(name1.lower().split())
        name2_clean = ' '.join(name2.lower().split())
        
        # Utiliser SequenceMatcher pour calculer la similarité
        similarity = difflib.SequenceMatcher(None, name1_clean, name2_clean).ratio()
        return similarity

    def _get_product_completeness_score(self, product):
        """Calcule un score de complétude pour un produit"""
        score = 0
        
        # Points pour les champs de base
        if product.name: score += 1
        if product.description: score += 1
        if product.list_price > 0: score += 1
        if product.standard_price > 0: score += 1
        
        # Points pour les images
        if product.image_1920: score += 2
        
        # Points pour les images supplémentaires
        if hasattr(product, 'product_image_ids'):
            score += min(len(product.product_image_ids), 3)
        
        # Points pour les opérations via les variantes
        operations_score = 0

        # Récupérer tous les IDs des variantes
        variant_ids = [variant.id for variant in product.product_variant_ids]

        if variant_ids:
            # Vérifier les mouvements de stock
            stock_moves = request.env['stock.move'].sudo().search([
                ('product_id', 'in', variant_ids)
            ], limit=1)
            if stock_moves:
                operations_score += 3
            
            # Vérifier les lignes de vente
            sale_lines = request.env['sale.order.line'].sudo().search([
                ('product_id', 'in', variant_ids)
            ], limit=1)
            if sale_lines:
                operations_score += 3
            
            # Vérifier les lignes d'achat
            purchase_lines = request.env['purchase.order.line'].sudo().search([
                ('product_id', 'in', variant_ids)
            ], limit=1)
            if purchase_lines:
                operations_score += 3

        score += operations_score
        
        # Points pour la catégorie
        if product.categ_id: score += 1
        
        return score

    def _has_operations(self, product):
        """Vérifie si un produit a des opérations (ventes, achats, mouvements de stock)"""
        # Récupérer tous les IDs des variantes de ce produit template
        variant_ids = [variant.id for variant in product.product_variant_ids]
        
        if not variant_ids:
            return False
        
        # Vérifier les mouvements de stock
        stock_moves = request.env['stock.move'].sudo().search([
            ('product_id', 'in', variant_ids)
        ], limit=1)
        if stock_moves:
            return True
        
        # Vérifier les lignes de vente
        sale_lines = request.env['sale.order.line'].sudo().search([
            ('product_id', 'in', variant_ids)
        ], limit=1)
        if sale_lines:
            return True
        
        # Vérifier les lignes d'achat
        purchase_lines = request.env['purchase.order.line'].sudo().search([
            ('product_id', 'in', variant_ids)
        ], limit=1)
        if purchase_lines:
            return True
        
        return False

    def _merge_products(self, product_to_keep, product_to_remove):
        """Fusionne deux produits en gardant les meilleures données"""
        
        # Préparer les valeurs de mise à jour
        update_vals = {}
        
        # S'assurer que le type est 'product' (stockable)
        if product_to_keep.type != 'product':
            update_vals['type'] = 'product'
        
        # Fusionner les descriptions si celle à supprimer est plus complète
        if not product_to_keep.description and product_to_remove.description:
            update_vals['description'] = product_to_remove.description
        elif (product_to_remove.description and 
          len(product_to_remove.description) > len(product_to_keep.description or '')):
            update_vals['description'] = product_to_remove.description
        
        # Fusionner les prix si manquants
        if not product_to_keep.list_price and product_to_remove.list_price:
            update_vals['list_price'] = product_to_remove.list_price
        if not product_to_keep.standard_price and product_to_remove.standard_price:
            update_vals['standard_price'] = product_to_remove.standard_price
        if not product_to_keep.volume and product_to_remove.volume:
            update_vals['volume'] = product_to_remove.volume
        if not product_to_keep.weight and product_to_remove.weight:
            update_vals['weight'] = product_to_remove.weight
        if not product_to_keep.barcode and product_to_remove.barcode:
            update_vals['barcode'] = product_to_remove.barcode
        if not product_to_keep.default_code and product_to_remove.default_code:
            update_vals['default_code'] = product_to_remove.default_code
        if not product_to_keep.creditorder_price and product_to_remove.creditorder_price:
            update_vals['creditorder_price'] = product_to_remove.creditorder_price
        if not product_to_keep.promo_price and product_to_remove.promo_price:  
            update_vals['promo_price'] = product_to_remove.promo_price
        if not product_to_keep.rate_price and product_to_remove.rate_price:
            update_vals['rate_price'] = product_to_remove.rate_price

        # Fusionner l'image principale si manquante
        if not product_to_keep.image_1920 and product_to_remove.image_1920:
            update_vals['image_1920'] = product_to_remove.image_1920
        
        if not product_to_keep.image_1 and product_to_remove.image_1:
            update_vals['image_1'] = product_to_remove.image_1
        
        if not product_to_keep.image_2 and product_to_remove.image_2:
            update_vals['image_2'] = product_to_remove.image_2
        
        if not product_to_keep.image_3 and product_to_remove.image_3:
            update_vals['image_3'] = product_to_remove.image_3
        
        if not product_to_keep.image_4 and product_to_remove.image_4:
            update_vals['image_4'] = product_to_remove.image_4
        
        # Fusionner la catégorie si manquante
        if not product_to_keep.categ_id and product_to_remove.categ_id:
            update_vals['categ_id'] = product_to_remove.categ_id.id
        
        update_vals['sale_ok'] = True
        update_vals['purchase_ok'] = True
        update_vals['en_promo']= True
        update_vals['is_preorder'] = True
        update_vals['is_creditorder'] = True

        # Mettre à jour le produit à conserver
        if update_vals:
            product_to_keep.sudo().write(update_vals)
            _logger.info(f"Produit mis à jour: {product_to_keep.name} avec {list(update_vals.keys())}")
        
        # Transférer les images supplémentaires
        if hasattr(product_to_remove, 'product_image_ids'):
            for image in product_to_remove.product_image_ids:
                # Vérifier si cette image n'existe pas déjà
                existing_image = request.env['product.image'].sudo().search([
                    ('product_tmpl_id', '=', product_to_keep.id),
                    ('name', '=', image.name)
                ], limit=1)
            
            if not existing_image:
                image.sudo().write({'product_tmpl_id': product_to_keep.id})
                _logger.info(f"Image transférée: {image.name}")
    
        # Transférer les références des variantes de produit
        for variant_to_remove in product_to_remove.product_variant_ids:
            # Trouver la variante correspondante dans le produit à conserver
            corresponding_variant = product_to_keep.product_variant_ids[0] if product_to_keep.product_variant_ids else None
            
            if corresponding_variant:
                # Transférer les mouvements de stock non terminés
                stock_moves = request.env['stock.move'].sudo().search([
                    ('product_id', '=', variant_to_remove.id),
                    ('state', 'not in', ['done', 'cancel'])
                ])
                for move in stock_moves:
                    try:
                        move.sudo().write({'product_id': corresponding_variant.id})
                        _logger.info(f"Mouvement de stock transféré: {move.name}")
                    except Exception as e:
                        _logger.warning(f"Impossible de transférer le mouvement {move.name}: {str(e)}")
            
                # Transférer les lignes de commande de vente en brouillon
                sale_lines = request.env['sale.order.line'].sudo().search([
                    ('product_id', '=', variant_to_remove.id),
                    ('order_id.state', 'in', ['draft', 'sent'])
                ])
                for sale_line in sale_lines:
                    try:
                        sale_line.sudo().write({'product_id': corresponding_variant.id})
                        _logger.info(f"Ligne de vente transférée: {sale_line.order_id.name}")
                    except Exception as e:
                        _logger.warning(f"Impossible de transférer la ligne de vente: {str(e)}")
            
                # Transférer les lignes de commande d'achat en brouillon
                purchase_lines = request.env['purchase.order.line'].sudo().search([
                    ('product_id', '=', variant_to_remove.id),
                    ('order_id.state', 'in', ['draft', 'sent'])
                ])
                for purchase_line in purchase_lines:
                    try:
                        purchase_line.sudo().write({'product_id': corresponding_variant.id})
                        _logger.info(f"Ligne d'achat transférée: {purchase_line.order_id.name}")
                    except Exception as e:
                        _logger.warning(f"Impossible de transférer la ligne d'achat: {str(e)}")
        
        return product_to_keep

    def _deduplicate_products(self):
        """
        Fonction principale pour détecter et fusionner les produits similaires avec 95% de ressemblance.
        """
        try:
            # Récupérer tous les produits actifs
            all_products = request.env['product.template'].sudo().search([('active', '=', True)])
            
            if not all_products:
                return {
                    "success": True,
                    "message": "Aucun produit trouvé",
                    "merged_count": 0,
                    "deleted_count": 0
                }
            
            # Grouper les produits similaires
            similar_groups = defaultdict(list)
            processed_products = set()
            
            _logger.info(f"Analyse de {len(all_products)} produits pour détecter les doublons...")
            
            for i, product1 in enumerate(all_products):
                if product1.id in processed_products:
                    continue
                    
                current_group = [product1]
                processed_products.add(product1.id)
                
                for j, product2 in enumerate(all_products[i+1:], i+1):
                    if product2.id in processed_products:
                        continue
                        
                    similarity = self._calculate_similarity(product1.name, product2.name)
                    
                    if similarity >= 0.95:  # 95% de similarité
                        current_group.append(product2)
                        processed_products.add(product2.id)
                        _logger.info(f"Produits similaires détectés: '{product1.name}' et '{product2.name}' (similarité: {similarity:.2%})")
                
                if len(current_group) > 1:
                    similar_groups[f"group_{len(similar_groups)}"] = current_group
            
            # Traiter chaque groupe de produits similaires
            merged_count = 0
            deleted_count = 0
            merge_details = []
            
            for group_name, products in similar_groups.items():
                _logger.info(f"Traitement du groupe {group_name} avec {len(products)} produits")
                
                # Séparer les produits avec et sans opérations
                products_with_operations = [p for p in products if self._has_operations(p)]
                products_without_operations = [p for p in products if not self._has_operations(p)]
                
                # Déterminer le produit à conserver
                if products_with_operations:
                    # S'il y a des produits avec opérations, choisir le plus complet parmi eux
                    product_to_keep = max(products_with_operations, 
                                        key=lambda p: self._get_product_completeness_score(p))
                    products_to_remove = [p for p in products if p.id != product_to_keep.id]
                else:
                    # Sinon, choisir le plus complet parmi tous
                    product_to_keep = max(products, 
                                        key=lambda p: self._get_product_completeness_score(p))
                    products_to_remove = [p for p in products if p.id != product_to_keep.id]
                
                _logger.info(f"Produit à conserver: {product_to_keep.name} (ID: {product_to_keep.id})")
                
                group_detail = {
                    "group_name": group_name,
                    "product_kept": {
                        "id": product_to_keep.id,
                        "name": product_to_keep.name,
                        "has_operations": self._has_operations(product_to_keep)
                    },
                    "products_removed": []
                }
                
                # Fusionner les données des autres produits dans celui à conserver
                for product_to_remove in products_to_remove:
                    _logger.info(f"Fusion du produit: {product_to_remove.name} (ID: {product_to_remove.id})")
                    
                    try:
                        # Ajouter aux détails avant suppression
                        group_detail["products_removed"].append({
                            "id": product_to_remove.id,
                            "name": product_to_remove.name,
                            "has_operations": self._has_operations(product_to_remove)
                        })
                        
                        # Fusionner les données
                        self._merge_products(product_to_keep, product_to_remove)
                        
                        # Supprimer le produit en double
                        product_to_remove.sudo().unlink()
                        deleted_count += 1
                        
                        _logger.info(f"Produit supprimé: {product_to_remove.name}")
                        
                    except Exception as e:
                        _logger.error(f"Erreur lors de la suppression du produit {product_to_remove.name}: {str(e)}")
                        # Retirer de la liste des supprimés en cas d'erreur
                        if group_detail["products_removed"]:
                            group_detail["products_removed"].pop()
                
                merge_details.append(group_detail)
                merged_count += 1
            
            result = {
                "success": True,
                "message": f"Déduplication terminée avec succès",
                "groups_processed": len(similar_groups),
                "merged_count": merged_count,
                "deleted_count": deleted_count,
                "details": {
                    "total_products_analyzed": len(all_products),
                    "similar_groups_found": len(similar_groups),
                    "merge_details": merge_details
                }
            }
            
            _logger.info(f"Déduplication terminée: {merged_count} groupes traités, {deleted_count} produits supprimés")
            return result
            
        except Exception as e:
            _logger.error(f"Erreur lors de la déduplication: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Erreur lors de la déduplication: {str(e)}",
                "merged_count": 0,
                "deleted_count": 0
            }

    @http.route('/api/deduplicate_products', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def deduplicate_products_endpoint(self, **kwargs):
        """Endpoint pour lancer la déduplication des produits"""
        
        try:
            # Vérifier si un mode de test est demandé
            test_mode = kwargs.get('test_mode', 'false').lower() == 'true'
            
            if test_mode:
                # En mode test, on fait juste une prévisualisation
                result = self._preview_duplicates()
                result["test_mode"] = True
                result["message"] = "Mode test - Aucune modification effectuée"
            else:
                result = self._deduplicate_products()
            
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(result, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
            )
            
        except Exception as e:
            _logger.error(f"Erreur dans l'endpoint de déduplication: {str(e)}", exc_info=True)
            return werkzeug.wrappers.Response(
                status=500,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({
                    "success": False,
                    "error": f"Erreur lors de la déduplication: {str(e)}"
                })
            )

    def _preview_duplicates(self):
        """Prévisualise les doublons sans les supprimer"""
        try:
            all_products = request.env['product.template'].sudo().search([('active', '=', True)])
            
            duplicates_preview = []
            processed_products = set()
            
            for i, product1 in enumerate(all_products):
                if product1.id in processed_products:
                    continue
                    
                similar_products = []
                
                for j, product2 in enumerate(all_products[i+1:], i+1):
                    if product2.id in processed_products:
                        continue
                        
                    similarity = self._calculate_similarity(product1.name, product2.name)
                    
                    if similarity >= 0.95:
                        similar_products.append({
                            'id': product2.id,
                            'name': product2.name,
                            'similarity': round(similarity * 100, 2),
                            'has_operations': self._has_operations(product2),
                            'completeness_score': self._get_product_completeness_score(product2),
                            'type': product2.type,
                            'list_price': product2.list_price,
                            'category': product2.categ_id.name if product2.categ_id else None
                        })
                        processed_products.add(product2.id)
                
                if similar_products:
                    duplicates_preview.append({
                        'main_product': {
                            'id': product1.id,
                            'name': product1.name,
                            'has_operations': self._has_operations(product1),
                            'completeness_score': self._get_product_completeness_score(product1),
                            'type': product1.type,
                            'list_price': product1.list_price,
                            'category': product1.categ_id.name if product1.categ_id else None
                        },
                        'similar_products': similar_products,
                        'total_in_group': len(similar_products) + 1,
                        'recommended_to_keep': max([product1] + [p for p in all_products if p.id in [sp['id'] for sp in similar_products]], 
                                                 key=lambda p: (self._has_operations(p), self._get_product_completeness_score(p))).id
                    })
                    processed_products.add(product1.id)
            
            return {
                "success": True,
                "total_duplicate_groups": len(duplicates_preview),
                "total_products_to_remove": sum(len(group['similar_products']) for group in duplicates_preview),
                "duplicate_groups": duplicates_preview
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la prévisualisation: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Erreur lors de la prévisualisation: {str(e)}"
            }

    @http.route('/api/preview_duplicates', methods=['GET'], type='http', auth='none', cors="*")
    def preview_duplicates_endpoint(self, **kwargs):
        """Endpoint pour prévisualiser les doublons sans les supprimer"""
        
        try:
            result = self._preview_duplicates()
            
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(result, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
            )
            
        except Exception as e:
            return werkzeug.wrappers.Response(
                status=500,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({
                    "success": False,
                    "error": f"Erreur lors de la prévisualisation: {str(e)}"
                })
            )

    @http.route('/api/merge_specific_products', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def merge_specific_products_endpoint(self, **kwargs):
        """Endpoint pour fusionner des produits spécifiques"""
        
        try:
            # Récupérer les IDs des produits à fusionner
            product_ids = kwargs.get('product_ids', '')
            keep_product_id = kwargs.get('keep_product_id', '')
            
            if not product_ids or not keep_product_id:
                return werkzeug.wrappers.Response(
                    status=400,
                    content_type='application/json; charset=utf-8',
                    response=json.dumps({
                        "success": False,
                        "error": "Paramètres manquants: product_ids et keep_product_id requis"
                    })
                )
            
            # Convertir les IDs en liste d'entiers
            try:
                product_ids_list = [int(id.strip()) for id in product_ids.split(',')]
                keep_product_id = int(keep_product_id)
            except ValueError:
                return werkzeug.wrappers.Response(
                    status=400,
                    content_type='application/json; charset=utf-8',
                    response=json.dumps({
                        "success": False,
                        "error": "IDs de produits invalides"
                    })
                )
            
            # Récupérer les produits
            products_to_remove = request.env['product.template'].sudo().browse(product_ids_list)
            product_to_keep = request.env['product.template'].sudo().browse(keep_product_id)
            
            if not product_to_keep.exists():
                return werkzeug.wrappers.Response(
                    status=404,
                    content_type='application/json; charset=utf-8',
                    response=json.dumps({
                        "success": False,
                        "error": "Produit à conserver non trouvé"
                    })
                )
            
            merged_products = []
            errors = []
            
            # Fusionner chaque produit
            for product_to_remove in products_to_remove:
                if product_to_remove.exists() and product_to_remove.id != keep_product_id:
                    try:
                        self._merge_products(product_to_keep, product_to_remove)
                        merged_products.append({
                            "id": product_to_remove.id,
                            "name": product_to_remove.name
                        })
                        product_to_remove.sudo().unlink()
                    except Exception as e:
                        errors.append({
                            "product_id": product_to_remove.id,
                            "product_name": product_to_remove.name,
                            "error": str(e)
                        })
            
            result = {
                "success": True,
                "product_kept": {
                    "id": product_to_keep.id,
                    "name": product_to_keep.name
                },
                "merged_products": merged_products,
                "merged_count": len(merged_products),
                "errors": errors
            }
            
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(result, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
            )
            
        except Exception as e:
            _logger.error(f"Erreur lors de la fusion spécifique: {str(e)}", exc_info=True)
            return werkzeug.wrappers.Response(
                status=500,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({
                    "success": False,
                    "error": f"Erreur lors de la fusion: {str(e)}"
                })
            )

    @http.route('/api/deduplication_stats', methods=['GET'], type='http', auth='none', cors="*")
    def deduplication_stats_endpoint(self, **kwargs):
        """Endpoint pour obtenir des statistiques sur les produits"""
        
        try:
            all_products = request.env['product.template'].sudo().search([('active', '=', True)])
            
            # Statistiques générales
            total_products = len(all_products)
            products_with_operations = sum(1 for p in all_products if self._has_operations(p))
            products_without_operations = total_products - products_with_operations
            
            # Statistiques par type
            type_stats = {}
            for product in all_products:
                product_type = product.type
                if product_type not in type_stats:
                    type_stats[product_type] = 0
                type_stats[product_type] += 1
            
            # Produits sans images
            products_without_images = sum(1 for p in all_products if not p.image_1920)
            
            # Produits sans catégorie
            products_without_category = sum(1 for p in all_products if not p.categ_id)
            
            # Estimation des doublons potentiels
            potential_duplicates = 0
            processed = set()
            
            for i, product1 in enumerate(all_products):
                if product1.id in processed:
                    continue
                
                similar_count = 0
                for j, product2 in enumerate(all_products[i+1:], i+1):
                    if product2.id in processed:
                        continue
                    
                    similarity = self._calculate_similarity(product1.name, product2.name)
                    if similarity >= 0.9995:
                        similar_count += 1
                        processed.add(product2.id)
                
                if similar_count > 0:
                    potential_duplicates += similar_count
                    processed.add(product1.id)
            
            result = {
                "success": True,
                "statistics": {
                    "total_products": total_products,
                    "products_with_operations": products_with_operations,
                    "products_without_operations": products_without_operations,
                    "products_without_images": products_without_images,
                    "products_without_category": products_without_category,
                    "potential_duplicates": potential_duplicates,
                    "type_distribution": type_stats
                }
            }
            
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(result, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
            )
            
        except Exception as e:
            _logger.error(f"Erreur lors du calcul des statistiques: {str(e)}", exc_info=True)
            return werkzeug.wrappers.Response(
                status=500,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({
                    "success": False,
                    "error": f"Erreur lors du calcul des statistiques: {str(e)}"
                })
            )
        
    def find_similar_products(self, products, max_diff=3):
        """
        Trouve les produits ayant presque le même nom avec une différence de max_diff caractères.

        :param products: Liste de dictionnaires contenant les noms et les IDs des produits.
        :param max_diff: Différence maximale autorisée (par défaut 3).
        :return: Dictionnaire avec les groupes de produits similaires.
        """
        similar_groups = {}

        for i, product1 in enumerate(products):
            group = [product1]
            for j, product2 in enumerate(products[i+1:], i+1):
                # Calculer la différence entre les deux noms de produits
                diff = difflib.ndiff(product1['name'].lower(), product2['name'].lower())
                differences = sum(1 for d in diff if d[0] != ' ')

                if differences <= max_diff:
                    group.append(product2)

            if len(group) > 1:
                # Utiliser le premier produit du groupe comme clé
                key = group[0]['name']
                similar_groups[key] = group

        return similar_groups        

    


    @http.route('/api/find_similar_products', methods=['GET'], type='http', auth='none', cors="*")
    def find_similar_products_endpoint(self, **kwargs):
        """Endpoint pour trouver les produits ayant presque le même nom avec une différence de max_diff caractères."""
        try:
            max_diff = int(kwargs.get('max_diff', 3))
            all_products = request.env['product.template'].sudo().search([('active', '=', True)])
            products = [{'id': product.id, 'name': product.name} for product in all_products]

            similar_products = self.find_similar_products(products, max_diff)

            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(similar_products, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
            )

        except Exception as e:
            _logger.error(f"Erreur lors de la recherche de produits similaires: {str(e)}", exc_info=True)
            return werkzeug.wrappers.Response(
                status=500,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({
                    "success": False,
                    "error": f"Erreur lors de la recherche de produits similaires: {str(e)}"
                })
            )