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

    @http.route('/api/produits', methods=['GET'], type='http', auth='none', cors="*")
    def api__products_GET(self, **kw):
        products = request.env['product.product'].sudo().search([('sale_ok', '=', True)])
        product_data = []
        if products:
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            for p in products:
                image_1920_url = f"{base_url}/web/image/product.product/{p.id}/image_1920"
                image_128_url = f"{base_url}/web/image/product.product/{p.id}/image_128"
                image_1024_url = f"{base_url}/web/image/product.product/{p.id}/image_1024"
                image_512_url = f"{base_url}/web/image/product.product/{p.id}/image_512"
                image_256_url = f"{base_url}/web/image/product.product/{p.id}/image_256"

                image_1 = f"{base_url}/web/image/product.template/{p.product_tmpl_id.id}/image_1"
                image_2 = f"{base_url}/web/image/product.template/{p.product_tmpl_id.id}/image_2"
                image_3 = f"{base_url}/web/image/product.template/{p.product_tmpl_id.id}/image_3"
                image_4 = f"{base_url}/web/image/product.template/{p.product_tmpl_id.id}/image_4"

                product_data.append({
                'id': p.id,
                'name': p.name,
                'display_name': p.display_name,
                'image': image_1920_url,
                # 'avg_cost': p.avg_cost,
                'quantite_en_stock': p.qty_available,
                'quantity_reception':p.incoming_qty,
                'quanitty_virtuelle_disponible': p.free_qty,
                'quanitty_commande': p.outgoing_qty,
                'quanitty_prevu': p.virtual_available,
                'image_1920': image_1920_url,
                'image_128' : image_128_url,
                'image_1024': image_1024_url,
                'image_512': image_512_url,
                'image_256': image_256_url,
                # 'image_1920': p.image_1920,
                # 'image_128' : p.image_128,
                # 'image_1024': p.image_1024,
                # 'image_512': p.image_512,
                # 'image_256': p.image_256,
                'categ_id': p.categ_id.name,
                'type': p.type,
                'description': p.product_tmpl_id.description,
                'image_1': image_1,
                'image_2': image_2,
                'image_3': image_3,
                'image_4': image_4,
                'en_promo' : p.product_tmpl_id.en_promo,
                'list_price': p.list_price,
                'volume': p.volume,
                'weight': p.weight,
                'sale_ok': p.sale_ok,
                'standard_price': p.standard_price,
                'active': p.active,
                'is_preorder': p.product_tmpl_id.is_preorder,
                'preorder_price': p.product_tmpl_id.preorder_price,
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


    @http.route('/api/produits-precommande', methods=['GET'], type='http', auth='none', cors="*")
    def api__products__precommande_GET(self, **kw):
        products = request.env['product.product'].sudo().search([('sale_ok', '=', True), ( 'is_preorder', '=', True ) ])
        product_data = []
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        if products:
            for p in products:

                image_1920_url = f"{base_url}/web/image/product.product/{p.id}/image_1920"
                image_128_url = f"{base_url}/web/image/product.product/{p.id}/image_128"
                image_1024_url = f"{base_url}/web/image/product.product/{p.id}/image_1024"
                image_512_url = f"{base_url}/web/image/product.product/{p.id}/image_512"
                image_256_url = f"{base_url}/web/image/product.product/{p.id}/image_256"

                image_1 = f"{base_url}/web/image/product.template/{p.product_tmpl_id.id}/image_1"
                image_2 = f"{base_url}/web/image/product.template/{p.product_tmpl_id.id}/image_2"
                image_3 = f"{base_url}/web/image/product.template/{p.product_tmpl_id.id}/image_3"
                image_4 = f"{base_url}/web/image/product.template/{p.product_tmpl_id.id}/image_4"

                _logger.info(image_1920_url)
                _logger.info(image_128_url)

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
                # 'image_256': p.image_256,
                'image_1920': image_1920_url,
                'image_128' : image_128_url,
                'image_1024': image_1024_url,
                'image_512': image_512_url,
                'image_256': image_256_url,
                'image_1': image_1,
                'image_2': image_2,
                'image_3': image_3,
                'image_4': image_4,

                'categ_id': p.categ_id.name,
                'type': p.type,
                'description': p.product_tmpl_id.description,
                'en_promo' : p.product_tmpl_id.en_promo,
                'list_price': p.list_price,
                'volume': p.volume,
                'weight': p.weight,
                'sale_ok': p.sale_ok,
                'standard_price': p.standard_price,
                'active': p.active,
                'is_preorder': p.product_tmpl_id.is_preorder,
                'preorder_price': p.product_tmpl_id.preorder_price,
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
 

            image_1920_url = f"{base_url}/web/image/product.product/{p.id}/image_1920"
            image_128_url = f"{base_url}/web/image/product.product/{p.id}/image_128"
            image_1024_url = f"{base_url}/web/image/product.product/{p.id}/image_1024"
            image_512_url = f"{base_url}/web/image/product.product/{p.id}/image_512"
            image_256_url = f"{base_url}/web/image/product.product/{p.id}/image_256"

            image_1 = f"{base_url}/web/image/product.template/{p.product_tmpl_id.id}/image_1"
            image_2 = f"{base_url}/web/image/product.template/{p.product_tmpl_id.id}/image_2"
            image_3 = f"{base_url}/web/image/product.template/{p.product_tmpl_id.id}/image_3"
            image_4 = f"{base_url}/web/image/product.template/{p.product_tmpl_id.id}/image_4"
            
            produit_data = {
                'id': p.id,
                'name': p.name,
                'image': image_1920_url,
               
                # 'image_1920': p.image_1920,
                # 'image_128' : p.image_128,
                # 'image_1024': p.image_1024,
                # 'image_512': p.image_512,
                # 'image_256': p.image_256,
                'image_1920': image_1920_url,
                'image_128' : image_128_url,
                'image_1024': image_1024_url,
                'image_512': image_512_url,
                'image_256': image_256_url,
                'image_1': image_1,
                'image_2': image_2,
                'image_3': image_3,
                'image_4': image_4,
                'categ_id': p.categ_id.name,
                'type': p.type,
                'description': p.description,
                'list_price': p.list_price,
                'volume': p.volume,
                'weight': p.weight,
                'sale_ok': p.sale_ok,
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

                image_1920_url = f"{base_url}/web/image/product.product/{p.id}/image_1920"
                image_128_url = f"{base_url}/web/image/product.product/{p.id}/image_128"
                image_1024_url = f"{base_url}/web/image/product.product/{p.id}/image_1024"
                image_512_url = f"{base_url}/web/image/product.product/{p.id}/image_512"
                image_256_url = f"{base_url}/web/image/product.product/{p.id}/image_256"

                image_1 = f"{base_url}/web/image/product.template/{p.product_tmpl_id.id}/image_1"
                image_2 = f"{base_url}/web/image/product.template/{p.product_tmpl_id.id}/image_2"
                image_3 = f"{base_url}/web/image/product.template/{p.product_tmpl_id.id}/image_3"
                image_4 = f"{base_url}/web/image/product.template/{p.product_tmpl_id.id}/image_4"
                _logger.info(image_1920_url)
                _logger.info(image_128_url)
                
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
                'image_1920': image_1920_url,
                'image_128' : image_128_url,
                'image_1024': image_1024_url,
                'image_512': image_512_url,
                'image_256': image_256_url,
                'image_1': image_1,
                'image_2': image_2,
                'image_3': image_3,
                'image_4': image_4,
                # 'image_1920': p.image_1920,
                # 'image_128' : p.image_128,
                # 'image_1024': p.image_1024,
                # 'image_512': p.image_512,
                # 'image_256': p.image_256,
                'categ_id': p.categ_id.name,
                'type': p.type,
                'description': p.product_tmpl_id.description,
                'en_promo' : p.product_tmpl_id.en_promo,
                'list_price': p.list_price,
                'volume': p.volume,
                'weight': p.weight,
                'sale_ok': p.sale_ok,
                'standard_price': p.standard_price,
                'active': p.active,
                'is_preorder': p.product_tmpl_id.is_preorder,
                'preorder_price': p.product_tmpl_id.preorder_price,
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
                'standard_price': p.standard_price,
                'active': p.active,
                'en_promo' : p.product_tmpl_id.en_promo,
                'is_preorder': p.product_tmpl_id.is_preorder,
                'preorder_price': p.product_tmpl_id.preorder_price,
                # 'ttc_price': p.product_tmpl_id.ttc_price
            })
        resp = werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(product_data)
            )
        return resp

