# Promotions avec Packs Prédéfinis

## Introduction
Nous allons créer des promotions basées sur des packs prédéfinis. Chaque pack contiendra une sélection de produits et aura un numéro unique généré automatiquement.

## Packs Prédéfinis
### Pack 1
- **Produits**:
    - Produit A
    - Produit B
    - Produit C
- **Numéro de Pack**: `PACK1-XXXX` (où `XXXX` est un numéro unique)

### Pack 2
- **Produits**:
    - Produit D
    - Produit E
    - Produit F
- **Numéro de Pack**: `PACK2-XXXX` (où `XXXX` est un numéro unique)

### Pack 3
- **Produits**:
    - Produit G
    - Produit H
    - Produit I
- **Numéro de Pack**: `PACK3-XXXX` (où `XXXX` est un numéro unique)

## Génération des Numéros de Pack
Chaque pack aura un numéro unique généré en fonction du pack. Le format du numéro sera `PACKX-XXXX`, où `X` représente le numéro du pack et `XXXX` est un identifiant unique.

## Envoi des Packs
Les packs seront envoyés avec leur numéro unique pour assurer une traçabilité et une gestion efficace des promotions.

## Exemple de Code
```python
import random

def generate_pack_number(pack_id):
        unique_number = random.randint(1000, 9999)
        return f"PACK{pack_id}-{unique_number}"

# Exemple d'utilisation
pack1_number = generate_pack_number(1)
pack2_number = generate_pack_number(2)
pack3_number = generate_pack_number(3)

print(pack1_number)  # Exemple de sortie: PACK1-1234
print(pack2_number)  # Exemple de sortie: PACK2-5678
print(pack3_number)  # Exemple de sortie: PACK3-9101
```

## Conclusion
En utilisant des packs prédéfinis avec des numéros uniques, nous pouvons créer des promotions efficaces et traçables. Cela permet une meilleure gestion des produits et des promotions.
## Création de la Table `pack.produit`

Pour gérer les packs et leurs produits, nous allons créer une table `pack.produit` qui aura une relation avec `product.product`. Chaque pack peut contenir un ou plusieurs produits, et chaque pack aura une date de commencement, une date de fin, et un numéro unique.

### Définition de la Table
```python
from odoo import models, fields

class PackProduit(models.Model):
    _name = 'pack.produit'
    _description = 'Pack de Produits'

    name = fields.Char(string='Nom du Pack', required=True)
    pack_number = fields.Char(string='Numéro de Pack', required=True, copy=False, readonly=True, index=True, default=lambda self: self.env['ir.sequence'].next_by_code('pack.produit'))
    start_date = fields.Date(string='Date de Commencement', required=True)
    end_date = fields.Date(string='Date de Fin', required=True)
    product_ids = fields.Many2many('product.product', string='Produits')
```

### Séquence pour le Numéro de Pack
```xml

<odoo>
    <data noupdate="1">
        <record id="seq_pack_produit" model="ir.sequence">
            <field name="name">Pack Produit</field>
            <field name="code">pack.produit</field>
            <field name="prefix">PACK</field>
            <field name="padding">4</field>
            <field name="number_increment">1</field>
        </record>
    </data>
</odoo>
```

## Interface de Gestion des Packs

Nous allons créer une interface dans Odoo pour gérer les packs, permettant d'ajouter, supprimer, et modifier les packs.

### Vue Formulaire
```xml

<record id="view_form_pack_produit" model="ir.ui.view">
    <field name="name">pack.produit.form</field>
    <field name="model">pack.produit</field>
    <field name="arch" type="xml">
        <form string="Pack de Produits">
            <sheet>
                <group>
                    <field name="name"/>
                    <field name="pack_number"/>
                    <field name="start_date"/>
                    <field name="end_date"/>
                    <field name="product_ids" widget="many2many_tags"/>
                </group>
            </sheet>
        </form>
    </field>
</record>
```

### Vue Liste
```xml
<record id="view_tree_pack_produit" model="ir.ui.view">
    <field name="name">pack.produit.tree</field>
    <field name="model">pack.produit</field>
    <field name="arch" type="xml">
        <tree string="Pack de Produits">
            <field name="name"/>
            <field name="pack_number"/>
            <field name="start_date"/>
            <field name="end_date"/>
        </tree>
    </field>
</record>
```

### Action et Menu
```xml
<record id="action_pack_produit" model="ir.actions.act_window">
    <field name="name">Packs de Produits</field>
    <field name="res_model">pack.produit</field>
    <field name="view_mode">tree,form</field>
</record>

<menuitem id="menu_pack_produit" name="Packs de Produits" parent="base.menu_sales" action="action_pack_produit"/>
```

## Conclusion
Avec cette configuration, nous avons créé une table `pack.produit` pour gérer les packs de produits, chaque pack ayant un numéro unique, une date de commencement, une date de fin, et une relation avec plusieurs produits. Nous avons également mis en place une interface dans Odoo pour ajouter, supprimer, et modifier les packs.