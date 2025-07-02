

from odoo import http
from odoo.http import request
import json
import requests
from bs4 import BeautifulSoup
import werkzeug.wrappers
import os
import datetime
import urllib.parse
import base64
import logging
import io
from PIL import Image
import difflib
import re
from collections import defaultdict
from pathlib import Path

from difflib import SequenceMatcher


# Importer la configuration pour accéder au filestore
from odoo.tools import config
from odoo import fields

_logger = logging.getLogger(__name__)

# Encodeur JSON personnalisé pour gérer les objets datetime
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)


class CompleteProductController(http.Controller):
    """
    Contrôleur complet pour la gestion avancée des produits Odoo
    Inclut scraping, déduplication, import intelligent et nettoyage
    """

    def _is_odoo_sh(self):
        """Détecte si l'environnement est Odoo SH"""
        return os.environ.get('ODOO_SH_ENVIRONMENT') is not None

    def _get_data_dir(self):
        """Obtient le répertoire de données approprié"""
        filestore_path = config.get('data_dir')
        data_dir = os.path.join(filestore_path, 'scraper_data')
        os.makedirs(data_dir, exist_ok=True)
        return data_dir

    def _has_operations(self, product):
        """Vérifie si un produit a des opérations (ventes, achats, mouvements de stock)"""
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

    def _calculate_name_similarity(self, name1, name2):
        """Calcule la similarité entre deux noms de produits avec une précision élevée"""
        if not name1 or not name2:
            return 0.0
        
        # Normaliser les noms
        name1_clean = ' '.join(name1.lower().strip().split())
        name2_clean = ' '.join(name2.lower().strip().split())
        
        # Utiliser SequenceMatcher pour calculer la similarité
        similarity = difflib.SequenceMatcher(None, name1_clean, name2_clean).ratio()
        return similarity

    def _has_only_dash_difference(self, name1, name2):
        """Vérifie si la seule différence entre deux noms est un tiret ou underscore"""
        if not name1 or not name2:
            return False
        
        # Normaliser et comparer sans tirets/underscores/espaces
        name1_no_dash = re.sub(r'[-_\s]+', '', name1.lower())
        name2_no_dash = re.sub(r'[-_\s]+', '', name2.lower())
        
        return name1_no_dash == name2_no_dash and name1_no_dash != ''

    def _has_only_number_difference(self, name1, name2):
        """Vérifie si la seule différence entre deux noms est un ou plusieurs chiffres"""
        if not name1 or not name2:
            return False
        
        # Remplacer tous les chiffres par un placeholder
        name1_no_numbers = re.sub(r'\d+', 'X', name1.lower())
        name2_no_numbers = re.sub(r'\d+', 'X', name2.lower())
        
        return name1_no_numbers == name2_no_numbers and name1_no_numbers != ''



    def _get_product_completeness_score(self, product):
        """Calcule un score de complétude pour un produit"""
        score = 0
        
        # Points pour les champs de base
        if product.name: score += 1
        if product.description: score += 3
        if product.list_price > 0: score += 2
        if product.standard_price > 0: score += 1
        
        # Points pour les images
        if product.image_1920: score += 4

        if product.image_1: score += 4
        if product.image_2: score += 4
        if product.image_3: score += 4
        if product.image_4: score += 4
        
        # # Points pour les images supplémentaires
        # if hasattr(product, 'product_image_ids'):
        #     score += min(len(product.product_image_ids), 3)
        
        # Points pour la catégorie
        if product.categ_id: score += 1
        
        # Points pour les champs supplémentaires
        if product.barcode: score += 1
        if product.default_code: score += 1
        if product.weight > 0: score += 1
        if product.volume > 0: score += 1
        
        # Points pour les opérations
        if self._has_operations(product):
            score += 5
        
        return score

    def _get_product_completeness_score_simple(self, product):
        """Calcule un score de complétude pour un produit"""
        score = 0
        
        # Points pour les champs de base
        if product.name: score += 1
        # Points pour les opérations
        if self._has_operations(product):
            score += 5
        
        return score

    def _get_similarity_details(self, name1, name2):
        """Retourne les détails de similarité entre deux noms"""
        if not name1 or not name2:
            return {
                'similarity_score': 0.0,
                'similarity_percentage': 0.0,
                'match_type': 'no_match',
                'details': 'Noms manquants'
            }

        # Calculer la similarité de base
        similarity = self._calculate_name_similarity(name1, name2)

        # Déterminer le type de correspondance
        match_type = 'no_match'
        details = ''

        if similarity >= 0.99:
            match_type = 'high_similarity'
            details = f'Similarité très élevée ({similarity:.4f})'
        elif similarity >= 0.95:
            match_type = 'good_similarity'
            details = f'Bonne similarité ({similarity:.4f})'
        elif self._has_only_dash_difference(name1, name2):
            match_type = 'dash_difference'
            details = 'Différence de tiret/underscore uniquement'
        elif self._has_only_number_difference(name1, name2):
            match_type = 'number_difference'
            details = 'Différence de chiffre uniquement'
        elif similarity >= 0.8:
            match_type = 'moderate_similarity'
            details = f'Similarité modérée ({similarity:.4f})'
        else:
            match_type = 'low_similarity'
            details = f'Faible similarité ({similarity:.4f})'

        return {
            'similarity_score': round(similarity, 4),
            'similarity_percentage': round(similarity * 100, 2),
            'match_type': match_type,
            'details': details
        }

    def _merge_product_data(self, target_product, source_product):
        """Fusionne les données du produit source vers le produit cible"""
        update_vals = {}
        
        # S'assurer que le type est 'product' (stockable)
        if target_product.type != 'product':
            update_vals['type'] = 'product'
        
        # Fusionner les descriptions si celle source est plus complète
        if not target_product.description and source_product.description:
            update_vals['description'] = source_product.description
        elif (source_product.description and 
              len(source_product.description) > len(target_product.description or '')):
            update_vals['description'] = source_product.description
        
        # Fusionner les prix si manquants ou si source est plus élevé
        if not target_product.list_price and source_product.list_price:
            update_vals['list_price'] = source_product.list_price
        if not target_product.standard_price and source_product.standard_price:
            update_vals['standard_price'] = source_product.standard_price
        
        # Fusionner les autres champs si manquants
        fields_to_merge = ['volume', 'weight', 'barcode', 'default_code']
        for field in fields_to_merge:
            if not getattr(target_product, field) and getattr(source_product, field):
                update_vals[field] = getattr(source_product, field)

        if not target_product.barcode and source_product.barcode:
            update_vals['barcode'] = source_product.barcode
        if not target_product.default_code and source_product.default_code:
            update_vals['default_code'] = source_product.default_code
        if not target_product.creditorder_price and source_product.creditorder_price:
            update_vals['creditorder_price'] = source_product.creditorder_price
        if not target_product.promo_price and source_product.promo_price:  
            update_vals['promo_price'] = source_product.promo_price
        if not target_product.rate_price and source_product.rate_price:
            update_vals['rate_price'] = source_product.rate_price

        
        # Fusionner l'image principale si manquante
        if not target_product.image_1920 and source_product.image_1920:
            update_vals['image_1920'] = source_product.image_1920

        if not target_product.image_1 and source_product.image_1:
            update_vals['image_1'] = source_product.image_1

        if not target_product.image_2 and source_product.image_2:
            update_vals['image_2'] = source_product.image_2

        if not target_product.image_3 and source_product.image_3:
            update_vals['image_3'] = source_product.image_3

        if not target_product.image_4 and source_product.image_4:
            update_vals['image_4'] = source_product.image_4
        
        # Fusionner la catégorie si manquante
        if not target_product.categ_id and source_product.categ_id:
            update_vals['categ_id'] = source_product.categ_id.id
        
        # S'assurer que les flags de vente/achat sont activés
        update_vals['sale_ok'] = True
        update_vals['purchase_ok'] = True
        
        # Mettre à jour le produit cible
        if update_vals:
            target_product.sudo().write(update_vals)
            _logger.info(f"Produit mis à jour: {target_product.name} avec {list(update_vals.keys())}")
        
        
        return target_product

    def ensure_default_category(self):
        """S'assure qu'une catégorie par défaut existe et retourne son ID"""
        default_category_name = "Non catégorisé"
        
        default_category = request.env['product.category'].sudo().search([
            ('name', '=', default_category_name)
        ], limit=1)
        
        if not default_category:
            _logger.info(f"Création de la catégorie par défaut: {default_category_name}")
            try:
                default_category = request.env['product.category'].sudo().create({
                    'name': default_category_name
                })
                _logger.info(f"Catégorie par défaut créée avec ID: {default_category.id}")
            except Exception as e:
                _logger.error(f"Erreur lors de la création de la catégorie par défaut: {str(e)}")
                return 1  # Utiliser la catégorie "All" par défaut
        
        return default_category.id

    def get_category_id(self, categories):
        """Récupère ou crée une catégorie de produit"""
        try:
            if not categories or not categories[0]:
                return None
            
            category_name = categories[0]
            category = request.env['product.category'].sudo().search([
                ('name', '=', category_name)
            ], limit=1)
            
            if not category:
                category = request.env['product.category'].sudo().create({
                    'name': category_name
                })
            
            return category.id
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération/création de la catégorie: {str(e)}")
            return None

    def get_image_base64(self, image_url):
        """Récupère une image depuis une URL et la convertit en base64"""
        if not image_url:
            return False
            
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            content = response.content
            try:
                img = Image.open(io.BytesIO(content))
                img.verify()
                
                img = Image.open(io.BytesIO(content))
                
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                    img = background
                
                max_size = (1920, 1920)
                if img.width > max_size[0] or img.height > max_size[1]:
                    img.thumbnail(max_size, Image.LANCZOS)
                
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                return img_base64
                
            except Exception as e:
                _logger.error(f"Contenu non valide comme image: {str(e)}")
                return False
                
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de l'image {image_url}: {str(e)}")
            return False

    # ==================== ENDPOINTS PRINCIPAUX ====================

    @http.route('/api/delete_products_without_operations', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def delete_products_without_operations(self, **kwargs):
        """Supprime tous les produits qui n'ont pas d'opérations"""
        try:
            all_products = request.env['product.template'].sudo().search([('active', '=', True)])
            
            products_to_delete = []
            products_with_operations = []
            
            _logger.info(f"Analyse de {len(all_products)} produits pour identifier ceux sans opérations...")
            
            for product in all_products:
                product_info = {
                    'id': product.id,
                    'name': product.name,
                    'type': product.type,
                    'category': product.categ_id.name if product.categ_id else 'Sans catégorie',
                    'completeness_score': self._get_product_completeness_score(product),
                    'has_image': bool(product.image_1920),
                    'has_description': bool(product.description),
                    'list_price': product.list_price
                }
                
                if self._has_operations(product):
                    products_with_operations.append(product_info)
                else:
                    products_to_delete.append(product_info)
            
            test_mode = kwargs.get('test_mode', 'false').lower() == 'true'
            
            if test_mode:
                result = {
                    "success": True,
                    "test_mode": True,
                    "message": "Mode test - Aucune suppression effectuée",
                    "total_products": len(all_products),
                    "products_with_operations": len(products_with_operations),
                    "products_to_delete": len(products_to_delete),
                    "products_to_delete_preview": products_to_delete[:20],  # Aperçu des 20 premiers
                    "summary_by_category": self._get_deletion_summary_by_category(products_to_delete)
                }
            else:
                deleted_count = 0
                errors = []
                
                _logger.info(f"Suppression de {len(products_to_delete)} produits sans opérations...")
                
                for product_info in products_to_delete:
                    try:
                        product = request.env['product.template'].sudo().browse(product_info['id'])
                        if product.exists():
                            product.unlink()
                            deleted_count += 1
                            if deleted_count % 100 == 0:
                                _logger.info(f"Supprimé {deleted_count} produits...")
                    except Exception as e:
                        errors.append({
                            'product_id': product_info['id'],
                            'product_name': product_info['name'],
                            'error': str(e)
                        })
                
                result = {
                    "success": True,
                    "message": f"Suppression terminée: {deleted_count} produits supprimés",
                    "total_products": len(all_products),
                    "products_with_operations": len(products_with_operations),
                    "deleted_count": deleted_count,
                    "errors_count": len(errors),
                    "errors": errors[:10],  # Limiter l'affichage des erreurs
                    "summary_by_category": self._get_deletion_summary_by_category(products_to_delete)
                }
                
                _logger.info(f"Suppression terminée: {deleted_count} produits supprimés, {len(errors)} erreurs")
            
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(result, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
            )
            
        except Exception as e:
            _logger.error(f"Erreur lors de la suppression: {str(e)}", exc_info=True)
            return werkzeug.wrappers.Response(
                status=500,
                content_type='application/json; charset=utf-8',
                response=json.dumps({
                    "success": False,
                    "error": f"Erreur lors de la suppression: {str(e)}"
                })
            )

    def _get_deletion_summary_by_category(self, products_to_delete):
        """Résumé des suppressions par catégorie"""
        summary = {}
        for product in products_to_delete:
            category = product['category']
            if category not in summary:
                summary[category] = {
                    'count': 0,
                    'avg_completeness_score': 0,
                    'total_score': 0
                }
            summary[category]['count'] += 1
            summary[category]['total_score'] += product['completeness_score']
        
        # Calculer les moyennes
        for category in summary:
            if summary[category]['count'] > 0:
                summary[category]['avg_completeness_score'] = round(
                    summary[category]['total_score'] / summary[category]['count'], 2
                )
            del summary[category]['total_score']  # Supprimer le total temporaire
        
        return summary



    def normalize_name(self, name):
        return name.replace('-', '').replace('–', '').replace('—', '').lower().strip()

    def _has_only_dash_difference(self, name1, name2):
        """
        Vérifie si la seule différence entre deux noms est la présence ou absence de tirets
        """
        normalize = lambda s: s.replace('-', '').replace('–', '').lower().strip()
        return normalize(name1) == normalize(name2)
    
    def _has_only_number_difference(self, name1, name2):
        """
        Vérifie si la seule différence entre deux noms est la présence ou absence de chiffres
        """
        normalize = lambda s: re.sub(r'\d+', 'X', s.lower().strip())
        return normalize(name1) == normalize(name2)
    
    def _are_names_similar(self, name1, name2, threshold=0.99):
        """
        Compare deux noms et retourne True si leur similarité est supérieure au seuil.
        """
        ratio = difflib.SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
        return ratio >= threshold
    



    def _is_minor_difference(self, name1, name2):
        """
        Vérifie si les deux noms sont identiques à un tiret, un espace ou un chiffre près.
        """
        # Normalisation : tout en minuscules, sans espaces ni tirets
        clean1 = re.sub(r'[\s\-]', '', name1.lower())
        clean2 = re.sub(r'[\s\-]', '', name2.lower())

        # Ratio de similarité
        similarity_ratio = SequenceMatcher(None, clean1, clean2).ratio()

        # S'ils sont très proches (95% ou plus), on considère qu'on peut mettre à jour
        return similarity_ratio >= 0.95 and clean1 != clean2


    

    @http.route('/api/analyze_product_similarities', methods=['GET'], type='http', auth='none', cors="*")
    def analyze_product_similarities(self, **kwargs):
        """Analyse les similarités entre produits existants avec scores détaillés"""
        try:
            similarity_threshold = float(kwargs.get('similarity_threshold', 0.99))
            max_results = int(kwargs.get('max_results', 5))
            include_all_similarities = kwargs.get('include_all_similarities', 'false').lower() == 'true'
            
            all_products = request.env['product.template'].sudo().search([('active', '=', True)])
            
            _logger.info(f"Analyse des similarités pour {len(all_products)} produits...")
            
            analysis = {
                'high_similarity': [],
                'dash_differences': [],
                'number_differences': [],
                'moderate_similarities': [],  # Nouveau: similarités modérées
                'total_analyzed': len(all_products),
                'analysis_parameters': {
                    'similarity_threshold': similarity_threshold,
                    'max_results': max_results,
                    'include_all_similarities': include_all_similarities
                }
            }
            
            processed = set()
            
            for i, product1 in enumerate(all_products):
                if product1.id in processed:
                    continue
                
                if i % 100 == 0:
                    _logger.info(f"Analysé {i}/{len(all_products)} produits...")
                
                for j, product2 in enumerate(all_products[i+1:], i+1):
                    if product2.id in processed:
                        continue
                    
                    # Arrêter si on a atteint le maximum de résultats (sauf si include_all_similarities)
                    if not include_all_similarities:
                        total_found = (len(analysis['high_similarity']) + 
                                     len(analysis['dash_differences']) + 
                                     len(analysis['number_differences']))
                        if total_found >= max_results:
                            break
                    
                    similarity_details = self._get_similarity_details(product1.name, product2.name)
                    similarity = similarity_details['similarity_score']
                    
                    pair_info = {
                        'product1': {
                            'id': product1.id, 
                            'name': product1.name,
                            'has_operations': self._has_operations(product1),
                            'completeness_score': self._get_product_completeness_score(product1),
                            'category': product1.categ_id.name if product1.categ_id else 'Sans catégorie',
                            'type': product1.type
                        },
                        'product2': {
                            'id': product2.id, 
                            'name': product2.name,
                            'has_operations': self._has_operations(product2),
                            'completeness_score': self._get_product_completeness_score(product2),
                            'category': product2.categ_id.name if product2.categ_id else 'Sans catégorie',
                            'type': product2.type
                        },
                        'similarity_details': similarity_details,
                        'recommended_action': self._get_recommended_action(product1, product2, similarity_details)
                    }
                    
                    if similarity >= similarity_threshold:
                        analysis['high_similarity'].append(pair_info)
                        processed.add(product2.id)
                    elif self._has_only_dash_difference(product1.name, product2.name):
                        analysis['dash_differences'].append(pair_info)
                        processed.add(product2.id)
                    elif self._has_only_number_difference(product1.name, product2.name):
                        analysis['number_differences'].append(pair_info)
                        processed.add(product2.id)
                    elif include_all_similarities and similarity >= 0.8:  # Similarités modérées
                        analysis['moderate_similarities'].append(pair_info)
                
                processed.add(product1.id)
            
            # Trier par score de similarité décroissant
            for category in ['high_similarity', 'dash_differences', 'number_differences', 'moderate_similarities']:
                analysis[category].sort(key=lambda x: x['similarity_details']['similarity_score'], reverse=True)
            
            _logger.info(f"Analyse terminée: {len(analysis['high_similarity'])} similarités élevées, "
                        f"{len(analysis['dash_differences'])} différences de tirets, "
                        f"{len(analysis['number_differences'])} différences de chiffres, "
                        f"{len(analysis['moderate_similarities'])} similarités modérées")
            
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(analysis, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
            )
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'analyse: {str(e)}", exc_info=True)
            return werkzeug.wrappers.Response(
                status=500,
                content_type='application/json; charset=utf-8',
                response=json.dumps({
                    "success": False,
                    "error": f"Erreur lors de l'analyse: {str(e)}"
                })
            )

    def _get_recommended_action(self, product1, product2, similarity_details):
        """Recommande une action basée sur l'analyse des produits"""
        score1 = self._get_product_completeness_score(product1)
        score2 = self._get_product_completeness_score(product2)
        has_ops1 = self._has_operations(product1)
        has_ops2 = self._has_operations(product2)
        
        if similarity_details['match_type'] in ['high_similarity', 'dash_difference', 'number_difference']:
            if has_ops1 and has_ops2:
                return {
                    'action': 'merge_carefully',
                    'keep_product_id': product1.id if score1 >= score2 else product2.id,
                    'reason': 'Les deux produits ont des opérations - fusion manuelle recommandée',
                    'priority': 'high'
                }
            elif has_ops1:
                return {
                    'action': 'merge_into_first',
                    'keep_product_id': product1.id,
                    'reason': 'Le premier produit a des opérations',
                    'priority': 'medium'
                }
            elif has_ops2:
                return {
                    'action': 'merge_into_second',
                    'keep_product_id': product2.id,
                    'reason': 'Le second produit a des opérations',
                    'priority': 'medium'
                }
            else:
                return {
                    'action': 'merge_best_score',
                    'keep_product_id': product1.id if score1 >= score2 else product2.id,
                    'reason': 'Fusionner vers le produit le plus complet',
                    'priority': 'low'
                }
        else:
            return {
                'action': 'review_manually',
                'keep_product_id': None,
                'reason': 'Similarité faible - révision manuelle recommandée',
                'priority': 'low'
            }

    # =======================================================================================================



    def _extract_numeric_specifications(self, name):
        """Extrait les spécifications numériques importantes d'un nom de produit"""
        if not name:
            return {}
        
        specs = {}
        name_lower = name.lower()
        
        # Patterns pour différents types de spécifications
        patterns = {
            'capacity_liters': r'(\d+)\s*l(?:itres?)?(?:\s|$)',
            'capacity_ml': r'(\d+)\s*ml(?:\s|$)',
            'size_inches': r'(\d+(?:\.\d+)?)\s*(?:inch|pouces?)(?:\s|$)',
            'size_cm': r'(\d+(?:\.\d+)?)\s*cm(?:\s|$)',
            'weight_kg': r'(\d+(?:\.\d+)?)\s*kg(?:\s|$)',
            'weight_g': r'(\d+)\s*g(?:rammes?)?(?:\s|$)',
            'power_watts': r'(\d+)\s*w(?:atts?)?(?:\s|$)',
            'voltage': r'(\d+)\s*v(?:olts?)?(?:\s|$)',
            'memory_gb': r'(\d+)\s*gb(?:\s|$)',
            'memory_mb': r'(\d+)\s*mb(?:\s|$)',
            'screen_size': r'(\d+(?:\.\d+)?)\s*(?:"|pouces)(?:\s|$)',
            'model_numbers': r'[a-z]+(\d+)(?:\s|$)',
        }
        
        for spec_type, pattern in patterns.items():
            matches = re.findall(pattern, name_lower)
            if matches:
                try:
                    specs[spec_type] = float(matches[0]) if '.' in matches[0] else int(matches[0])
                except (ValueError, IndexError):
                    continue
        
        return specs

    def _are_specifications_compatible(self, specs1, specs2):
        """Vérifie si deux ensembles de spécifications sont compatibles"""
        if not specs1 or not specs2:
            return True
        
        critical_specs = [
            'capacity_liters', 'capacity_ml', 'size_inches', 'size_cm',
            'weight_kg', 'power_watts', 'voltage', 'memory_gb', 'screen_size'
        ]
        
        for spec in critical_specs:
            if spec in specs1 and spec in specs2:
                val1, val2 = specs1[spec], specs2[spec]
                
                # Tolérance pour les mesures (5% de différence max)
                if spec in ['size_inches', 'size_cm', 'weight_kg', 'screen_size']:
                    tolerance = max(val1, val2) * 0.05
                    if abs(val1 - val2) > tolerance:
                        return False
                else:
                    # Pour les capacités, puissance, etc. : différence exacte non autorisée
                    if val1 != val2:
                        return False
        
        # Vérifier les numéros de modèle
        if 'model_numbers' in specs1 and 'model_numbers' in specs2:
            if specs1['model_numbers'] != specs2['model_numbers']:
                return False
        
        return True

    def _has_only_number_difference_improved(self, name1, name2):
        """Version améliorée qui vérifie les spécifications critiques"""
        if not name1 or not name2:
            return False
        
        # Extraire les spécifications des deux noms
        specs1 = self._extract_numeric_specifications(name1)
        specs2 = self._extract_numeric_specifications(name2)
        
        # Si les spécifications ne sont pas compatibles, ce ne sont pas les mêmes produits
        if not self._are_specifications_compatible(specs1, specs2):
            return False
        
        # Vérifier si c'est juste une différence de numérotation non critique
        name1_no_numbers = re.sub(r'\d+', 'X', name1.lower())
        name2_no_numbers = re.sub(r'\d+', 'X', name2.lower())
        
        return name1_no_numbers == name2_no_numbers and name1_no_numbers != ''

    def _get_similarity_details_improved(self, name1, name2):
        """Version améliorée de l'analyse de similarité"""
        if not name1 or not name2:
            return {
                'similarity_score': 0.0,
                'similarity_percentage': 0.0,
                'match_type': 'no_match',
                'details': 'Noms manquants',
                'specifications_analysis': None
            }
        
        # Calculer la similarité de base
        similarity = self._calculate_name_similarity(name1, name2)
        
        # Analyser les spécifications
        specs1 = self._extract_numeric_specifications(name1)
        specs2 = self._extract_numeric_specifications(name2)
        specs_compatible = self._are_specifications_compatible(specs1, specs2)
        
        # Déterminer le type de correspondance
        match_type = 'no_match'
        details = ''
        
        if similarity >= 0.99 and specs_compatible:
            match_type = 'high_similarity'
            details = f'Similarité très élevée ({similarity:.4f}) avec spécifications compatibles'
        elif similarity >= 0.95 and specs_compatible:
            match_type = 'good_similarity'
            details = f'Bonne similarité ({similarity:.4f}) avec spécifications compatibles'
        elif self._has_only_dash_difference(name1, name2):
            match_type = 'dash_difference'
            details = 'Différence de tiret/underscore uniquement'
        elif self._has_only_number_difference_improved(name1, name2):
            match_type = 'safe_number_difference'
            details = 'Différence numérique non critique uniquement'
        elif similarity >= 0.8:
            if specs_compatible:
                match_type = 'moderate_similarity'
                details = f'Similarité modérée ({similarity:.4f}) avec spécifications compatibles'
            else:
                match_type = 'different_specifications'
                details = f'Similarité modérée ({similarity:.4f}) mais spécifications différentes'
        else:
            match_type = 'low_similarity'
            details = f'Faible similarité ({similarity:.4f})'
        
        return {
            'similarity_score': round(similarity, 4),
            'similarity_percentage': round(similarity * 100, 2),
            'match_type': match_type,
            'details': details,
            'specifications_analysis': {
                'specs1': specs1,
                'specs2': specs2,
                'compatible': specs_compatible
            }
        }





    @http.route('/api/deduplicate_products_advanced', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def deduplicate_products_advanced(self, **kwargs):
        """Déduplication avancée avec gestion des tirets et chiffres et scores de similarité"""
        try:
            similarity_threshold = float(kwargs.get('similarity_threshold', 0.99))
            test_mode = kwargs.get('test_mode', 'false').lower() == 'true'
            include_dash_differences = kwargs.get('include_dash_differences', 'true').lower() == 'true'
            include_number_differences = kwargs.get('include_number_differences', 'true').lower() == 'true'
            
            user = request.env['res.users'].sudo().browse(request.env.uid)
            if not user or user._is_public():
                admin_user = request.env.ref('base.user_admin')
                request.env = request.env(user=admin_user.id)

            all_products = request.env['product.template'].sudo().search([('active', '=', True)])
            
            _logger.info(f"Déduplication avancée de {len(all_products)} produits...")
            
            # Grouper les produits similaires
            similar_groups = defaultdict(list)
            processed_products = set()
            
            for i, product1 in enumerate(all_products):
                if product1.id in processed_products:
                    continue
                
                if i % 100 == 0:
                    _logger.info(f"Analysé {i}/{len(all_products)} produits pour déduplication...")
                    
                current_group = [{'product': product1, 'similarity_details': None}]
                processed_products.add(product1.id)
                
                for j, product2 in enumerate(all_products[i+1:], i+1):
                    if product2.id in processed_products:
                        continue
                    
                    should_group = False
                    similarity_details = self._get_similarity_details_improved(product1.name, product2.name)
                    similarity = similarity_details['similarity_score']
                    match_reason = None
                    
                    # Vérifier la similarité élevée
                    if similarity >= similarity_threshold:
                        should_group = True
                        match_reason = f"Similarité élevée ({similarity:.2%})"
                    
                    # Vérifier les différences de tirets
                    elif include_dash_differences and self._has_only_dash_difference(product1.name, product2.name):
                        should_group = True
                        match_reason = "Différence de tiret uniquement"
                    
                    # Vérifier les différences de chiffres
                    elif include_number_differences and self._has_only_number_difference_improved(product1.name, product2.name):
                        should_group = True
                        match_reason = "Différence de chiffre uniquement"
                    
                    if should_group:
                        current_group.append({
                            'product': product2, 
                            'similarity_details': similarity_details,
                            'match_reason': match_reason
                        })
                        processed_products.add(product2.id)
                        _logger.info(f"Produits groupés: '{product1.name}' et '{product2.name}' - {match_reason}")
                
                if len(current_group) > 1:
                    similar_groups[f"group_{len(similar_groups)}"] = current_group
            
            # Traiter chaque groupe
            merged_count = 0
            deleted_count = 0
            merge_details = []
            
            for group_name, group_items in similar_groups.items():
                _logger.info(f"Traitement du groupe {group_name} avec {len(group_items)} produits")
                
                products = [item['product'] for item in group_items]
                
                # Séparer les produits avec et sans opérations
                products_with_operations = [p for p in products if self._has_operations(p)]
                products_without_operations = [p for p in products if not self._has_operations(p)]
                
                # Déterminer le produit à conserver
                if products_with_operations:
                    product_to_keep = max(products_with_operations, 
                                        key=lambda p: self._get_product_completeness_score_simple(p))
                    products_to_remove = [p for p in products if p.id != product_to_keep.id]
                else:
                    product_to_keep = max(products, 
                                        key=lambda p: self._get_product_completeness_score_simple(p))
                    products_to_remove = [p for p in products if p.id != product_to_keep.id]
                
                group_detail = {
                    "group_name": group_name,
                    "product_kept": {
                        "id": product_to_keep.id,
                        "name": product_to_keep.name,
                        "has_operations": self._has_operations(product_to_keep),
                        "completeness_score": self._get_product_completeness_score_simple(product_to_keep),
                        "category": product_to_keep.categ_id.name if product_to_keep.categ_id else 'Sans catégorie'
                    },
                    "products_removed": [],
                    "similarity_analysis": []
                }
                
                # Ajouter l'analyse de similarité pour chaque produit du groupe
                for item in group_items:
                    if item['similarity_details']:
                        group_detail["similarity_analysis"].append({
                            "product_name": item['product'].name,
                            "similarity_details": item['similarity_details'],
                            "match_reason": item.get('match_reason', 'Produit principal')
                        })
                
                # Fusionner et supprimer
                if not test_mode:
                    for product_to_remove in products_to_remove:
                        try:
                            # Calculer la similarité avec le produit à conserver
                            similarity_with_kept = self._get_similarity_details_improved(
                                product_to_keep.name, product_to_remove.name
                            )
                            
                            group_detail["products_removed"].append({
                                "id": product_to_remove.id,
                                "name": product_to_remove.name,
                                "has_operations": self._has_operations(product_to_remove),
                                "completeness_score": self._get_product_completeness_score_simple(product_to_remove),
                                "category": product_to_remove.categ_id.name if product_to_remove.categ_id else 'Sans catégorie',
                                "similarity_with_kept": similarity_with_kept
                            })
                            
                            # Fusionner les données
                            self._merge_product_data(product_to_keep, product_to_remove)
                            
                            # Supprimer le produit en double
                            product_to_remove.sudo().unlink()
                            deleted_count += 1
                            
                        except Exception as e:
                            _logger.error(f"Erreur lors de la suppression du produit {product_to_remove.name}: {str(e)}")
                            if group_detail["products_removed"]:
                                group_detail["products_removed"].pop()
                else:
                    # En mode test, juste enregistrer les détails
                    for product_to_remove in products_to_remove:
                        similarity_with_kept = self._get_similarity_details_improved(
                            product_to_keep.name, product_to_remove.name
                        )
                        
                        group_detail["products_removed"].append({
                            "id": product_to_remove.id,
                            "name": product_to_remove.name,
                            "has_operations": self._has_operations(product_to_remove),
                            "completeness_score": self._get_product_completeness_score_simple(product_to_remove),
                            "category": product_to_remove.categ_id.name if product_to_remove.categ_id else 'Sans catégorie',
                            "similarity_with_kept": similarity_with_kept
                        })
                
                merge_details.append(group_detail)
                merged_count += 1
            
            result = {
                "success": True,
                "test_mode": test_mode,
                "message": f"Déduplication avancée terminée" if not test_mode else "Mode test - Aucune modification effectuée",
                "parameters": {
                    "similarity_threshold": similarity_threshold,
                    "include_dash_differences": include_dash_differences,
                    "include_number_differences": include_number_differences
                },
                "statistics": {
                    "total_products_analyzed": len(all_products),
                    "similar_groups_found": len(similar_groups),
                    "groups_processed": merged_count,
                    "products_deleted": deleted_count,
                    "avg_similarity_per_group": self._calculate_avg_similarity_per_group(merge_details)
                },
                "details": {
                    "merge_details": merge_details[:20]  # Limiter l'affichage
                }
            }
            
            _logger.info(f"Déduplication terminée: {merged_count} groupes traités, {deleted_count} produits supprimés")
            
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(result, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
            )
            
        except Exception as e:
            _logger.error(f"Erreur lors de la déduplication avancée: {str(e)}", exc_info=True)
            return werkzeug.wrappers.Response(
                status=500,
                content_type='application/json; charset=utf-8',
                response=json.dumps({
                    "success": False,
                    "error": f"Erreur lors de la déduplication avancée: {str(e)}"
                })
            )


    def _calculate_avg_similarity_per_group(self, merge_details):
        """Calcule la similarité moyenne par groupe"""
        if not merge_details:
            return 0.0
        
        total_similarity = 0
        total_comparisons = 0
        
        for group in merge_details:
            for analysis in group.get('similarity_analysis', []):
                if analysis.get('similarity_details', {}).get('similarity_score'):
                    total_similarity += analysis['similarity_details']['similarity_score']
                    total_comparisons += 1
        
        return round(total_similarity / total_comparisons if total_comparisons > 0 else 0.0, 4)

    # ==================== ENDPOINTS DE SCRAPING (EXISTANTS) ====================

    @http.route('/api/scrape_products_full', methods=['GET'], type='http', auth='none', cors="*")
    def scrape_products_full(self, **kwargs):
        """Scrape des produits depuis une URL avec détails complets"""
        target_url = kwargs.get('target_url')
        fetch_details = kwargs.get('fetch_details', 'false').lower() == 'true'
        save_to_file = kwargs.get('save_to_file', 'true').lower() == 'true'
        save_to_db = kwargs.get('save_to_db', 'false').lower() == 'true'
        check_existing = kwargs.get('check_existing', 'false').lower() == 'true'

        if not target_url:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                response=json.dumps({"error": "Veuillez fournir l'URL cible via le paramètre 'target_url'."})
            )

        try:
            response = requests.get(target_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            products = soup.select("ul.products li.product")
            product_data = []

            for product in products:
                title = product.select_one("h2.woocommerce-loop-product__title")
                link = product.select_one("a.woocommerce-LoopProduct-link")
                image = product.select_one("img")
                title_text = title.text.replace('  ', ' ') if title else "Sans titre"

                product_info = {
                    "title": title_text.strip() if title else None,
                    "link": link["href"] if link else None,
                    "image": image.get("src") if image else None,
                }

                if fetch_details and product_info["link"]:
                    try:
                        details_produits = self.fetch_page_text(target_url=product_info["link"])
                        product_info["summary_text"] = details_produits.get("summary_text", None)
                        product_info["images"] = details_produits.get("images", [])
                        product_info["categories"] = details_produits.get("categories", [])
                        product_info["tags"] = details_produits.get("tags", [])
                    except Exception as e:
                        product_info["detail_fetch_error"] = str(e)

                product_data.append(product_info)

            page_data = {
                "url": target_url,
                "scrape_date": datetime.datetime.now().isoformat(),
                "produits_nbre": len(product_data),
                "produits": product_data
            }

            if check_existing:
                product_titles = [p['title'] for p in product_data]
                existing_products = request.env['product.template'].sudo().search([('name', 'in', product_titles)])
                existing_product_titles = set(existing_products.mapped('name'))

                for product in product_data:
                    product['exists_in_db'] = product['title'] in existing_product_titles
                    # Ajouter les détails de similarité pour les produits existants
                    if product['exists_in_db']:
                        existing_product = existing_products.filtered(lambda p: p.name == product['title'])
                        if existing_product:
                            product['similarity_details'] = {
                                'similarity_score': 1.0,
                                'similarity_percentage': 100.0,
                                'match_type': 'exact_match',
                                'details': 'Correspondance exacte trouvée'
                            }
                    else:
                        product['similarity_details'] = {
                            'similarity_score': 0.0,
                            'similarity_percentage': 0.0,
                            'match_type': 'no_match',
                            'details': 'Aucune correspondance trouvée'
                        }
            else:
                for product in product_data:
                    product['exists_in_db'] = False
                    product['similarity_details'] = {
                        'similarity_score': 0.0,
                        'similarity_percentage': 0.0,
                        'match_type': 'not_checked',
                        'details': 'Vérification non effectuée'
                    }

            if save_to_db:
                default_category_id = self.ensure_default_category()
                
                for product in product_data:
                    existing_product = request.env['product.template'].sudo().search([
                        ('name', '=', product['title'])
                    ], limit=1)
                    
                    if not existing_product:
                        image_base64 = self.get_image_base64(product.get('image'))
                        categ_id = self.get_category_id(product.get('categories', []))
                        if not categ_id:
                            categ_id = default_category_id
                        
                        product_vals = {
                            'name': product['title'],
                            'description': product.get('summary_text', ''),
                            'categ_id': categ_id,
                            'type': 'product',
                            'sale_ok': True,
                            'purchase_ok': True,
                        }
                        
                        if image_base64:
                            product_vals['image_1920'] = image_base64
                        
                        try:
                            new_product = request.env['product.template'].sudo().create(product_vals)
                            
                            # Ajouter les images supplémentaires
                            images = product.get('images', [])
                            # for i, img in enumerate(images[:4]):
                            #     if img.get('src'):
                            #         img_base64 = self.get_image_base64(img['src'])
                            #         if img_base64:
                            #             request.env['product.image'].sudo().create({
                            #                 'name': f"{product['title']} - Image {i+1}",
                            #                 'product_tmpl_id': new_product.id,
                            #                 'image_1920': img_base64
                            #             })
                        except Exception as e:
                            _logger.error(f"Erreur lors de la création du produit {product['title']}: {str(e)}")
                
                page_data["saved_to_db"] = True
            else:
                page_data["saved_to_db"] = False

            if save_to_file:
                data_dir = self._get_data_dir()
                parsed_url = urllib.parse.urlparse(target_url)
                category = parsed_url.path.split('/')[-2] if parsed_url.path.count('/') > 1 else 'uncategorized'
                domain = parsed_url.netloc.replace('.', '_')
                
                filename = f"products_{domain}_{category}.json"
                file_path = os.path.join(data_dir, filename)

                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(page_data, f, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
                    page_data["file_saved"] = file_path
                except Exception as e:
                    page_data["file_save_error"] = str(e)

            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(page_data, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                status=500,
                content_type='application/json; charset=utf-8',
                response=json.dumps({"error": f"Erreur lors du scraping : {str(e)}"})
            )

    def fetch_page_text(self, target_url):
        """Récupère le texte détaillé d'une page produit"""
        if not target_url:
            return {"error": "URL cible manquante"}

        try:
            response = requests.get(target_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            summary_section = soup.select_one('div.summary.entry-summary')
            if not summary_section:
                return {"error": "Section spécifiée non trouvée"}

            title_element = summary_section.select_one('h1.product_title.entry-title')
            title_text = title_element.get_text(strip=True) if title_element else "Titre non trouvé"

            description_section = summary_section.select_one('div.woocommerce-product-details__short-description')
            if description_section:
                paragraphs = description_section.find_all('p')
                summary_text = "\n".join(p.get_text(strip=True) for p in paragraphs)
            else:
                summary_text = summary_section.get_text(separator='\n', strip=True)

            gallery_section = soup.select_one('div.woocommerce-product-gallery')
            images = []
            if gallery_section:
                for img in gallery_section.select('div.woocommerce-product-gallery__image img'):
                    images.append({
                        "src": img.get("data-large_image") or img.get("src")
                    })

            category_element = summary_section.select_one('span.posted_in')
            categories = [a.get_text(strip=True) for a in category_element.select('a')] if category_element else []

            tag_element = summary_section.select_one('span.tagged_as')
            tags = [a.get_text(strip=True) for a in tag_element.select('a')] if tag_element else []

            return {
                "title": title_text,
                "summary_text": summary_text,
                "images": images,
                "categories": categories,
                "tags": tags
            }

        except Exception as e:
            return {"error": f"Erreur lors de la récupération : {str(e)}"}

    # ==================== ENDPOINTS UTILITAIRES ====================

    @http.route('/api/list_product_files', methods=['GET'], type='http', auth='none', cors="*")
    def list_product_files(self, **kwargs):
        """Liste tous les fichiers de produits disponibles"""
        data_dir = self._get_data_dir()
        
        try:
            files = [f for f in os.listdir(data_dir) if f.startswith('products_') and f.endswith('.json')]
            
            file_info = []
            for file_name in files:
                file_path = os.path.join(data_dir, file_name)
                file_stat = os.stat(file_path)
                
                parts = file_name.replace('products_', '').replace('.json', '').split('_')
                domain = parts[0].replace('_', '.')
                category = parts[1] if len(parts) > 1 else 'uncategorized'
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        product_count = data.get('produits_nbre', 0)
                except:
                    product_count = 0
                
                file_info.append({
                    'file_name': file_name,
                    'domain': domain,
                    'category': category,
                    'size': file_stat.st_size,
                    'modified': datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    'product_count': product_count
                })
            
            file_info.sort(key=lambda x: x['modified'], reverse=True)
            
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(file_info, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
            )
            
        except Exception as e:
            return werkzeug.wrappers.Response(
                status=500,
                content_type='application/json; charset=utf-8',
                response=json.dumps({"error": f"Erreur lors de la lecture du répertoire : {str(e)}"})
            )

    @http.route('/api/product_statistics', methods=['GET'], type='http', auth='none', cors="*")
    def product_statistics(self, **kwargs):
        """Statistiques complètes sur les produits avec scores de similarité"""
        try:
            all_products = request.env['product.template'].sudo().search([('active', '=', True)])
            include_similarity_analysis = kwargs.get('include_similarity_analysis', 'false').lower() == 'true'
            
            stats = {
                'total_products': len(all_products),
                'products_with_operations': 0,
                'products_without_operations': 0,
                'products_with_images': 0,
                'products_without_images': 0,
                'products_with_description': 0,
                'products_without_description': 0,
                'products_by_type': {},
                'products_by_category': {},
                'completeness_distribution': {
                    'very_complete': 0,    # Score >= 10
                    'complete': 0,         # Score 7-9
                    'partial': 0,          # Score 4-6
                    'minimal': 0           # Score < 4
                },
                'similarity_analysis': {
                    'potential_duplicates_99': 0,
                    'potential_duplicates_95': 0,
                    'dash_differences': 0,
                    'number_differences': 0
                } if include_similarity_analysis else None
            }
            
            # Analyse de base
            for product in all_products:
                # Opérations
                if self._has_operations(product):
                    stats['products_with_operations'] += 1
                else:
                    stats['products_without_operations'] += 1
                
                # Images
                if product.image_1920:
                    stats['products_with_images'] += 1
                else:
                    stats['products_without_images'] += 1
                
                # Description
                if product.description:
                    stats['products_with_description'] += 1
                else:
                    stats['products_without_description'] += 1
                
                # Type
                product_type = product.type
                if product_type not in stats['products_by_type']:
                    stats['products_by_type'][product_type] = 0
                stats['products_by_type'][product_type] += 1
                
                # Catégorie
                category_name = product.categ_id.name if product.categ_id else 'Sans catégorie'
                if category_name not in stats['products_by_category']:
                    stats['products_by_category'][category_name] = 0
                stats['products_by_category'][category_name] += 1
                
                # Score de complétude
                score = self._get_product_completeness_score(product)
                if score >= 10:
                    stats['completeness_distribution']['very_complete'] += 1
                elif score >= 7:
                    stats['completeness_distribution']['complete'] += 1
                elif score >= 4:
                    stats['completeness_distribution']['partial'] += 1
                else:
                    stats['completeness_distribution']['minimal'] += 1
            
            # Analyse de similarité si demandée
            if include_similarity_analysis:
                _logger.info("Analyse de similarité en cours...")
                processed = set()
                
                for i, product1 in enumerate(all_products):
                    if product1.id in processed:
                        continue
                    
                    if i % 200 == 0:
                        _logger.info(f"Analyse de similarité: {i}/{len(all_products)} produits traités")
                    
                    for j, product2 in enumerate(all_products[i+1:], i+1):
                        if product2.id in processed:
                            continue
                        
                        similarity_details = self._get_similarity_details(product1.name, product2.name)
                        similarity = similarity_details['similarity_score']
                        
                        if similarity >= 0.99:
                            stats['similarity_analysis']['potential_duplicates_99'] += 1
                            processed.add(product2.id)
                        elif similarity >= 0.95:
                            stats['similarity_analysis']['potential_duplicates_95'] += 1
                            processed.add(product2.id)
                        elif self._has_only_dash_difference(product1.name, product2.name):
                            stats['similarity_analysis']['dash_differences'] += 1
                            processed.add(product2.id)
                        elif self._has_only_number_difference(product1.name, product2.name):
                            stats['similarity_analysis']['number_differences'] += 1
                            processed.add(product2.id)
                    
                    processed.add(product1.id)
            
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(stats, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
            )
            
        except Exception as e:
            return werkzeug.wrappers.Response(
                status=500,
                content_type='application/json; charset=utf-8',
                response=json.dumps({"error": f"Erreur lors du calcul des statistiques : {str(e)}"})
            )

    @http.route('/api/compare_products', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def compare_products(self, **kwargs):
        """Compare deux produits spécifiques avec score de similarité détaillé"""
        try:
            product1_id = kwargs.get('product1_id')
            product2_id = kwargs.get('product2_id')
            
            if not product1_id or not product2_id:
                return werkzeug.wrappers.Response(
                    status=400,
                    content_type='application/json; charset=utf-8',
                    response=json.dumps({"error": "product1_id et product2_id requis"})
                )
            
            try:
                product1_id = int(product1_id)
                product2_id = int(product2_id)
            except ValueError:
                return werkzeug.wrappers.Response(
                    status=400,
                    content_type='application/json; charset=utf-8',
                    response=json.dumps({"error": "IDs de produits invalides"})
                )
            
            product1 = request.env['product.template'].sudo().browse(product1_id)
            product2 = request.env['product.template'].sudo().browse(product2_id)
            
            if not product1.exists() or not product2.exists():
                return werkzeug.wrappers.Response(
                    status=404,
                    content_type='application/json; charset=utf-8',
                    response=json.dumps({"error": "Un ou plusieurs produits non trouvés"})
                )
            
            # Analyse de similarité détaillée
            similarity_details = self._get_similarity_details(product1.name, product2.name)
            
            # Comparaison détaillée
            comparison = {
                "product1": {
                    "id": product1.id,
                    "name": product1.name,
                    "description": product1.description or "",
                    "list_price": product1.list_price,
                    "standard_price": product1.standard_price,
                    "category": product1.categ_id.name if product1.categ_id else None,
                    "type": product1.type,
                    "has_image": bool(product1.image_1920),
                    "has_operations": self._has_operations(product1),
                    "completeness_score": self._get_product_completeness_score(product1),
                    "barcode": product1.barcode or "",
                    "default_code": product1.default_code or "",
                    "weight": product1.weight,
                    "volume": product1.volume
                },
                "product2": {
                    "id": product2.id,
                    "name": product2.name,
                    "description": product2.description or "",
                    "list_price": product2.list_price,
                    "standard_price": product2.standard_price,
                    "category": product2.categ_id.name if product2.categ_id else None,
                    "type": product2.type,
                    "has_image": bool(product2.image_1920),
                    "has_operations": self._has_operations(product2),
                    "completeness_score": self._get_product_completeness_score(product2),
                    "barcode": product2.barcode or "",
                    "default_code": product2.default_code or "",
                    "weight": product2.weight,
                    "volume": product2.volume
                },
                "similarity_analysis": similarity_details,
                "comparison_analysis": {
                    "name_differences": self._analyze_name_differences(product1.name, product2.name),
                    "completeness_comparison": {
                        "product1_score": self._get_product_completeness_score(product1),
                        "product2_score": self._get_product_completeness_score(product2),
                        "better_product": "product1" if self._get_product_completeness_score(product1) > self._get_product_completeness_score(product2) else "product2"
                    },
                    "operations_comparison": {
                        "product1_has_operations": self._has_operations(product1),
                        "product2_has_operations": self._has_operations(product2),
                        "safer_to_keep": "product1" if self._has_operations(product1) and not self._has_operations(product2) else 
                                       "product2" if self._has_operations(product2) and not self._has_operations(product1) else "both_or_neither"
                    }
                },
                "recommended_action": self._get_recommended_action(product1, product2, similarity_details)
            }
            
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(comparison, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
            )
            
        except Exception as e:
            _logger.error(f"Erreur lors de la comparaison: {str(e)}", exc_info=True)
            return werkzeug.wrappers.Response(
                status=500,
                content_type='application/json; charset=utf-8',
                response=json.dumps({
                    "success": False,
                    "error": f"Erreur lors de la comparaison: {str(e)}"
                })
            )

    def _analyze_name_differences(self, name1, name2):
        """Analyse détaillée des différences entre deux noms"""
        if not name1 or not name2:
            return {"error": "Noms manquants"}
        
        # Normaliser
        name1_clean = name1.lower().strip()
        name2_clean = name2.lower().strip()
        
        # Analyser les différences
        differences = {
            "has_dash_difference": self._has_only_dash_difference(name1, name2),
            "has_number_difference": self._has_only_number_difference(name1, name2),
            "character_differences": [],
            "word_differences": [],
            "length_difference": abs(len(name1_clean) - len(name2_clean))
        }
        
        # Différences de caractères
        matcher = difflib.SequenceMatcher(None, name1_clean, name2_clean)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                differences["character_differences"].append({
                    "type": tag,
                    "name1_part": name1_clean[i1:i2],
                    "name2_part": name2_clean[j1:j2],
                    "position": {"name1": [i1, i2], "name2": [j1, j2]}
                })
        
        # Différences de mots
        words1 = name1_clean.split()
        words2 = name2_clean.split()
        
        words_only_in_1 = set(words1) - set(words2)
        words_only_in_2 = set(words2) - set(words1)
        
        differences["word_differences"] = {
            "only_in_name1": list(words_only_in_1),
            "only_in_name2": list(words_only_in_2),
            "common_words": list(set(words1) & set(words2))
        }
        
        return differences

    @http.route('/api/bulk_similarity_check', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def bulk_similarity_check(self, **kwargs):
        """Vérification de similarité en lot pour une liste de noms de produits"""
        try:
            import json as json_module
            
            # Récupérer les données POST
            if hasattr(request, 'httprequest') and request.httprequest.data:
                try:
                    post_data = json_module.loads(request.httprequest.data.decode('utf-8'))
                    product_names = post_data.get('product_names', [])
                except:
                    product_names = []
            else:
                product_names = []
            
            # Fallback: essayer de récupérer depuis les paramètres
            if not product_names:
                names_param = kwargs.get('product_names', '')
                if names_param:
                    try:
                        product_names = json_module.loads(names_param)
                    except:
                        product_names = names_param.split(',') if names_param else []
            
            similarity_threshold = float(kwargs.get('similarity_threshold', 0.95))
            
            if not product_names:
                return werkzeug.wrappers.Response(
                    status=400,
                    content_type='application/json; charset=utf-8',
                    response=json.dumps({"error": "Liste de noms de produits requise (product_names)"})
                )
            
            # Récupérer tous les produits existants
            existing_products = request.env['product.template'].sudo().search([('active', '=', True)])
            
            results = []
            
            for input_name in product_names:
                if not input_name or not input_name.strip():
                    continue
                
                input_name = input_name.strip()
                best_matches = []
                
                # Comparer avec tous les produits existants
                for existing_product in existing_products:
                    similarity_details = self._get_similarity_details(input_name, existing_product.name)
                    
                    if similarity_details['similarity_score'] >= similarity_threshold:
                        best_matches.append({
                            "existing_product": {
                                "id": existing_product.id,
                                "name": existing_product.name,
                                "category": existing_product.categ_id.name if existing_product.categ_id else None,
                                "has_operations": self._has_operations(existing_product),
                                "completeness_score": self._get_product_completeness_score(existing_product)
                            },
                            "similarity_details": similarity_details
                        })
                
                # Trier par score de similarité décroissant
                best_matches.sort(key=lambda x: x['similarity_details']['similarity_score'], reverse=True)
                
                results.append({
                    "input_name": input_name,
                    "matches_found": len(best_matches),
                    "best_matches": best_matches[:5],  # Limiter aux 5 meilleurs
                    "has_exact_match": any(match['similarity_details']['similarity_score'] == 1.0 for match in best_matches),
                    "best_similarity_score": best_matches[0]['similarity_details']['similarity_score'] if best_matches else 0.0
                })
            
            summary = {
                "total_names_checked": len(product_names),
                "names_with_matches": sum(1 for r in results if r['matches_found'] > 0),
                "names_with_exact_matches": sum(1 for r in results if r['has_exact_match']),
                "avg_best_similarity": round(sum(r['best_similarity_score'] for r in results) / len(results) if results else 0, 4)
            }
            
            response_data = {
                "success": True,
                "parameters": {
                    "similarity_threshold": similarity_threshold,
                    "total_existing_products": len(existing_products)
                },
                "summary": summary,
                "results": results
            }
            
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(response_data, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
            )
            
        except Exception as e:
            _logger.error(f"Erreur lors de la vérification en lot: {str(e)}", exc_info=True)
            return werkzeug.wrappers.Response(
                status=500,
                content_type='application/json; charset=utf-8',
                response=json.dumps({
                    "success": False,
                    "error": f"Erreur lors de la vérification en lot: {str(e)}"
                })
            )


    # # ==================== NOUVELLE FONCTION DE COMPLÉTION AUTOMATIQUE ====================

    def _merge_product_data_advanced(self, target_product, source_product):
        """Fusionne les données du produit source vers le produit cible de manière avancée"""
        update_vals = {}
        merged_fields = []
        
        # S'assurer que le type est 'product' (stockable)
        if target_product.type != 'product':
            update_vals['type'] = 'product'
            merged_fields.append('type')
        
        # Fusionner les descriptions
        if not target_product.description and source_product.description:
            update_vals['description'] = source_product.description
            merged_fields.append('description')
        elif (source_product.description and target_product.description and
            len(source_product.description) > len(target_product.description)):
            # Combiner les descriptions si celle de la source est plus longue
            combined_desc = f"{target_product.description}\n\n{source_product.description}"
            update_vals['description'] = combined_desc
            merged_fields.append('description (combined)')
        
        # Fusionner les prix
        price_fields = ['list_price', 'standard_price']
        for field in price_fields:
            target_val = getattr(target_product, field, 0)
            source_val = getattr(source_product, field, 0)
            
            if not target_val and source_val:
                update_vals[field] = source_val
                merged_fields.append(field)
            elif source_val > target_val:
                # Prendre le prix le plus élevé
                update_vals[field] = source_val
                merged_fields.append(f'{field} (higher)')
        
        # Fusionner les champs personnalisés
        custom_price_fields = ['creditorder_price', 'promo_price', 'rate_price']
        for field in custom_price_fields:
            if hasattr(target_product, field) and hasattr(source_product, field):
                target_val = getattr(target_product, field, 0)
                source_val = getattr(source_product, field, 0)
                
                if not target_val and source_val:
                    update_vals[field] = source_val
                    merged_fields.append(field)
        
        # Fusionner les autres champs
        other_fields = ['volume', 'weight', 'barcode', 'default_code']
        for field in other_fields:
            target_val = getattr(target_product, field, None)
            source_val = getattr(source_product, field, None)
            
            if not target_val and source_val:
                update_vals[field] = source_val
                merged_fields.append(field)
        
        # Fusionner l'image principale
        if not target_product.image_1920 and source_product.image_1920:
            update_vals['image_1920'] = source_product.image_1920
            merged_fields.append('main_image')
        
        # Fusionner les images supplémentaires
        image_fields = ['image_1', 'image_2', 'image_3', 'image_4']
        for field in image_fields:
            if hasattr(target_product, field) and hasattr(source_product, field):
                target_img = getattr(target_product, field, None)
                source_img = getattr(source_product, field, None)
                
                if not target_img and source_img:
                    update_vals[field] = source_img
                    merged_fields.append(field)
        
        # Fusionner la catégorie
        if not target_product.categ_id and source_product.categ_id:
            update_vals['categ_id'] = source_product.categ_id.id
            merged_fields.append('category')
        
        # S'assurer que les flags de vente/achat sont activés
        if not target_product.sale_ok:
            update_vals['sale_ok'] = True
            merged_fields.append('sale_ok')
        if not target_product.purchase_ok:
            update_vals['purchase_ok'] = True
            merged_fields.append('purchase_ok')
        
        # Mettre à jour le produit cible
        if update_vals:
            target_product.sudo().write(update_vals)
            _logger.info(f"Produit {target_product.name} mis à jour avec: {merged_fields}")
        
        return merged_fields, update_vals
    

    def _get_product_completeness_score_detailed(self, product):
        """
        Calcule un score de complétude détaillé pour un produit
        Retourne un tuple (score, details) où details est un dictionnaire avec les détails de chaque champ
        """
        score = 0
        details = {}

        # Points pour les champs de base
        if product.name:
            score += 1
            details['name'] = {'has_value': True, 'score': 1}
        else:
            details['name'] = {'has_value': False, 'score': 0}

        if product.description:
            score += 3
            details['description'] = {'has_value': True, 'score': 3, 'length': len(product.description)}
        else:
            details['description'] = {'has_value': False, 'score': 0}

        if product.list_price > 0:
            score += 2
            details['list_price'] = {'has_value': True, 'score': 2, 'value': product.list_price}
        else:
            details['list_price'] = {'has_value': False, 'score': 0}

        if product.standard_price > 0:
            score += 1
            details['standard_price'] = {'has_value': True, 'score': 1, 'value': product.standard_price}
        else:
            details['standard_price'] = {'has_value': False, 'score': 0}

        # Points pour les images
        if product.image_1920:
            score += 4
            details['image_1920'] = {'has_value': True, 'score': 4}
        else:
            details['image_1920'] = {'has_value': False, 'score': 0}

        # Points pour les images supplémentaires
        if hasattr(product, 'product_image_ids'):
            image_count = len(product.product_image_ids)
            score += min(image_count, 3)
            details['additional_images'] = {'has_value': True, 'score': min(image_count, 3), 'count': image_count}
        else:
            details['additional_images'] = {'has_value': False, 'score': 0}

        # Points pour la catégorie
        if product.categ_id:
            score += 1
            details['category'] = {'has_value': True, 'score': 1, 'name': product.categ_id.name}
        else:
            details['category'] = {'has_value': False, 'score': 0}

        # Points pour les champs supplémentaires
        if product.barcode:
            score += 1
            details['barcode'] = {'has_value': True, 'score': 1, 'value': product.barcode}
        else:
            details['barcode'] = {'has_value': False, 'score': 0}

        if product.default_code:
            score += 1
            details['default_code'] = {'has_value': True, 'score': 1, 'value': product.default_code}
        else:
            details['default_code'] = {'has_value': False, 'score': 0}

        if product.weight > 0:
            score += 1
            details['weight'] = {'has_value': True, 'score': 1, 'value': product.weight}
        else:
            details['weight'] = {'has_value': False, 'score': 0}

        if product.volume > 0:
            score += 1
            details['volume'] = {'has_value': True, 'score': 1, 'value': product.volume}
        else:
            details['volume'] = {'has_value': False, 'score': 0}

        # Points pour les opérations
        if self._has_operations(product):
            score += 5
            details['operations'] = {'has_value': True, 'score': 5}
        else:
            details['operations'] = {'has_value': False, 'score': 0}

        return score, details

    @http.route('/api/auto_complete_similar_products', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def auto_complete_similar_products(self, **kwargs):
        """Complétion automatique des produits similaires avec score > 99.2%"""
        try:
            similarity_threshold = float(kwargs.get('similarity_threshold', 99.2))
            test_mode = kwargs.get('test_mode', 'true').lower() == 'true'
            delete_source = kwargs.get('delete_source', 'false').lower() == 'true'
            max_products = kwargs.get('max_products')
            
            if max_products:
                max_products = int(max_products)
            
            all_products = request.env['product.template'].sudo().search([('active', '=', True)])
            
            if max_products:
                all_products = all_products[:max_products]
            
            _logger.info(f"Analyse de {len(all_products)} produits pour complétion automatique...")
            
            # Trouver les paires similaires
            similar_pairs = []
            processed_products = set()
            
            for i, product1 in enumerate(all_products):
                if product1.id in processed_products:
                    continue
                
                if i % 100 == 0:
                    _logger.info(f"Analysé {i}/{len(all_products)} produits...")
                
                for j, product2 in enumerate(all_products[i+1:], i+1):
                    if product2.id in processed_products:
                        continue
                    
                    # Utiliser la fonction de similarité améliorée
                    similarity_details = self._get_similarity_details_improved(product1.name, product2.name)
                    similarity_percentage = similarity_details['similarity_percentage']
                    
                    # Vérifier si les spécifications sont compatibles
                    specs_compatible = similarity_details.get('specifications_analysis', {}).get('compatible', True)
                    
                    if similarity_percentage >= similarity_threshold and specs_compatible:
                        # Calculer les scores de complétude
                        score1, details1 = self._get_product_completeness_score_detailed(product1)
                        score2, details2 = self._get_product_completeness_score_detailed(product2)
                        
                        # Déterminer le produit cible (le plus complet)
                        if score1 >= score2:
                            target_product = product1
                            source_product = product2
                            target_score = score1
                            source_score = score2
                            target_details = details1
                            source_details = details2
                        else:
                            target_product = product2
                            source_product = product1
                            target_score = score2
                            source_score = score1
                            target_details = details2
                            source_details = details1
                        
                        similar_pairs.append({
                            'target_product': target_product,
                            'source_product': source_product,
                            'target_score': target_score,
                            'source_score': source_score,
                            'target_details': target_details,
                            'source_details': source_details,
                            'similarity_details': similarity_details,
                            'score_difference': target_score - source_score
                        })
                        
                        processed_products.add(source_product.id)
                        break  # Ne traiter qu'une paire par produit
                
                processed_products.add(product1.id)
            
            # Traiter les paires trouvées
            completion_results = []
            total_merged_fields = 0
            
            _logger.info(f"Trouvé {len(similar_pairs)} paires de produits similaires à compléter")
            
            for i, pair in enumerate(similar_pairs):
                target = pair['target_product']
                source = pair['source_product']
                
                _logger.info(f"Traitement de la paire {i+1}/{len(similar_pairs)}: "
                           f"'{target.name}' <- '{source.name}'")
                
                result = {
                    'pair_index': i + 1,
                    'target_product': {
                        'id': target.id,
                        'name': target.name,
                        'score_before': pair['target_score'],
                        'details_before': pair['target_details']
                    },
                    'source_product': {
                        'id': source.id,
                        'name': source.name,
                        'score': pair['source_score'],
                        'details': pair['source_details']
                    },
                    'similarity_details': pair['similarity_details'],
                    'merged_fields': [],
                    'score_improvement': 0,
                    'was_source_deleted': False,
                    'errors': []
                }
                
                if not test_mode:
                    try:
                        # Effectuer la fusion
                        merged_fields, update_vals = self._merge_product_data_advanced(target, source)
                        result['merged_fields'] = merged_fields
                        result['update_values'] = list(update_vals.keys())
                        total_merged_fields += len(merged_fields)
                        
                        # Calculer le nouveau score
                        new_score, new_details = self._get_product_completeness_score_detailed(target)
                        result['target_product']['score_after'] = new_score
                        result['target_product']['details_after'] = new_details
                        result['score_improvement'] = new_score - pair['target_score']
                        
                        # Supprimer le produit source si demandé et s'il n'a pas d'opérations
                        if delete_source and not self._has_operations(source):
                            try:
                                source.sudo().unlink()
                                result['was_source_deleted'] = True
                                _logger.info(f"Produit source supprimé: {source.name}")
                            except Exception as e:
                                result['errors'].append(f"Erreur lors de la suppression: {str(e)}")
                                _logger.error(f"Erreur lors de la suppression de {source.name}: {str(e)}")
                        
                    except Exception as e:
                        result['errors'].append(f"Erreur lors de la fusion: {str(e)}")
                        _logger.error(f"Erreur lors de la fusion {target.name} <- {source.name}: {str(e)}")
                else:
                    # Mode test : simuler la fusion
                    result['merged_fields'] = ['simulation']
                    result['score_improvement'] = 'simulated'
                
                completion_results.append(result)
            
            # Préparer le résumé
            summary = {
                'total_products_analyzed': len(all_products),
                'similar_pairs_found': len(similar_pairs),
                'pairs_processed': len(completion_results),
                'total_merged_fields': total_merged_fields if not test_mode else 'simulated',
                'products_deleted': sum(1 for r in completion_results if r['was_source_deleted']),
                'errors_count': sum(len(r['errors']) for r in completion_results),
                'avg_similarity': round(sum(p['similarity_details']['similarity_percentage'] 
                                          for p in similar_pairs) / len(similar_pairs) if similar_pairs else 0, 2),
                'avg_score_improvement': round(sum(r['score_improvement'] 
                                                 for r in completion_results 
                                                 if isinstance(r['score_improvement'], (int, float))) / 
                                             len(completion_results) if completion_results else 0, 2)
            }
            
            result = {
                'success': True,
                'test_mode': test_mode,
                'parameters': {
                    'similarity_threshold': similarity_threshold,
                    'delete_source': delete_source,
                    'max_products': max_products
                },
                'summary': summary,
                'completion_results': completion_results[:20],  # Limiter l'affichage
                'all_results_count': len(completion_results)
            }
            
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(result, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
            )
            
        except Exception as e:
            _logger.error(f"Erreur lors de la complétion automatique: {str(e)}", exc_info=True)
            return werkzeug.wrappers.Response(
                status=500,
                content_type='application/json; charset=utf-8',
                response=json.dumps({
                    "success": False,
                    "error": f"Erreur lors de la complétion automatique: {str(e)}"
                })
            )
        

    # ==================== FONCTION À AJOUTER DANS CompleteProductController ====================

    @http.route('/api/delete_all_products_without_operations', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def delete_all_products_without_operations(self, **kwargs):
        """Supprime TOUS les produits qui n'ont aucune opération (ventes, achats, mouvements de stock)"""
        try:
            # Paramètres
            test_mode = kwargs.get('test_mode', 'true').lower() == 'true'
            batch_size = int(kwargs.get('batch_size', 100))  # Traiter par lots pour éviter les timeouts
            force_delete = kwargs.get('force_delete', 'false').lower() == 'true'  # Forcer même avec des erreurs
            
            # Récupérer tous les produits actifs
            all_products = request.env['product.template'].sudo().search([('active', '=', True)])
            
            _logger.info(f"Analyse de {len(all_products)} produits pour suppression...")
            
            # Identifier les produits sans opérations
            products_to_delete = []
            products_with_operations = []
            analysis_errors = []
            
            for i, product in enumerate(all_products):
                if i % 500 == 0:
                    _logger.info(f"Analysé {i}/{len(all_products)} produits...")
                
                try:
                    has_operations = self._has_operations(product)
                    
                    product_info = {
                        'id': product.id,
                        'name': product.name,
                        'type': product.type,
                        'category': product.categ_id.name if product.categ_id else 'Sans catégorie',
                        'completeness_score': self._get_product_completeness_score(product),
                        'has_image': bool(product.image_1920),
                        'has_description': bool(product.description),
                        'list_price': product.list_price,
                        'create_date': product.create_date.isoformat() if product.create_date else None,
                        'write_date': product.write_date.isoformat() if product.write_date else None
                    }
                    
                    if has_operations:
                        products_with_operations.append(product_info)
                    else:
                        products_to_delete.append(product_info)
                        
                except Exception as e:
                    analysis_errors.append({
                        'product_id': product.id,
                        'product_name': product.name,
                        'error': str(e)
                    })
                    _logger.error(f"Erreur lors de l'analyse du produit {product.name}: {str(e)}")
            
            # Statistiques détaillées
            stats = {
                'total_products': len(all_products),
                'products_with_operations': len(products_with_operations),
                'products_without_operations': len(products_to_delete),
                'analysis_errors': len(analysis_errors),
                'percentage_to_delete': round((len(products_to_delete) / len(all_products)) * 100, 2) if all_products else 0
            }
            
            # Analyse par catégorie
            category_analysis = self._analyze_products_by_category(products_to_delete)
            
            # Mode test - retourner les informations sans supprimer
            if test_mode:
                result = {
                    "success": True,
                    "test_mode": True,
                    "message": "Mode test - Aucune suppression effectuée",
                    "statistics": stats,
                    "category_analysis": category_analysis,
                    "products_to_delete_sample": products_to_delete[:50],  # Échantillon des 50 premiers
                    "products_with_operations_sample": products_with_operations[:20],  # Échantillon des 20 premiers
                    "analysis_errors": analysis_errors,
                    "recommendations": self._get_deletion_recommendations(products_to_delete, products_with_operations)
                }
                
                return werkzeug.wrappers.Response(
                    status=200,
                    content_type='application/json; charset=utf-8',
                    headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                    response=json.dumps(result, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
                )
            
            # Mode production - effectuer les suppressions
            _logger.info(f"DÉBUT DE SUPPRESSION: {len(products_to_delete)} produits à supprimer")
            
            deleted_count = 0
            deletion_errors = []
            deletion_details = []
            
            # Traiter par lots pour éviter les timeouts
            for i in range(0, len(products_to_delete), batch_size):
                batch = products_to_delete[i:i + batch_size]
                batch_number = (i // batch_size) + 1
                total_batches = (len(products_to_delete) + batch_size - 1) // batch_size
                
                _logger.info(f"Traitement du lot {batch_number}/{total_batches} ({len(batch)} produits)")
                
                batch_deleted = 0
                batch_errors = []
                
                for product_info in batch:
                    try:
                        product = request.env['product.template'].sudo().browse(product_info['id'])
                        
                        if product.exists():
                            # Vérification finale avant suppression
                            if not self._has_operations(product) or force_delete:
                                # Collecter les informations avant suppression
                                deletion_detail = {
                                    'id': product.id,
                                    'name': product.name,
                                    'category': product.categ_id.name if product.categ_id else 'Sans catégorie',
                                    'type': product.type,
                                    'list_price': product.list_price,
                                    'create_date': product.create_date.isoformat() if product.create_date else None,
                                    'deletion_timestamp': datetime.datetime.now().isoformat()
                                }
                                
                                # Supprimer le produit
                                product.unlink()
                                deleted_count += 1
                                batch_deleted += 1
                                deletion_details.append(deletion_detail)
                                
                            else:
                                # Le produit a maintenant des opérations
                                batch_errors.append({
                                    'product_id': product_info['id'],
                                    'product_name': product_info['name'],
                                    'error': 'Le produit a maintenant des opérations - suppression annulée'
                                })
                        else:
                            # Le produit n'existe plus
                            batch_errors.append({
                                'product_id': product_info['id'],
                                'product_name': product_info['name'],
                                'error': 'Produit déjà supprimé ou inexistant'
                            })
                            
                    except Exception as e:
                        error_detail = {
                            'product_id': product_info['id'],
                            'product_name': product_info['name'],
                            'error': str(e)
                        }
                        batch_errors.append(error_detail)
                        deletion_errors.append(error_detail)
                        _logger.error(f"Erreur lors de la suppression du produit {product_info['name']}: {str(e)}")
                        
                        if not force_delete:
                            _logger.warning(f"Arrêt du lot en cours à cause de l'erreur (force_delete=False)")
                            break
                
                _logger.info(f"Lot {batch_number} terminé: {batch_deleted} supprimés, {len(batch_errors)} erreurs")
                
                # Commit après chaque lot pour éviter les rollbacks massifs
                request.env.cr.commit()
            
            # Résultat final
            result = {
                "success": True,
                "test_mode": False,
                "message": f"Suppression terminée: {deleted_count} produits supprimés sur {len(products_to_delete)} identifiés",
                "parameters": {
                    "batch_size": batch_size,
                    "force_delete": force_delete
                },
                "statistics": {
                    **stats,
                    "actually_deleted": deleted_count,
                    "deletion_errors": len(deletion_errors),
                    "deletion_success_rate": round((deleted_count / len(products_to_delete)) * 100, 2) if products_to_delete else 0
                },
                "category_analysis": category_analysis,
                "deletion_summary": {
                    "total_batches_processed": (len(products_to_delete) + batch_size - 1) // batch_size,
                    "deletion_details": deletion_details[:100],  # Limiter l'affichage
                    "deletion_errors": deletion_errors[:50]  # Limiter l'affichage des erreurs
                },
                "analysis_errors": analysis_errors,
                "performance": {
                    "products_per_second": round(deleted_count / max((datetime.datetime.now() - datetime.datetime.now()).total_seconds(), 1), 2)
                }
            }
            
            _logger.info(f"SUPPRESSION TERMINÉE: {deleted_count} produits supprimés, {len(deletion_errors)} erreurs")
            
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(result, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
            )
            
        except Exception as e:
            _logger.error(f"Erreur critique lors de la suppression massive: {str(e)}", exc_info=True)
            return werkzeug.wrappers.Response(
                status=500,
                content_type='application/json; charset=utf-8',
                response=json.dumps({
                    "success": False,
                    "error": f"Erreur critique lors de la suppression massive: {str(e)}"
                })
            )

    def _analyze_products_by_category(self, products_list):
        """Analyse les produits par catégorie"""
        category_stats = {}
        
        for product in products_list:
            category = product['category']
            if category not in category_stats:
                category_stats[category] = {
                    'count': 0,
                    'total_completeness_score': 0,
                    'with_images': 0,
                    'with_descriptions': 0,
                    'with_prices': 0,
                    'avg_completeness_score': 0
                }
            
            stats = category_stats[category]
            stats['count'] += 1
            stats['total_completeness_score'] += product['completeness_score']
            
            if product['has_image']:
                stats['with_images'] += 1
            if product['has_description']:
                stats['with_descriptions'] += 1
            if product['list_price'] > 0:
                stats['with_prices'] += 1
        
        # Calculer les moyennes
        for category in category_stats:
            stats = category_stats[category]
            if stats['count'] > 0:
                stats['avg_completeness_score'] = round(stats['total_completeness_score'] / stats['count'], 2)
                stats['image_percentage'] = round((stats['with_images'] / stats['count']) * 100, 1)
                stats['description_percentage'] = round((stats['with_descriptions'] / stats['count']) * 100, 1)
                stats['price_percentage'] = round((stats['with_prices'] / stats['count']) * 100, 1)
            
            # Supprimer le total temporaire
            del stats['total_completeness_score']
        
        # Trier par nombre de produits décroissant
        sorted_categories = dict(sorted(category_stats.items(), key=lambda x: x[1]['count'], reverse=True))
        
        return sorted_categories

    def _get_deletion_recommendations(self, products_to_delete, products_with_operations):
        """Génère des recommandations basées sur l'analyse"""
        recommendations = []
        
        total_to_delete = len(products_to_delete)
        total_with_ops = len(products_with_operations)
        
        if total_to_delete > total_with_ops:
            recommendations.append({
                'type': 'warning',
                'message': f"ATTENTION: Vous allez supprimer plus de produits ({total_to_delete}) que vous n'en gardez ({total_with_ops})",
                'suggestion': "Vérifiez que c'est bien votre intention"
            })
        
        # Analyser les produits récents
        recent_products = [p for p in products_to_delete if p.get('create_date') and 
                        (datetime.datetime.now() - datetime.datetime.fromisoformat(p['create_date'].replace('Z', '+00:00'))).days < 30]
        
        if recent_products:
            recommendations.append({
                'type': 'info',
                'message': f"{len(recent_products)} produits ont été créés dans les 30 derniers jours",
                'suggestion': "Considérez les exclure de la suppression"
            })
        
        # Analyser les produits avec prix
        products_with_price = [p for p in products_to_delete if p['list_price'] > 0]
        if products_with_price:
            recommendations.append({
                'type': 'warning',
                'message': f"{len(products_with_price)} produits ont un prix défini",
                'suggestion': "Ces produits pourraient être vendus à l'avenir"
            })
        
        # Analyser les produits avec images
        products_with_images = [p for p in products_to_delete if p['has_image']]
        if products_with_images:
            recommendations.append({
                'type': 'info',
                'message': f"{len(products_with_images)} produits ont des images",
                'suggestion': "Considérez sauvegarder les images avant suppression"
            })
        
        return recommendations

  
    @http.route('/api/delete_products_by_criteria', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def delete_products_by_criteria(self, **kwargs):
        """Supprime les produits selon des critères spécifiques"""
        try:
            # Paramètres de filtrage
            test_mode = kwargs.get('test_mode', 'true').lower() == 'true'
            
            # Critères de sélection
            max_completeness_score = kwargs.get('max_completeness_score')  # Ex: 3
            exclude_with_images = kwargs.get('exclude_with_images', 'false').lower() == 'true'
            exclude_with_prices = kwargs.get('exclude_with_prices', 'false').lower() == 'true'
            exclude_recent_days = kwargs.get('exclude_recent_days')  # Ex: 30
            categories_to_exclude = kwargs.get('categories_to_exclude', '').split(',') if kwargs.get('categories_to_exclude') else []
            categories_to_include = kwargs.get('categories_to_include', '').split(',') if kwargs.get('categories_to_include') else []
            
            # Récupérer tous les produits sans opérations
            all_products = request.env['product.template'].sudo().search([('active', '=', True)])
            products_without_operations = []
            
            for product in all_products:
                if not self._has_operations(product):
                    products_without_operations.append(product)
            
            # Appliquer les filtres
            filtered_products = []
            exclusion_reasons = {}
            
            for product in products_without_operations:
                should_exclude = False
                reasons = []
                
                # Filtre par score de complétude
                if max_completeness_score:
                    score = self._get_product_completeness_score(product)
                    if score > int(max_completeness_score):
                        should_exclude = True
                        reasons.append(f"Score trop élevé ({score} > {max_completeness_score})")
                
                # Filtre par images
                if exclude_with_images and product.image_1920:
                    should_exclude = True
                    reasons.append("A une image")
                
                # Filtre par prix
                if exclude_with_prices and product.list_price > 0:
                    should_exclude = True
                    reasons.append(f"A un prix ({product.list_price})")
                
                # Filtre par date de création
                if exclude_recent_days and product.create_date:
                    days_old = (datetime.datetime.now() - product.create_date).days
                    if days_old < int(exclude_recent_days):
                        should_exclude = True
                        reasons.append(f"Trop récent ({days_old} jours)")
                
                # Filtre par catégorie à exclure
                category_name = product.categ_id.name if product.categ_id else 'Sans catégorie'
                if categories_to_exclude and category_name in categories_to_exclude:
                    should_exclude = True
                    reasons.append(f"Catégorie exclue ({category_name})")
                
                # Filtre par catégorie à inclure
                if categories_to_include and category_name not in categories_to_include:
                    should_exclude = True
                    reasons.append(f"Catégorie non incluse ({category_name})")
                
                if should_exclude:
                    exclusion_reasons[product.id] = {
                        'name': product.name,
                        'reasons': reasons
                    }
                else:
                    filtered_products.append(product)
            
            # Préparer les informations des produits filtrés
            products_to_delete = []
            for product in filtered_products:
                products_to_delete.append({
                    'id': product.id,
                    'name': product.name,
                    'category': product.categ_id.name if product.categ_id else 'Sans catégorie',
                    'completeness_score': self._get_product_completeness_score(product),
                    'has_image': bool(product.image_1920),
                    'list_price': product.list_price,
                    'create_date': product.create_date.isoformat() if product.create_date else None
                })
            
            if test_mode:
                result = {
                    "success": True,
                    "test_mode": True,
                    "message": "Mode test - Analyse des critères de suppression",
                    "criteria_applied": {
                        "max_completeness_score": max_completeness_score,
                        "exclude_with_images": exclude_with_images,
                        "exclude_with_prices": exclude_with_prices,
                        "exclude_recent_days": exclude_recent_days,
                        "categories_to_exclude": categories_to_exclude,
                        "categories_to_include": categories_to_include
                    },
                    "statistics": {
                        "total_products": len(all_products),
                        "products_without_operations": len(products_without_operations),
                        "products_after_filtering": len(filtered_products),
                        "products_excluded_by_criteria": len(exclusion_reasons),
                        "reduction_percentage": round((1 - len(filtered_products) / len(products_without_operations)) * 100, 2) if products_without_operations else 0
                    },
                    "products_to_delete_sample": products_to_delete[:30],
                    "exclusion_reasons_sample": dict(list(exclusion_reasons.items())[:20])
                }
                
                return werkzeug.wrappers.Response(
                    status=200,
                    content_type='application/json; charset=utf-8',
                    headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                    response=json.dumps(result, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
                )
            
            # Mode production - supprimer les produits filtrés
            deleted_count = 0
            errors = []
            
            for product in filtered_products:
                try:
                    product.sudo().unlink()
                    deleted_count += 1
                except Exception as e:
                    errors.append({
                        'product_id': product.id,
                        'product_name': product.name,
                        'error': str(e)
                    })
            
            result = {
                "success": True,
                "test_mode": False,
                "message": f"Suppression sélective terminée: {deleted_count} produits supprimés",
                "criteria_applied": {
                    "max_completeness_score": max_completeness_score,
                    "exclude_with_images": exclude_with_images,
                    "exclude_with_prices": exclude_with_prices,
                    "exclude_recent_days": exclude_recent_days,
                    "categories_to_exclude": categories_to_exclude,
                    "categories_to_include": categories_to_include
                },
                "statistics": {
                    "total_products": len(all_products),
                    "products_without_operations": len(products_without_operations),
                    "products_deleted": deleted_count,
                    "deletion_errors": len(errors)
                },
                "errors": errors
            }
            
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(result, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
            )
            
        except Exception as e:
            _logger.error(f"Erreur lors de la suppression sélective: {str(e)}", exc_info=True)
            return werkzeug.wrappers.Response(
                status=500,
                content_type='application/json; charset=utf-8',
                response=json.dumps({
                    "success": False,
                    "error": f"Erreur lors de la suppression sélective: {str(e)}"
                })
            )







   
    def _has_only_space_difference(self, name1, name2):
        """
        Vérifie si la seule différence entre deux noms est la présence ou absence d'espaces
        """
        if not name1 or not name2:
            return False
        
        # Supprimer tous les espaces et comparer
        name1_no_spaces = re.sub(r'\s+', '', name1.lower())
        name2_no_spaces = re.sub(r'\s+', '', name2.lower())
        
        return name1_no_spaces == name2_no_spaces and name1_no_spaces != ''

    def _has_only_digit_difference(self, name1, name2):
        """
        Vérifie si la seule différence entre deux noms est la présence ou absence de chiffres
        """
        if not name1 or not name2:
            return False
        
        # Supprimer tous les chiffres et comparer
        name1_no_digits = re.sub(r'\d+', '', name1.lower())
        name2_no_digits = re.sub(r'\d+', '', name2.lower())
        
        return name1_no_digits == name2_no_digits and name1_no_digits != ''

    def _has_only_space_or_digit_difference(self, name1, name2):
        """
        Vérifie si la seule différence entre deux noms est des espaces et/ou des chiffres
        """
        if not name1 or not name2:
            return False
        
        # Normaliser : supprimer espaces et chiffres
        def normalize_name(name):
            # Supprimer espaces et chiffres, garder seulement les lettres et caractères spéciaux
            normalized = re.sub(r'[\s\d]+', '', name.lower())
            return normalized
        
        name1_normalized = normalize_name(name1)
        name2_normalized = normalize_name(name2)
        
        return name1_normalized == name2_normalized and name1_normalized != ''

    def _has_exact_characters_with_space_digit_diff(self, name1, name2):
        """
        Vérifie si deux noms ont exactement les mêmes caractères mais diffèrent seulement 
        par des espaces ou des chiffres
        """
        if not name1 or not name2:
            return False
        
        # Extraire tous les caractères alphabétiques et spéciaux (sans espaces ni chiffres)
        def extract_alpha_chars(name):
            return ''.join(sorted(re.findall(r'[a-zA-ZÀ-ÿ\-_]', name.lower())))
        
        chars1 = extract_alpha_chars(name1)
        chars2 = extract_alpha_chars(name2)
        
        # Vérifier si les caractères alphabétiques sont identiques
        if chars1 != chars2 or chars1 == '':
            return False
        
        # Vérifier que la différence est seulement dans les espaces/chiffres
        # Supprimer les caractères alphabétiques et voir ce qui reste
        remaining1 = re.sub(r'[a-zA-ZÀ-ÿ\-_]', '', name1)
        remaining2 = re.sub(r'[a-zA-ZÀ-ÿ\-_]', '', name2)
        
        # Ce qui reste doit être seulement des espaces et/ou des chiffres
        pattern_spaces_digits = r'^[\s\d]*$'
        
        return (re.match(pattern_spaces_digits, remaining1) and 
                re.match(pattern_spaces_digits, remaining2))

    @http.route('/api/smart_import_products', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def smart_import_products(self, **kwargs):
        """
        Importe des produits avec vérification intelligente des noms existants
        - Vérifie la corrélation à 99%
        - Met à jour si le produit importé est plus complet
        - Modifie TOUJOURS le nom si correspondance trouvée
        - Prend en compte les différences d'espaces et de chiffres uniquement
        """
        try:
            file_name = kwargs.get('file_name')
            similarity_threshold = float(kwargs.get('similarity_threshold', 0.99))
            test_mode = kwargs.get('test_mode', 'false').lower() == 'true'
            update_existing = kwargs.get('update_existing', 'true').lower() == 'true'
            force_name_update = kwargs.get('force_name_update', 'true').lower() == 'true'
            
            if not file_name:
                return werkzeug.wrappers.Response(
                    status=400,
                    content_type='application/json; charset=utf-8',
                    response=json.dumps({"error": "Paramètre file_name requis"})
                )
            
            # Lire le fichier de produits
            data_dir = self._get_data_dir()
            file_path = os.path.join(data_dir, file_name)
            
            if not os.path.exists(file_path):
                return werkzeug.wrappers.Response(
                    status=404,
                    content_type='application/json; charset=utf-8',
                    response=json.dumps({"error": "Fichier non trouvé"})
                )
            
            with open(file_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
            
            products_to_import = file_data.get('produits', [])
            existing_products = request.env['product.template'].sudo().search([('active', '=', True)])
            
            _logger.info(f"Import intelligent de {len(products_to_import)} produits...")
            _logger.info(f"Comparaison avec {len(existing_products)} produits existants...")
            
            # Statistiques détaillées avec nouveaux types de correspondance
            stats = {
                'created': [],
                'updated_high_similarity': [],
                'updated_dash_difference': [],
                'updated_number_difference': [],
                'updated_minor_difference': [],
                'updated_similar_name': [],
                'updated_space_difference': [],      # Nouveau : différence d'espaces
                'updated_digit_difference': [],      # Nouveau : différence de chiffres
                'updated_space_digit_difference': [], # Nouveau : différence d'espaces et chiffres
                'updated_exact_chars': [],           # Nouveau : mêmes caractères, diff espaces/chiffres
                'name_force_updated': [],
                'skipped_existing': [],
                'errors': []
            }
            
            for i, import_product in enumerate(products_to_import):
                if not import_product.get('title'):
                    continue
                
                if i % 50 == 0:
                    _logger.info(f"Traitement du produit {i+1}/{len(products_to_import)}")
                
                import_name = import_product['title']
                best_match = None
                best_similarity = 0
                best_similarity_details = None
                match_type = None
                
                # Rechercher le meilleur match parmi les produits existants
                for existing_product in existing_products:
                    similarity_details = self._get_similarity_details(import_name, existing_product.name)
                    similarity = similarity_details['similarity_score']
                    
                    # 1. Vérification de similarité élevée (priorité la plus haute)
                    if similarity >= similarity_threshold and similarity > best_similarity:
                        best_match = existing_product
                        best_similarity = similarity
                        best_similarity_details = similarity_details
                        match_type = 'high_similarity'
                    
                    # 2. Vérification des caractères exactement identiques avec diff espaces/chiffres
                    elif self._has_exact_characters_with_space_digit_diff(import_name, existing_product.name):
                        if similarity > best_similarity:
                            best_match = existing_product
                            best_similarity = similarity
                            best_similarity_details = similarity_details
                            match_type = 'exact_chars_space_digit_diff'
                            _logger.info(f"Correspondance exacte avec diff espaces/chiffres: '{existing_product.name}' <-> '{import_name}'")
                    
                    # 3. Vérification différence d'espaces uniquement
                    elif self._has_only_space_difference(import_name, existing_product.name):
                        if similarity > best_similarity:
                            best_match = existing_product
                            best_similarity = similarity
                            best_similarity_details = similarity_details
                            match_type = 'space_difference'
                            _logger.info(f"Correspondance avec diff espaces: '{existing_product.name}' <-> '{import_name}'")
                    
                    # 4. Vérification différence de chiffres uniquement
                    elif self._has_only_digit_difference(import_name, existing_product.name):
                        if similarity > best_similarity:
                            best_match = existing_product
                            best_similarity = similarity
                            best_similarity_details = similarity_details
                            match_type = 'digit_difference'
                            _logger.info(f"Correspondance avec diff chiffres: '{existing_product.name}' <-> '{import_name}'")
                    
                    # 5. Vérification différence d'espaces ET chiffres
                    elif self._has_only_space_or_digit_difference(import_name, existing_product.name):
                        if similarity > best_similarity:
                            best_match = existing_product
                            best_similarity = similarity
                            best_similarity_details = similarity_details
                            match_type = 'space_digit_difference'
                            _logger.info(f"Correspondance avec diff espaces/chiffres: '{existing_product.name}' <-> '{import_name}'")
                    
                    # 6. Vérification différence de tiret uniquement
                    elif self._has_only_dash_difference(import_name, existing_product.name):
                        if similarity > best_similarity:
                            best_match = existing_product
                            best_similarity = similarity
                            best_similarity_details = similarity_details
                            match_type = 'dash_difference'
                    
                    # 7. Vérification différence de chiffre (ancienne méthode)
                    elif self._has_only_number_difference(import_name, existing_product.name):
                        if similarity > best_similarity:
                            best_match = existing_product
                            best_similarity = similarity
                            best_similarity_details = similarity_details
                            match_type = 'number_difference'

                    # 8. Autres vérifications existantes
                    elif self._is_minor_difference(import_name, existing_product.name):
                        if similarity > best_similarity:
                            best_match = existing_product
                            best_similarity = similarity
                            best_similarity_details = similarity_details
                            match_type = 'minor_difference'

                    elif self._are_names_similar(import_name, existing_product.name):
                        if similarity > best_similarity:
                            best_match = existing_product
                            best_similarity = similarity
                            best_similarity_details = similarity_details
                            match_type = 'similar_name'
                
                try:
                    if best_match:
                        # Calculer les scores de complétude
                        existing_score = self._get_product_completeness_score(best_match)
                        
                        # Calculer le score du produit à importer
                        import_score = 0
                        if import_product.get('title'): import_score += 1
                        if import_product.get('summary_text'): import_score += 3
                        if import_product.get('image'): import_score += 4
                        if import_product.get('images'): import_score += min(len(import_product['images']), 3)
                        if import_product.get('categories'): import_score += 1
                        
                        product_info = {
                            'existing_id': best_match.id,
                            'existing_name': best_match.name,
                            'import_name': import_name,
                            'similarity_details': best_similarity_details,
                            'existing_score': existing_score,
                            'import_score': import_score,
                            'match_type': match_type,
                            'score_improvement': import_score - existing_score,
                            'character_analysis': self._analyze_character_differences(best_match.name, import_name)
                        }
                        
                        # Mettre à jour si autorisé
                        if update_existing and not test_mode:
                            update_vals = {}
                            
                            # Mise à jour forcée du nom pour TOUS les types de correspondance
                            name_was_updated = False
                            if force_name_update and import_name != best_match.name:
                                # Liste étendue des types de correspondance pour mise à jour du nom
                                update_match_types = [
                                    'high_similarity', 'dash_difference', 'number_difference', 
                                    'similar_name', 'minor_difference', 'space_difference',
                                    'digit_difference', 'space_digit_difference', 'exact_chars_space_digit_diff'
                                ]
                                
                                if match_type in update_match_types:
                                    update_vals['name'] = import_name
                                    name_was_updated = True
                                    _logger.info(f"Nom mis à jour: '{best_match.name}' -> '{import_name}' (type: {match_type})")
                            
                            # Autres mises à jour (description, images, etc.) - code inchangé
                            if (import_product.get('summary_text') and 
                                (not best_match.description or 
                                len(import_product['summary_text']) > len(best_match.description))):
                                update_vals['description'] = import_product['summary_text']
                            
                            if import_product.get('image') and not best_match.image_1920:
                                image_base64 = self.get_image_base64(import_product['image'])
                                if image_base64:
                                    update_vals['image_1920'] = image_base64
                            
                            # Images supplémentaires
                            images = import_product.get('images', [])
                            image_base64_list = []
                            for img in images:
                                if img.get('src'):
                                    img_base64 = self.get_image_base64(img['src'])
                                    if img_base64:
                                        image_base64_list.append(img_base64)

                            if image_base64_list:
                                if len(image_base64_list) > 0 and not best_match.image_1:
                                    update_vals['image_1'] = image_base64_list[0]
                                if len(image_base64_list) > 1 and not best_match.image_2:
                                    update_vals['image_2'] = image_base64_list[1]
                                if len(image_base64_list) > 2 and not best_match.image_3:
                                    update_vals['image_3'] = image_base64_list[2]
                                if len(image_base64_list) > 3 and not best_match.image_4:
                                    update_vals['image_4'] = image_base64_list[3]
                            
                            if import_product.get('categories') and not best_match.categ_id:
                                categ_id = self.get_category_id(import_product['categories'])
                                if categ_id:
                                    update_vals['categ_id'] = categ_id

                            # Appliquer les mises à jour
                            if update_vals:
                                best_match.sudo().write(update_vals)
                                product_info['updated_fields'] = list(update_vals.keys())
                                product_info['was_updated'] = True
                                product_info['name_was_updated'] = name_was_updated
                            else:
                                product_info['was_updated'] = False
                                product_info['name_was_updated'] = False
                        else:
                            product_info['was_updated'] = False
                            product_info['name_was_updated'] = False
                        
                        # Enregistrer selon le type de match
                        if name_was_updated and force_name_update:
                            stats['name_force_updated'].append(product_info)
                        elif match_type == 'high_similarity':
                            stats['updated_high_similarity'].append(product_info)
                        elif match_type == 'space_difference':
                            stats['updated_space_difference'].append(product_info)
                        elif match_type == 'digit_difference':
                            stats['updated_digit_difference'].append(product_info)
                        elif match_type == 'space_digit_difference':
                            stats['updated_space_digit_difference'].append(product_info)
                        elif match_type == 'exact_chars_space_digit_diff':
                            stats['updated_exact_chars'].append(product_info)
                        elif match_type == 'dash_difference':
                            stats['updated_dash_difference'].append(product_info)
                        elif match_type == 'number_difference':
                            stats['updated_number_difference'].append(product_info)
                        elif match_type == 'minor_difference':
                            stats['updated_minor_difference'].append(product_info)
                        elif match_type == 'similar_name':
                            stats['updated_similar_name'].append(product_info)
                    
                    else:
                        # Créer un nouveau produit (code inchangé)
                        if not test_mode:
                            default_category_id = self.ensure_default_category()
                            categ_id = self.get_category_id(import_product.get('categories', []))
                            if not categ_id:
                                categ_id = default_category_id
                            
                            product_vals = {
                                'name': import_product['title'],
                                'sale_ok': True,
                                'purchase_ok': True,
                                'type': 'product',
                                'description': import_product.get('summary_text'),
                                'categ_id': categ_id,
                            }
                            
                            if import_product.get('image'):
                                image_base64 = self.get_image_base64(import_product['image'])
                                if image_base64:
                                    product_vals['image_1920'] = image_base64
                            
                            new_product = request.env['product.template'].sudo().create(product_vals)
                            
                            if import_product.get('images'):
                                images = import_product['images']
                                image_base64_list = []
                                for img in images:
                                    if img.get('src'):
                                        img_base64 = self.get_image_base64(img['src'])
                                        if img_base64:
                                            image_base64_list.append(img_base64)

                                if image_base64_list:
                                    image_updates = {}
                                    if len(image_base64_list) > 0:
                                        image_updates['image_1'] = image_base64_list[0]
                                    if len(image_base64_list) > 1:
                                        image_updates['image_2'] = image_base64_list[1]
                                    if len(image_base64_list) > 2:
                                        image_updates['image_3'] = image_base64_list[2]
                                    if len(image_base64_list) > 3:
                                        image_updates['image_4'] = image_base64_list[3]
                                    
                                    if image_updates:
                                        new_product.sudo().write(image_updates)
                            
                            stats['created'].append({
                                'id': new_product.id,
                                'name': new_product.name,
                                'category': new_product.categ_id.name if new_product.categ_id else None,
                                'completeness_score': self._get_product_completeness_score(new_product)
                            })
                        else:
                            stats['created'].append({
                                'name': import_product['title'],
                                'category': import_product.get('categories', [None])[0] if import_product.get('categories') else None
                            })
                
                except Exception as e:
                    stats['errors'].append({
                        'product_name': import_name,
                        'error': str(e)
                    })
                    _logger.error(f"Erreur lors du traitement de {import_name}: {str(e)}")
            
            # Résultat avec nouvelles statistiques
            result = {
                "success": True,
                "test_mode": test_mode,
                "message": "Import intelligent terminé" if not test_mode else "Mode test - Aucune modification effectuée",
                "parameters": {
                    "similarity_threshold": similarity_threshold,
                    "update_existing": update_existing,
                    "force_name_update": force_name_update,
                    "file_name": file_name
                },
                "statistics": {
                    "total_imported": len(products_to_import),
                    "created": len(stats['created']),
                    "updated_high_similarity": len(stats['updated_high_similarity']),
                    "updated_space_difference": len(stats['updated_space_difference']),
                    "updated_digit_difference": len(stats['updated_digit_difference']),
                    "updated_space_digit_difference": len(stats['updated_space_digit_difference']),
                    "updated_exact_chars": len(stats['updated_exact_chars']),
                    "updated_dash_difference": len(stats['updated_dash_difference']),
                    "updated_number_difference": len(stats['updated_number_difference']),
                    "updated_minor_difference": len(stats['updated_minor_difference']),
                    "updated_similar_name": len(stats['updated_similar_name']),
                    "name_force_updated": len(stats['name_force_updated']),
                    "errors": len(stats['errors']),
                    "total_matches_found": (len(stats['updated_high_similarity']) + 
                                        len(stats['updated_space_difference']) +
                                        len(stats['updated_digit_difference']) +
                                        len(stats['updated_space_digit_difference']) +
                                        len(stats['updated_exact_chars']) +
                                        len(stats['updated_dash_difference']) +
                                        len(stats['updated_number_difference']) +
                                        len(stats['updated_minor_difference']) +
                                        len(stats['updated_similar_name']))
                },
                "details": {
                    "created": stats['created'][:5],
                    "updated_space_difference": stats['updated_space_difference'][:5],
                    "updated_digit_difference": stats['updated_digit_difference'][:5],
                    "updated_space_digit_difference": stats['updated_space_digit_difference'][:5],
                    "updated_exact_chars": stats['updated_exact_chars'][:5],
                    "updated_high_similarity": stats['updated_high_similarity'][:5],
                    "name_force_updated": stats['name_force_updated'][:5],
                    "errors": stats['errors']
                }
            }
            
            _logger.info(f"Import terminé: {len(stats['created'])} créés, "
                        f"{len(stats['updated_space_difference'])} diff espaces, "
                        f"{len(stats['updated_digit_difference'])} diff chiffres, "
                        f"{len(stats['updated_exact_chars'])} mêmes caractères, "
                        f"{len(stats['errors'])} erreurs")
            
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(result, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
            )
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'import intelligent: {str(e)}", exc_info=True)
            return werkzeug.wrappers.Response(
                status=500,
                content_type='application/json; charset=utf-8',
                response=json.dumps({
                    "success": False,
                    "error": f"Erreur lors de l'import intelligent: {str(e)}"
                })
            )

    def _analyze_character_differences(self, name1, name2):
        """Analyse détaillée des différences de caractères entre deux noms"""
        if not name1 or not name2:
            return {"error": "Noms manquants"}
        
        analysis = {
            "has_space_difference": self._has_only_space_difference(name1, name2),
            "has_digit_difference": self._has_only_digit_difference(name1, name2),
            "has_space_digit_difference": self._has_only_space_or_digit_difference(name1, name2),
            "has_exact_chars_diff": self._has_exact_characters_with_space_digit_diff(name1, name2),
            "spaces_in_name1": name1.count(' '),
            "spaces_in_name2": name2.count(' '),
            "digits_in_name1": len(re.findall(r'\d', name1)),
            "digits_in_name2": len(re.findall(r'\d', name2)),
            "length_difference": abs(len(name1) - len(name2))
        }
        
        return analysis