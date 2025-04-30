# -*- coding: utf-8 -*-
from .main import *
import pdb
import datetime
import re


_logger = logging.getLogger(__name__)


class ProductCategorieControllerREST(http.Controller):
    
    @http.route('/api/categories', methods=['GET'], type='http', auth='none', cors="*")
    def api__categories_GET(self, **kw):
        categories = request.env['product.category'].sudo().search([])
        categories_data = []
        if categories: 
            for category in categories:
                categories_data.append({
                    'id': category.id,
                    'name': category.name,
                })

            resp = werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(categories_data)
            )
            return resp
        
        return  werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps("pas de données")  )


    # api/produits-count
    @http.route('/api/produits-count', methods=['GET'], type='http', auth='none', cors="*")
    def api__products_count_GET(self, **kw):

        products = request.env['product.product'].sudo().search([('sale_ok', '=', True)])
        resp = werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps(len(products))
        )
        return resp


    @http.route('/api/produits-page', methods=['GET'], type='http', auth='none', cors="*")
    def api__products_GET_per_page_one(self, **kw):
        page = int(kw.get('page', 1))
        limit = int(kw.get('limit', 100))
        offset = (page - 1) * limit

        products = request.env['product.product'].sudo().search([('sale_ok', '=', True)], offset=offset, limit=limit)
        product_data = []
        if products:
            for p in products:
                product_data.append({
                'id': p.id,
                'name': p.name,
                'display_name': p.display_name,
                'quantite_en_stock': p.qty_available,
                'quantity_reception':p.incoming_qty,
                'quanitty_virtuelle_disponible': p.free_qty,
                'quanitty_commande': p.outgoing_qty,
                'quanitty_prevu': p.virtual_available,
                'image_256': p.image_256,
                'categ_id': p.categ_id.name,
                'type': p.type,
                'description': p.product_tmpl_id.description,
                'rang': p.product_tmpl_id.rang or 0,
                'en_promo' : p.product_tmpl_id.en_promo,
                'list_price': p.list_price,
                'volume': p.volume,
                'weight': p.weight,
                'sale_ok': p.sale_ok,
                'purchase_ok': p.purchase_ok,
                'standard_price': p.standard_price,
                'active': p.active,
                'is_preorder': p.product_tmpl_id.is_preorder,
                'preorder_price': p.product_tmpl_id.preorder_price,
                'promo_price': p.product_tmpl_id.promo_price,
                'is_creditorder': p.product_tmpl_id.is_creditorder or None,
                'creditorder_price': p.product_tmpl_id.creditorder_price or None,
            })

            resp = werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(product_data)
            )
            return resp
        return  werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps("pas de données")  )





    @http.route('/api/produits', methods=['GET'], type='http', auth='none', cors="*")
    def api__products_GET(self, **kw):
        products = request.env['product.product'].sudo().search([('sale_ok', '=', True)])
        product_data = []
        if products:
        
            for p in products:
                product_data.append({
                'id': p.id,
                'name': p.name,
                'display_name': p.display_name,
                'quantite_en_stock': p.qty_available,
                'quantity_reception':p.incoming_qty,
                'quanitty_virtuelle_disponible': p.free_qty,
                'quanitty_commande': p.outgoing_qty,
                'quanitty_prevu': p.virtual_available,
                'image_256': p.image_256,
                'categ_id': p.categ_id.name,
                'type': p.type,
                'description': p.product_tmpl_id.description,
                'rang': p.product_tmpl_id.rang or 0,
                'en_promo' : p.product_tmpl_id.en_promo,
                'list_price': p.list_price,
                'volume': p.volume,
                'weight': p.weight,
                'sale_ok': p.sale_ok,
                'purchase_ok': p.purchase_ok,
                'standard_price': p.standard_price,
                'active': p.active,
                'is_preorder': p.product_tmpl_id.is_preorder,
                'preorder_price': p.product_tmpl_id.preorder_price,
                'promo_price': p.product_tmpl_id.promo_price,
                'is_creditorder': p.product_tmpl_id.is_creditorder or None,
                'creditorder_price': p.product_tmpl_id.creditorder_price or None,
            })

            resp = werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(product_data)
            )
            return resp
        return  werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps("pas de données")  )


    @http.route('/api/produits-precommande', methods=['GET'], type='http', auth='none', cors="*")
    def api__products__precommande_GET(self, **kw):
        products = request.env['product.product'].sudo().search([('sale_ok', '=', True), ( 'is_preorder', '=', True ) ])
        product_data = []
        if products:
            for p in products:

                product_data.append({
                'id': p.id,
                'name': p.name,
                'display_name': p.display_name,
                # 'avg_cost': p.avg_cost,
                'quantite_en_stock': p.qty_available,
                'quantity_reception':p.incoming_qty,
                'quanitty_virtuelle_disponible': p.free_qty,
                'quanitty_commande': p.outgoing_qty,
                'quanitty_prevu': p.virtual_available,
                'rang': p.product_tmpl_id.rang or 0,
                # 'image_1920': p.image_1920,
                # 'image_128' : p.image_128,
                # 'image_1024': p.image_1024,
                # 'image_512': p.image_512,
                'image_256': p.image_256,
                'categ_id': p.categ_id.name,
                'type': p.type,
                'description': p.product_tmpl_id.description,
                'en_promo' : p.product_tmpl_id.en_promo,
                'list_price': p.list_price,
                'volume': p.volume,
                'weight': p.weight,
                'sale_ok': p.sale_ok,
                'purchase_ok': p.purchase_ok,
                'standard_price': p.standard_price,
                'active': p.active,
                'is_preorder': p.product_tmpl_id.is_preorder,
                'preorder_price': p.product_tmpl_id.preorder_price,
                'is_creditorder': p.product_tmpl_id.is_creditorder or None,
                'promo_price': p.product_tmpl_id.promo_price,
                'creditorder_price': p.product_tmpl_id.creditorder_price or None,
                # 'ttc_price': p.product_tmpl_id.ttc_price
            })

            resp = werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(product_data)
            )
            return resp
        return  werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps("pas de données")  )

    @http.route('/api/produits/<id>', methods=['GET'], type='http', auth='none', cors="*")
    def api__products__one_GET(self,id, **kw):
        p = request.env['product.product'].sudo().search([ ( 'id' , '=' , id ),('sale_ok', '=', True) ])
        if p:
            # base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')

            # url = f"{base_url}/web/image?model=product.template&id={p.product_tmpl_id.id}&field=image"
            # _logger.info(url)
            tags_data = []
            for tag in p.product_tmpl_id.product_tag_ids:
                tags_data.append({
                    'id': tag.id,
                    'name': tag.name
                })

            produit_data = {
                'id': p.id,
                'name': p.name,
                'tags': tags_data,
                'image_1': p.image_1,
                'image_2': p.image_2,
                'image_3': p.image_3,
                'image_4': p.image_4,
                'image_1920': p.image_1920,
                'image_128' : p.image_128,
                'image_1024': p.image_1024,
                'image_512': p.image_512,
                'image_256': p.image_256,
                'categ_id': p.categ_id.name,
                'type': p.type,
                'description': p.description,
                'list_price': p.list_price,
                'volume': p.volume,
                'weight': p.weight,
                'sale_ok': p.sale_ok,
                'purchase_ok': p.purchase_ok,
                'standard_price': p.standard_price,
                'active': p.active,
                'en_promo' : p.product_tmpl_id.en_promo,
                'rang': p.product_tmpl_id.rang or 0,
                'is_preorder': p.product_tmpl_id.is_preorder,
                'preorder_price': p.product_tmpl_id.preorder_price,
                'display_name': p.display_name,
                'quantite_en_stock': p.qty_available,
                'quantity_reception':p.incoming_qty,
                'quanitty_virtuelle_disponible': p.free_qty,
                'quanitty_commande': p.outgoing_qty,
                'quanitty_prevu': p.virtual_available,
                'is_creditorder': p.product_tmpl_id.is_creditorder or None,
                'creditorder_price': p.product_tmpl_id.creditorder_price or None,
                'promo_price': p.product_tmpl_id.promo_price,
            }

            resp = werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(produit_data)
            )
            return resp
        
        return  werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps(None))


    @http.route('/api/produits/categorie/<categ_id>', methods=['GET'], type='http', auth='none', cors="*")
    def api__products_catgeorie_GET(self,categ_id, **kw):
        products = request.env['product.product'].sudo().search([ ( 'categ_id.name' , '=' , categ_id ),('sale_ok', '=', True) ])
        product_data = []
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')

        if products:
            for p in products:

                product_data.append({
                'id': p.id,
                'name': p.name,
                'display_name': p.display_name,
                # 'avg_cost': p.avg_cost,
                'quantite_en_stock': p.qty_available,
                'quantity_reception':p.incoming_qty,
                'quanitty_virtuelle_disponible': p.free_qty,
                'quanitty_commande': p.outgoing_qty,
                'quanitty_prevu': p.virtual_available,
                # 'image_1920': p.image_1920,
                # 'image_128' : p.image_128,
                # 'image_1024': p.image_1024,
                # 'image_512': p.image_512,
                'image_256': p.image_256,
                'categ_id': p.categ_id.name,
                'type': p.type,
                'description': p.product_tmpl_id.description,
                'en_promo' : p.product_tmpl_id.en_promo,
                'rang': p.product_tmpl_id.rang or 0,
                'list_price': p.list_price,
                'volume': p.volume,
                'weight': p.weight,
                'sale_ok': p.sale_ok,
                'purchase_ok': p.purchase_ok,
                'standard_price': p.standard_price,
                'active': p.active,
                'is_preorder': p.product_tmpl_id.is_preorder,
                'preorder_price': p.product_tmpl_id.preorder_price,
                'is_creditorder': p.product_tmpl_id.is_creditorder or None,
                'creditorder_price': p.product_tmpl_id.creditorder_price or None,
                'promo_price': p.product_tmpl_id.promo_price,
            })
                
            resp = werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(product_data)
            )
            return resp
        return  werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps("pas de données")  )
   
   
   
    @http.route('/api/produits/flash',   methods=['GET'],  type='http', auth='none' , cors="*")
    def api_flash_produits_get(self, **kw):
        products = request.env['product.product'].sudo().search([ ('sale_ok', '=', True), ('active', '=', True)])
        product_data = []
        if products:
            for p in products:
                product_data.append({
                'id': p.id,
                'name': p.name,
                'display_name': p.display_name,
                'quantite_en_stock': p.qty_available,
                'quantity_reception':p.incoming_qty,
                'quanitty_virtuelle_disponible': p.free_qty,
                'quanitty_commande': p.outgoing_qty,
                'quanitty_prevu': p.virtual_available,
                'image_1920': p.image_1920,
                'image_128' : p.image_128,
                'image_1024': p.image_1024,
                'image_512': p.image_512,
                'image_256': p.image_256,
                'categ_id': p.categ_id.name,
                'type': p.type,
                'description': p.description,
                'list_price': p.list_price,
                'volume': p.volume,
                'weight': p.weight,
                'sale_ok': p.sale_ok,
                'purchase_ok': p.purchase_ok,
                'purchase_ok': p.purchase_ok,
                'standard_price': p.standard_price,
                'active': p.active,
                'en_promo' : p.product_tmpl_id.en_promo,
                'rang': p.product_tmpl_id.rang or 0,
                'is_preorder': p.product_tmpl_id.is_preorder,
                'preorder_price': p.product_tmpl_id.preorder_price,
                'is_creditorder': p.product_tmpl_id.is_creditorder or None,
                'creditorder_price': p.product_tmpl_id.creditorder_price or None,
                'promo_price': p.product_tmpl_id.promo_price,
                # 'ttc_price': p.product_tmpl_id.ttc_price
            })
        resp = werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(product_data)
            )
        return resp
    
    @http.route('/api/produits-creditcommande', methods=['GET'], type='http', auth='none', cors="*")
    def api__products__creditcommande_GET(self, **kw):
        products = request.env['product.product'].sudo().search([('sale_ok', '=', True), ( 'is_creditorder', '=', True ) ])
        product_data = []
        if products:
            for p in products:
                product_data.append({
                'id': p.id,
                'name': p.name,
                'display_name': p.display_name,
                # 'avg_cost': p.avg_cost,
                'quantite_en_stock': p.qty_available,
                'quantity_reception':p.incoming_qty,
                'quanitty_virtuelle_disponible': p.free_qty,
                'quanitty_commande': p.outgoing_qty,
                'quanitty_prevu': p.virtual_available,
                # 'image_1920': p.image_1920,
                # 'image_128' : p.image_128,
                # 'image_1024': p.image_1024,
                # 'image_512': p.image_512,
                'image_256': p.image_256,
                'categ_id': p.categ_id.name,
                'type': p.type,
                'description': p.product_tmpl_id.description,
                'en_promo' : p.product_tmpl_id.en_promo,
                'rang': p.product_tmpl_id.rang or 0,
                'list_price': p.list_price,
                'volume': p.volume,
                'weight': p.weight,
                'sale_ok': p.sale_ok,
                'purchase_ok': p.purchase_ok,
                'standard_price': p.standard_price,
                'active': p.active,
                'is_preorder': p.product_tmpl_id.is_preorder,
                'purchase_ok': p.product_tmpl_id.purchase_ok,
                'preorder_price': p.product_tmpl_id.preorder_price,
                'is_creditorder': p.product_tmpl_id.is_creditorder or None,
                'creditorder_price': p.product_tmpl_id.creditorder_price or None,
                'promo_price': p.product_tmpl_id.promo_price,
                # 'ttc_price': p.product_tmpl_id.ttc_price
            })

            resp = werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(product_data)
            )
            return resp
        return  werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps("pas de données")  )




    
    @http.route('/api/produits-filtrer', methods=['GET'], type='http', auth='none', cors="*")
    def api__products_GET_per_page(self, **kw):
        page = int(kw.get('page', 1))
        limit = int(kw.get('limit', 10))
        offset = (page - 1) * limit

        domain = [('sale_ok', '=', True)]

        list_of_category_exclude = ["Services", "service", "Expenses", "Internal", "Consumable", "Saleable", "Software", "All"]
        
        for c in list_of_category_exclude:
            domain.append(('categ_id.name', 'not ilike', c))

        if kw.get('search'):
            search_terms = kw.get('search').split()
            for term in search_terms:
                domain.append(('name', 'ilike', term))

        if kw.get('category') and kw.get('category') != 'All':
            domain.append(('categ_id.name', '=', kw.get('category')))

        if kw.get('productType') and kw.get('productType') != 'All':
            if kw.get('productType') == 'credit':
                domain.append(('is_creditorder', '=', True))
            if kw.get('productType') == 'promo':
                domain.append(('en_promo', '=', True))

        if kw.get('tag') and kw.get('tag') != 'All':
            domain.append(('product_tmpl_id.product_tag_ids.name', 'ilike', kw.get('tag')))
            

        # Vérification sécurisée des valeurs numériques
        min_price = kw.get('min')
        max_price = kw.get('max')

        if min_price:
            try:
                domain.append(('list_price', '>=', float(min_price)))
            except ValueError:
                pass

        if max_price:
            try:
                domain.append(('list_price', '<=', float(max_price)))
            except ValueError:
                pass

        # Comptage total avant la pagination
        total = request.env['product.product'].sudo().search_count(domain)

        # Recherche et tri direct dans la requête
        products = request.env['product.product'].sudo().search(domain, order='list_price asc', offset=offset, limit=limit)
        # je veux le trier en fonction de rang
        # products = sorted(products, key=lambda p: p.product_tmpl_id.rang or 0)

        product_data = []
        for p in products:
            tags_data = []
            for tag in p.product_tmpl_id.product_tag_ids:
                tags_data.append({
                    'id': tag.id,
                    'name': tag.name
                })
            product_data.append({
                'id': p.id,
                'tags': tags_data,
                'name': p.name,
                'rang': p.product_tmpl_id.rang or 0,
                'display_name': p.display_name,
                'quantite_en_stock': p.qty_available,
                'quantity_reception':p.incoming_qty,
                'quanitty_virtuelle_disponible': p.free_qty,
                'quanitty_commande': p.outgoing_qty,
                'quanitty_prevu': p.virtual_available,
                'image_256': p.image_256,
                'categ_id': p.categ_id.name,
                'type': p.type,
                'description': p.product_tmpl_id.description,
                'en_promo' : p.product_tmpl_id.en_promo,
                'list_price': p.list_price,
                'volume': p.volume,
                'weight': p.weight,
                'sale_ok': p.sale_ok,
                'purchase_ok': p.purchase_ok,
                'standard_price': p.standard_price,
                'active': p.active,
                'is_preorder': p.product_tmpl_id.is_preorder,
                'preorder_price': p.product_tmpl_id.preorder_price,
                'promo_price': p.product_tmpl_id.promo_price,
                'is_creditorder': p.product_tmpl_id.is_creditorder or None,
                'creditorder_price': p.product_tmpl_id.creditorder_price or None,
            })
        

        response_data = {
            'products': product_data,
            'total': total,
            'page': page,
            'page_size': limit
        }

        return werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            response=json.dumps(response_data)
        )

    


    
    @http.route('/api/produits-filtrer-promo', methods=['GET'], type='http', auth='none', cors="*")
    def api__products__promo_GET_per_page(self, **kw):
        page = int(kw.get('page', 1))
        limit = int(kw.get('limit', 10))
        offset = (page - 1) * limit

        domain = [('sale_ok', '=', True), ('en_promo', '=', True)]

        list_of_category_exclude = ["Services", "service", "Expenses", "Internal", "Consumable", "Saleable", "Software", "All"]
        
        for c in list_of_category_exclude:
            domain.append(('categ_id.name', 'not ilike', c))
        
        # Ajout des filtres dynamiques
        if kw.get('search'):
            search_terms = kw.get('search').split()
            for term in search_terms:
                domain.append(('name', 'ilike', term))

        if kw.get('category') and kw.get('category') != 'All':
            domain.append(('categ_id.name', '=', kw.get('category')))

        try:
            if kw.get('min'):
                min_price = float(kw.get('min'))
                domain += [
                    ('list_price', '>=', min_price),
                    ('product_tmpl_id.promo_price', '>=', min_price),
                    ('product_tmpl_id.creditorder_price', '>=', min_price),
                ]
            if kw.get('max'):
                max_price = float(kw.get('max'))
                domain += [
                    ('list_price', '<=', max_price),
                    ('product_tmpl_id.promo_price', '<=', max_price),
                    ('product_tmpl_id.creditorder_price', '<=', max_price),
                ]
        except ValueError:
            _logger.error("Invalid price value: min=%s, max=%s", kw.get('min'), kw.get('max'))

        total = request.env['product.product'].sudo().search_count(domain)
        products = request.env['product.product'].sudo().search(domain, order="list_price ASC", offset=offset, limit=limit)
        products = sorted(products, key=lambda p: p.product_tmpl_id.promo_price or 0)

        product_data = []
        for p in products:
            tags_data = []
            for tag in p.product_tmpl_id.product_tag_ids:
                tags_data.append({
                    'id': tag.id,
                    'name': tag.name
                })

            product_data.append({
                'id': p.id,
                'tags': tags_data,
                'name': p.name,
                'display_name': p.display_name,
                'quantite_en_stock': p.qty_available,
                'quantity_reception':p.incoming_qty,
                'quanitty_virtuelle_disponible': p.free_qty,
                'quanitty_commande': p.outgoing_qty,
                'quanitty_prevu': p.virtual_available,
                'image_256': p.image_256,
                'categ_id': p.categ_id.name,
                'type': p.type,
                'description': p.product_tmpl_id.description,
                'en_promo' : p.product_tmpl_id.en_promo,
                'list_price': p.list_price,
                'volume': p.volume,
                'weight': p.weight,
                'sale_ok': p.sale_ok,
                'purchase_ok': p.purchase_ok,
                'standard_price': p.standard_price,
                'active': p.active,
                'is_preorder': p.product_tmpl_id.is_preorder,
                'preorder_price': p.product_tmpl_id.preorder_price,
                'promo_price': p.product_tmpl_id.promo_price,
                'is_creditorder': p.product_tmpl_id.is_creditorder or None,
                'creditorder_price': p.product_tmpl_id.creditorder_price or None, 
                'rang': p.product_tmpl_id.rang or 0,
            })
        

        return werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            response=json.dumps({'products': product_data, 'total': total, 'page': page, 'page_size': limit})
        )


    @http.route('/api/produits/prix', methods=['GET'], type='http', auth='none', cors="*")
    def api_products_creditorder_GET(self, **kw):
        products = request.env['product.product'].sudo().search([('sale_ok', '=', True)])

        product_data = []
        if products:
            for p in products:
                if p.list_price > p.product_tmpl_id.creditorder_price and p.categ_id.name  != "All" and p.categ_id.name != "Services" and p.categ_id.name != "Expenses":

                    tags_data = []
                    for tag in p.product_tmpl_id.product_tag_ids:
                        tags_data.append({
                            'id': tag.id,
                            'name': tag.name
                        })
                        
                    product_data.append({
                        'id': p.id,
                        'nom': p.name,
                        'categ_id': p.categ_id.name,
                        'en_promo': p.product_tmpl_id.en_promo,
                        'list_price': p.list_price,
                        'purchase_ok': p.purchase_ok,
                        'standard_price': p.product_tmpl_id.standard_price,
                        'active': p.active,
                        'is_preorder': p.product_tmpl_id.is_preorder,
                        'preorder_price': p.product_tmpl_id.preorder_price,
                        'promo_price': p.product_tmpl_id.promo_price,
                        'is_creditorder': p.product_tmpl_id.is_creditorder or None,
                        'creditorder_price': p.product_tmpl_id.creditorder_price or None,
                        'rang': p.product_tmpl_id.rang or 0,
                        'tags': tags_data
                    })

        return werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            response=json.dumps(product_data)
        )


    
    # fonction de recherche pour le promo ramadan
    @http.route('/api/produits-filtrer-ramadan', methods=['GET'], type='http', auth='none', cors="*")
    def api__products__promo_ramadan_GET_per_page(self, **kw):
        page = int(kw.get('page', 1))
        limit = int(kw.get('limit', 10))
        offset = (page - 1) * limit
        
        domain = [('sale_ok', '=', True), ('en_promo', '=', True), ('product_tmpl_id.product_tag_ids.name', 'ilike', 'ramadan')]
        # domain = [('sale_ok', '=', True), ('en_promo', '=', True)]
        
        list_of_category_exclude = ["Services" , "service" , "Expenses" , "Internal" , "Consumable" , "Saleable" , "Software" , "All"]
        
        for c in list_of_category_exclude:
            domain.append(('categ_id.name', 'not ilike', c))
        
        # if kw.get('tag'):
        #     domain.append(('product_tmpl_id.product_tag_ids.name', 'ilike', kw.get('tag')))

        # Filtres supplémentaires
        if kw.get('search'):
            search_terms = kw.get('search').split()
            for term in search_terms:
                domain.append(('name', 'ilike', term))


        if kw.get('category') and kw.get('category') != 'All':
            domain.append(('categ_id.name', '=', kw.get('category')))

        if kw.get('min'):
            try:
                min_price = float(kw.get('min'))
                domain.append(('list_price', '>=', min_price))
                domain.append(('product_tmpl_id.promo_price', '>=', min_price))
                domain.append(('product_tmpl_id.creditorder_price', '>=', min_price))
            except ValueError:
                _logger.error("Invalid min price value: %s", kw.get('min'))

        if kw.get('max'):
            try:
                max_price = float(kw.get('max'))
                domain.append(('list_price', '<=', max_price))
                domain.append(('product_tmpl_id.promo_price', '<=', max_price))
                domain.append(('product_tmpl_id.creditorder_price', '<=', max_price))
            except ValueError:
                _logger.error("Invalid max price value: %s", kw.get('max'))


            
        total = request.env['product.product'].sudo().search_count(domain)

        products = request.env['product.product'].sudo().search(domain, order="list_price ASC", offset=offset, limit=limit)
        products = sorted(products, key=lambda p: p.product_tmpl_id.promo_price or 0)

        product_data = []
        for p in products:
            tags_data = []
            for tag in p.product_tmpl_id.product_tag_ids:
                tags_data.append({
                    'id': tag.id,
                    'name': tag.name
                })
            product_data.append({
                'id': p.id,
                'tags': tags_data,
                'name': p.name,
                'display_name': p.display_name,
                'quantite_en_stock': p.qty_available,
                'quantity_reception':p.incoming_qty,
                'quanitty_virtuelle_disponible': p.free_qty,
                'quanitty_commande': p.outgoing_qty,
                'quanitty_prevu': p.virtual_available,
                'image_256': p.image_256,
                'categ_id': p.categ_id.name,
                'type': p.type,
                'description': p.product_tmpl_id.description,
                'en_promo' : p.product_tmpl_id.en_promo,
                'list_price': p.list_price,
                'volume': p.volume,
                'weight': p.weight,
                'sale_ok': p.sale_ok,
                'purchase_ok': p.purchase_ok,
                'standard_price': p.standard_price,
                'active': p.active,
                'is_preorder': p.product_tmpl_id.is_preorder,
                'preorder_price': p.product_tmpl_id.preorder_price,
                'promo_price': p.product_tmpl_id.promo_price,
                'is_creditorder': p.product_tmpl_id.is_creditorder or None,
                'creditorder_price': p.product_tmpl_id.creditorder_price or None,
                'rang': p.product_tmpl_id.rang or 0,
            })
        
        response_data = {
            'products': product_data,
            'total': total,
            'page': page,
            'page_size': limit
        }
        
        return werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            response=json.dumps(response_data)
        )
    
    @http.route('/api/produits-filtrer-korite', methods=['GET'], type='http', auth='none', cors="*")
    def api__products__promo_korite_GET_per_page(self, **kw):
        page = int(kw.get('page', 1))
        limit = int(kw.get('limit', 10))
        offset = (page - 1) * limit
        
        domain = [('sale_ok', '=', True), ('en_promo', '=', True),('product_tmpl_id.product_tag_ids.name', 'ilike', 'Korité')]
        
        list_of_category_exclude = ["Services" , "service" , "Expenses" , "Internal" , "Consumable" , "Saleable" , "Software" , "All"]
        
        for c in list_of_category_exclude:
            domain.append(('categ_id.name', 'not ilike', c))
        
        # Filtres supplémentaires
        if kw.get('search'):
            search_terms = kw.get('search').split()
            for term in search_terms:
                domain.append(('name', 'ilike', term))


        if kw.get('category') and kw.get('category') != 'All':
            domain.append(('categ_id.name', '=', kw.get('category')))

        if kw.get('min'):
            try:
                min_price = float(kw.get('min'))
                domain.append(('list_price', '>=', min_price))
                domain.append(('product_tmpl_id.promo_price', '>=', min_price))
                domain.append(('product_tmpl_id.creditorder_price', '>=', min_price))
            except ValueError:
                _logger.error("Invalid min price value: %s", kw.get('min'))

        if kw.get('max'):
            try:
                max_price = float(kw.get('max'))
                domain.append(('list_price', '<=', max_price))
                domain.append(('product_tmpl_id.promo_price', '<=', max_price))
                domain.append(('product_tmpl_id.creditorder_price', '<=', max_price))
            except ValueError:
                _logger.error("Invalid max price value: %s", kw.get('max'))


            
        total = request.env['product.product'].sudo().search_count(domain)

        products = request.env['product.product'].sudo().search(domain, order="list_price ASC", offset=offset, limit=limit)
        products = sorted(products, key=lambda p: p.product_tmpl_id.promo_price or 0)

        product_data = []
        for p in products:
            tags_data = []
            for tag in p.product_tmpl_id.product_tag_ids:
                tags_data.append({
                    'id': tag.id,
                    'name': tag.name
                })
            product_data.append({
                'id': p.id,
                'tags': tags_data,
                'name': p.name,
                'rang': p.product_tmpl_id.rang or 0,
                'display_name': p.display_name,
                'quantite_en_stock': p.qty_available,
                'quantity_reception':p.incoming_qty,
                'quanitty_virtuelle_disponible': p.free_qty,
                'quanitty_commande': p.outgoing_qty,
                'quanitty_prevu': p.virtual_available,
                'image_256': p.image_256,
                'categ_id': p.categ_id.name,
                'type': p.type,
                'description': p.product_tmpl_id.description,
                'en_promo' : p.product_tmpl_id.en_promo,
                'list_price': p.list_price,
                'volume': p.volume,
                'weight': p.weight,
                'sale_ok': p.sale_ok,
                'purchase_ok': p.purchase_ok,
                'standard_price': p.standard_price,
                'active': p.active,
                'is_preorder': p.product_tmpl_id.is_preorder,
                'preorder_price': p.product_tmpl_id.preorder_price,
                'promo_price': p.product_tmpl_id.promo_price,
                'is_creditorder': p.product_tmpl_id.is_creditorder or None,
                'creditorder_price': p.product_tmpl_id.creditorder_price or None, 
            })
        
        response_data = {
            'products': product_data,
            'total': total,
            'page': page,
            'page_size': limit
        }
        
        return werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            response=json.dumps(response_data)
        )

    #  une methode pour retourner les tags
    @http.route('/api/tags', methods=['GET'], type='http', auth='none', cors="*")
    def api__tags_GET(self, **kw):
        tags = request.env['product.tag'].sudo().search([])
        tags_data = []
        for tag in tags:
            tags_data.append({
                'id': tag.id,
                'name': tag.name
            })
            # par ordre du name
            tags_data = sorted(tags_data, key=lambda x: x['name'])
            
        return werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            response=json.dumps(tags_data)
        )
    

