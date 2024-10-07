import os
import base64
import json
import werkzeug
from odoo import http
from odoo.http import request

class ProductCategorieControllerREST(http.Controller):

    @http.route('/api/produits', methods=['GET'], type='http', auth='none', cors="*")
    def api__products_GET(self, **kw):
        products = request.env['product.product'].sudo().search([('sale_ok', '=', True)])
        product_data = []

        if products:
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            for p in products:
               
                image_url = self.process_image(p.image_1920, p.id)
                image_1 = self.process_image(p.image_1, p.id)
                image_2 = self.process_image(p.image_2, p.id)
                image_3 = self.process_image(p.image_3, p.id)
                image_4 = self.process_image(p.image_4, p.id)

                product_data.append(self.construct_product_data(p, base_url, image_url,image_1,image_2,image_3,image_4))

            return self.create_response(product_data)

        return self.create_response("pas de données")

    def process_image(self, image_base64, product_id):
        """Decode the base64 image and save it to the server."""
        if not image_base64:
            return None

        # Extract the base64 data
        header, encoded = image_base64.split(',', 1)
        
        # Decode the base64 data
        image_data = base64.b64decode(encoded)

        # Define the folder path to save images
        folder_path = '/images'  
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Define the file name and path
        file_name = f"{product_id}.png"
        file_path = os.path.join(folder_path, file_name)

        # Write the image data to a file
        with open(file_path, 'wb') as file:
            file.write(image_data)

        # Return the URL of the saved image
        return f"{request.env['ir.config_parameter'].sudo().get_param('web.base.url')}/images/{file_name}"

    def construct_product_data(self, product, base_url, image_url,image_1,image_2,image_3,image_4):
        """Construct and return a dictionary of product data."""
        return {
            'id': product.id,
            'name': product.name,
            'display_name': product.display_name,
            'quantite_en_stock': product.qty_available,
            'quantity_reception': product.incoming_qty,
            'quanitty_virtuelle_disponible': product.free_qty,
            'quanitty_commande': product.outgoing_qty,
            'quanitty_prevu': product.virtual_available,
            'image_1920': image_url,
            'image_1': image_1,
            'image_2': image_2,
            'image_3': image_3,
            'image_4': image_4,
            'image_128': f"{base_url}/web/image/product.product/{product.id}/image_128",
            'image_1024': f"{base_url}/web/image/product.product/{product.id}/image_1024",
            'image_512': f"{base_url}/web/image/product.product/{product.id}/image_512",
            'image_256': f"{base_url}/web/image/product.product/{product.id}/image_256",
            'categ_id': product.categ_id.name,
            'type': product.type,
            'description': product.product_tmpl_id.description,
            'en_promo': product.product_tmpl_id.en_promo,
            'list_price': product.list_price,
            'volume': product.volume,
            'weight': product.weight,
            'sale_ok': product.sale_ok,
            'standard_price': product.standard_price,
            'active': product.active,
            'is_preorder': product.product_tmpl_id.is_preorder,
            'preorder_price': product.product_tmpl_id.preorder_price,
        }

    def create_response(self, data):
        """Create an HTTP response."""
        return werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps(data)
        )