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
            
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')

            url = f"{base_url}/web/image?model=product.template&id={p.product_tmpl_id.id}&field=image"
            _logger.info(url)

            produit_data = {
                'id': p.id,
                'name': p.name,
                'image_1': p.image_1,
                'image_2': p.image_2,
                'image_3': p.image_3,
                'image_4': p.image_4,
                # 'image_1920': p.image_1920,
                # 'image_128' : p.image_128,
                # 'image_1024': p.image_1024,
                'image_512': p.image_512,
                # 'image_256': p.image_256,
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
            response=json.dumps("pas de données")  )


    @http.route('/api/produits/categorie/<categ_id>', methods=['GET'], type='http', auth='none', cors="*")
    def api__products_catgeorie_GET(self,categ_id, **kw):
        products = request.env['product.product'].sudo().search([ ( 'categ_id.name' , '=' , categ_id ),('sale_ok', '=', True) ], limit = 4)
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




    # nouvelle fonction

    @http.route('/api/produits-filtrer', methods=['GET'], type='http', auth='none', cors="*")
    def api__products_GET_per_page(self, **kw):
        page = int(kw.get('page', 1))
        limit = int(kw.get('limit', 10))
        offset = (page - 1) * limit
        
        domain = [('sale_ok', '=', True)]

        list_of_category_exclude = ["Services" , "service" , "Expenses" , "Internal" , "Consumable" , "Saleable" , "Software" , "All"]
        
        for c in list_of_category_exclude:
            domain.append(('categ_id.name', 'not ilike', c))
        
        # Filtres supplémentaires
        if kw.get('search'):
            domain.append(('name', 'ilike', kw.get('search')))
        if kw.get('category') and kw.get('category') != 'All':
            domain.append(('categ_id.name', '=', kw.get('category')))
        if kw.get('min_price'):
            domain.append(('list_price', '>=', float(kw.get('min_price'))))
        if kw.get('max_price'):
            domain.append(('list_price', '<=', float(kw.get('max_price'))))

        total = request.env['product.product'].sudo().search_count(domain)
        products = request.env['product.product'].sudo().search(domain, offset=offset, limit=limit)
        
        product_data = []
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
        
        list_of_category_exclude = ["Services" , "service" , "Expenses" , "Internal" , "Consumable" , "Saleable" , "Software" , "All"]
        
        for c in list_of_category_exclude:
            domain.append(('categ_id.name', 'not ilike', c))
        
        # Filtres supplémentaires
        if kw.get('search'):
            domain.append(('name', 'ilike', kw.get('search')))
        if kw.get('category') and kw.get('category') != 'All':
            domain.append(('categ_id.name', '=', kw.get('category')))
        if kw.get('min_price'):
            domain.append(('list_price', '>=', float(kw.get('min_price'))))
        if kw.get('max_price'):
            domain.append(('list_price', '<=', float(kw.get('max_price'))))

        total = request.env['product.product'].sudo().search_count(domain)
        products = request.env['product.product'].sudo().search(domain, offset=offset, limit=limit)
        
        product_data = []
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