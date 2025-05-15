# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ScrapedProduct(models.Model):
    _name = 'scraped.product'
    _description = 'Produit scrapé'
    
    name = fields.Char('Nom', required=True)
    url = fields.Char('URL')
    image_url = fields.Char('URL de l\'image')
    summary = fields.Text('Résumé')
    scrape_date = fields.Datetime('Date de scraping')
    raw_data = fields.Text('Données brutes JSON')
    source_domain = fields.Char('Domaine source')
    category = fields.Char('Catégorie')
    
    # Relations avec les produits Odoo
    product_template_id = fields.Many2one('product.template', string='Modèle de produit')
    is_imported = fields.Boolean('Importé', default=False)
    
    def action_import_to_product(self):
        """Importe le produit scrapé dans le catalogue de produits Odoo"""
        for record in self:
            if record.is_imported:
                continue
                
            # Vérifier si le produit existe déjà
            existing_product = self.env['product.template'].sudo().search(
                [('name', '=', record.name)], limit=1)
                
            if existing_product:
                record.product_template_id = existing_product.id
            else:
                # Créer un nouveau produit
                import json
                raw_data = json.loads(record.raw_data or '{}')
                
                # Récupérer l'image
                image_base64 = False
                if record.image_url:
                    image_base64 = self._get_image_base64(record.image_url)
                
                # Créer le produit
                vals = {
                    'name': record.name,
                    'description': record.summary,
                    'detailed_type': 'product',
                    'sale_ok': True,
                    'purchase_ok': True,
                }
                
                if image_base64:
                    vals['image_1920'] = image_base64
                    
                product = self.env['product.template'].sudo().create(vals)
                record.product_template_id = product.id
                
            record.is_imported = True
            
    def _get_image_base64(self, image_url):
        """Récupère une image depuis une URL et la convertit en base64"""
        if not image_url:
            return False
            
        try:
            import requests
            import base64
            import io
            from PIL import Image
            
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Vérifier si le contenu est une image valide
            content = response.content
            try:
                # Essayer d'ouvrir l'image avec PIL pour vérifier qu'elle est valide
                img = Image.open(io.BytesIO(content))
                img.verify()  # Vérifier que l'image est valide
                
                # Réouvrir l'image pour la traiter (après verify(), l'image est fermée)
                img = Image.open(io.BytesIO(content))
                
                # Convertir en RGB si nécessaire (pour les images avec canal alpha)
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                    img = background
                
                # Redimensionner si l'image est trop grande
                max_size = (1920, 1920)
                if img.width > max_size[0] or img.height > max_size[1]:
                    img.thumbnail(max_size, Image.LANCZOS)
                
                # Convertir l'image traitée en base64
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                return img_base64
                
            except Exception as e:
                return False
                
        except Exception:
            return False